"""Runnable, network-free checks: python tests/check_publish_replay.py."""
from pathlib import Path
import stat
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publish_replay as replay


def refused(function):
    try:
        function()
    except (ValueError, FileNotFoundError):
        return
    raise AssertionError("unsafe or different input was accepted")


def package(path, extra=None, symlink=False):
    with zipfile.ZipFile(path, "w") as archive:
        for name in replay.FILES:
            if symlink and name == "index.html":
                info = zipfile.ZipInfo(name)
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
                archive.writestr(info, "/outside")
            else:
                archive.writestr(name, "test archive member: " + name)
        if extra:
            archive.writestr(extra, "must never be extracted")


with tempfile.TemporaryDirectory(prefix="hfl-replay-import-") as dirname:
    folder = Path(dirname).resolve()
    assert folder.parent == Path(tempfile.gettempdir()).resolve()
    archive = folder / "package.zip"
    package(archive)
    original_sha = replay.PACKAGE_SHA256
    # Local fake archive only: the production CLI still pins the real package hash.
    replay.PACKAGE_SHA256 = replay.sha(archive)
    assert str(replay.DESTINATION).startswith("/app/data/")
    destination = folder / "installed"
    result = replay.install(archive, destination)
    assert result["status"] == "PASS" and result["new_inference"] is False
    assert {p.name for p in (destination / "exports").iterdir()} == replay.FILES
    assert replay.sha(destination / "package.zip") == replay.sha(archive)
    for name in replay.FILES:
        assert (destination / "exports" / name).read_text() == "test archive member: " + name
    before = (destination / "import_receipt.json").read_bytes()
    assert replay.install(archive, destination)["already_installed"] is True
    assert before == (destination / "import_receipt.json").read_bytes()
    (destination / "exports/index.html").write_text("changed")
    refused(lambda: replay.install(archive, destination))
    assert (destination / "exports/index.html").read_text() == "changed"
    existing = folder / "do-not-overwrite"
    existing.mkdir()
    (existing / "keep.txt").write_text("preserve")
    refused(lambda: replay.install(archive, existing))
    assert (existing / "keep.txt").read_text() == "preserve"
    archive.write_bytes(archive.read_bytes() + b"changed transport bytes")
    refused(lambda: replay.install(archive, folder / "corrupt"))
    assert not (folder / "corrupt").exists()
    for name, extra, link in (("traversal.zip", "../outside.txt", False),
                              ("link.zip", None, True)):
        bad = folder / name
        package(bad, extra, link)
        replay.PACKAGE_SHA256 = replay.sha(bad)
        refused(lambda: replay.install(bad, folder / "bad"))
        assert not (folder / "bad").exists() and not (folder / "outside.txt").exists()
    replay.PACKAGE_SHA256 = original_sha

print("PASS: sealed bytes, POSIX target, exact members, safe staging, idempotence and no overwrite")
