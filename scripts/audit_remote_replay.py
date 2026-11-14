"""Read only market evidence from the existing Railway volume; never run its workers."""
import base64
import hashlib
import json
import subprocess

from continuous_replay_data import ROOT
import replay_multiasset as r

CODE = '''import pathlib,json,base64,hashlib,datetime
root=pathlib.Path('/app/data/platform/market-base-v1/b3')
coverage={}
exports=[]
for p in sorted(root.glob('*.json')):
 raw=p.read_bytes();v=json.loads(raw)
 for t,rows in v.get('rows',{}).items():
  old=coverage.setdefault(t,[]);old.extend(x['date'] for x in rows)
 if v.get('session','')>='2026-10-21':
  exports.append({'name':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()})
print(json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'coverage':{t:{'start':min(ds),'end':max(ds),'unique_dates':len(set(ds))} for t,ds in coverage.items() if ds},'storage':str(root),'exports':exports}))
'''


def audit():
    encoded = base64.b64encode(CODE.encode()).decode()
    command = "exec(__import__('base64').b64decode('" + encoded + "'))"
    completed = subprocess.run(["railway.cmd", "ssh", "-p", "ad6797e4-d9a0-45a2-b7b8-04950c277b5b", "-e", "f467c798-f6c7-48eb-be9c-5a4477e2e9cc", "-s", "7987997f-61ea-4e23-ae05-3cda9dd50d97", "--", "python", "-c", command], capture_output=True, timeout=60, check=True)
    # The CLI emits a key-selection notice before the remote JSON.
    line = next(x for x in completed.stdout.decode().splitlines() if x.startswith('{"observed_at"'))
    doc = json.loads(line)
    exports = doc.pop("exports")
    metadata = []
    for item in exports:
        raw = base64.b64decode(item["base64"], validate=True)
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("remote_market_export_hash_mismatch")
        r.b.check_seal(json.loads(raw))
        r.radar.write(ROOT / "remote/b3" / item["name"], raw, immutable=True)
        metadata.append({k: v for k, v in item.items() if k != "base64"})
    doc.update(exports=metadata, method="Railway SSH read-only pathlib export; no worker/API mutations", tailscale_local_state="NoState; HTTPS hostname unavailable", deployment="18fdc3c0-a955-47d8-a611-7201ca652c37", persistent_volume="hfl-data, 20 GB, /app/data", local_copy_reason="Migration guide section 4 preserves PC as pre-migration copy; Railway is the working copy")
    r.save(ROOT / "remote/audit.json", doc)
    return doc


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
