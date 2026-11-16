"""Install the sealed replay exports locally or through the existing Tailscale SSH."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import stat
import subprocess
import tempfile
import uuid
import zipfile
from datetime import datetime, timezone

PACKAGE_SHA256 = "c4d38ab78d4e2835a52fa17bf3debff10308173dda911b6aa1c5c2ae71c98047"
HOST = "root@hedge-fund-lab-1.tail2f2f04.ts.net."
DESTINATION = PurePosixPath("/app/data/replays/april-november-2026-flash")
FILES = {
    "index.html", "calls-data.js", "explorer.json", "calls.json", "manifest.json",
    "daily.csv", "operations.csv", "decisions.csv", "dividends.csv", "calls.csv",
    "abrir_explorador.py", "LEIA-ME.txt", "preview-desktop.jpg", "preview-mobile.jpg",
}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inspect_package(package):
    if sha(package) != PACKAGE_SHA256:
        raise ValueError("package_sha256_mismatch")
    with zipfile.ZipFile(package) as archive:
        infos = archive.infolist()
        if len(infos) != len(FILES) or {i.filename for i in infos} != FILES:
            raise ValueError("unexpected_package_members")
        if any(i.is_dir() or stat.S_ISLNK(i.external_attr >> 16) for i in infos):
            raise ValueError("package_requires_regular_files")
        result = {}
        for info in infos:
            with archive.open(info) as stream:
                result[info.filename] = {
                    "bytes": info.file_size,
                    "sha256": hashlib.file_digest(stream, "sha256").hexdigest(),
                }
        return result


def verify_exports(root, expected):
    folder = root / "exports"
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("exports_directory_missing_or_symlink")
    if {p.name for p in folder.iterdir()} != set(expected):
        raise ValueError("installed_members_differ")
    for name, record in expected.items():
        path = folder / name
        if path.is_symlink() or not path.is_file() or sha(path) != record["sha256"]:
            raise ValueError("installed_file_differs: " + name)


def install(package, destination):
    """Stage all verified files before one rename; never replace an existing dataset."""
    package, destination = Path(package), Path(destination)
    expected = inspect_package(package)
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink():
            raise ValueError("destination_is_symlink")
        verify_exports(destination, expected)
        receipt = json.loads((destination / "import_receipt.json").read_text())
        if receipt.get("package_sha256") != PACKAGE_SHA256:
            raise ValueError("installed_receipt_differs")
        return {**receipt, "already_installed": True}
    destination.parent.mkdir(parents=True, exist_ok=True)
    needed = sum(r["bytes"] for r in expected.values()) + package.stat().st_size
    if shutil.disk_usage(destination.parent).free < needed + 20_000_000:
        raise OSError("insufficient_storage_for_staging")
    # ponytail: failed staging stays for inspection; no existing data is deleted.
    stage = Path(tempfile.mkdtemp(prefix=".replay-staging-", dir=destination.parent))
    with zipfile.ZipFile(package) as archive:
        archive.extractall(stage / "exports")  # exact flat member allowlist checked above
    verify_exports(stage, expected)
    shutil.copy2(package, stage / "package.zip")
    if sha(stage / "package.zip") != PACKAGE_SHA256:
        raise ValueError("copied_package_sha256_mismatch")
    receipt = {
        "status": "PASS", "package_sha256": PACKAGE_SHA256,
        "installed_at": datetime.now(timezone.utc).isoformat(), "files": expected,
        "sessions": 153, "daily_wallet_states": 918, "new_inference": False,
    }
    (stage / "import_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    # Linux rename would replace an empty directory: fail if another installer won.
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    stage.rename(destination)
    return receipt


def publish(package):
    expected = inspect_package(package)
    options = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=yes"]
    known = Path(os.environ.get("APPDATA", "")) / "Tailscale/ssh_known_hosts"
    if known.is_file():
        options += ["-o", "UserKnownHostsFile=" + str(known)]
    upload = DESTINATION.parent / (".replay-upload-" + uuid.uuid4().hex + ".zip")
    # Binary stdin avoids Windows PowerShell's text-pipeline corruption.
    command = "umask 077; set -C; mkdir -p " + shlex.quote(str(upload.parent))
    command += "; cat > " + shlex.quote(str(upload))
    with Path(package).open("rb") as stream:
        subprocess.run(["ssh", *options, HOST, command], stdin=stream, check=True, timeout=300)
    code = base64.b64encode(Path(__file__).read_bytes()).decode("ascii")
    command = "python -c " + shlex.quote("exec(__import__('base64').b64decode('" + code + "'))")
    command += " --install " + shlex.quote(str(upload))
    if DESTINATION.name.endswith(("-v2", "-v3")):
        command += " --version " + DESTINATION.name.rsplit("-", 1)[1]
    result = subprocess.run(["ssh", *options, HOST, command], check=True, capture_output=True,
                            encoding="utf-8", timeout=180)
    receipt = json.loads(result.stdout)
    if receipt.get("package_sha256") != PACKAGE_SHA256 or receipt.get("files") != expected:
        raise ValueError("remote_receipt_mismatch")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--version", choices=("v1", "v2", "v3"), default="v1")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--install", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.version != "v1":
        PACKAGE_SHA256 = {
            "v2": "62998e60b09d24a49668a56cbbdcd9076db1d65ef34bb8af7a2e8d4652da5749",
            "v3": "da0016fe22095027e3f9ec0f314bc96e0d7f792d2099fe0276dead511e9b75d4",
        }[args.version]
        DESTINATION = DESTINATION.with_name(DESTINATION.name + "-" + args.version)
        FILES = FILES - {"preview-desktop.jpg", "preview-mobile.jpg"}
    if args.check_only:
        result = {"status": "PASS", "package_sha256": PACKAGE_SHA256,
                  "files": inspect_package(args.package)}
    elif args.install:
        if os.name != "posix":
            raise ValueError("server_install_requires_posix")
        result = install(args.package, DESTINATION)
        # Only the unique transport file is removed; the verified package is retained.
        if args.package.parent == DESTINATION.parent and args.package.name.startswith(".replay-upload-"):
            args.package.unlink()
    else:
        result = publish(args.package)
    print(json.dumps(result, ensure_ascii=False))
