#!/usr/bin/env python3
"""
Minimal-call, read-only Onshape fetcher (official public REST API only).

    export ONSHAPE_ACCESS_KEY=...  ONSHAPE_SECRET_KEY=...
    python3 scripts/onshape_fetch.py "https://cad.onshape.com/documents/<did>/w/<wid>/e/<eid>" --out cache/

Requests (each skipped when its cached file already exists):
  1  GET  /assemblies/d/{did}/w/{wid}/e/{eid}          assembly definition (instances, occurrence transforms)
  1  GET  /assemblies/d/{did}/w/{wid}/e/{eid}/bom      BOM
  1  POST /assemblies/d/{did}/w/{wid}/e/{eid}/translations   GLTF export, storeInDocument=false
  n  GET  /translations/{id}                           poll (back-off 5,10,20,30,30... s)
  1  GET  /documents/d/{did}/externaldata/{fileId}     download GLB
Typical total: 5-7 calls, once. Every request is appended to cache/api_log.json.

Nothing is written to the Onshape document (translation result is NOT stored in the document).
If you would rather spend ZERO API calls: in Onshape right-click the assembly tab -> Export ->
format GLTF (binary .glb) and pass that file straight to build_views.py.

STATUS: written against the public API reference; not executed against your
document from the authoring session because no credentials were available there.
"""
import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://cad.onshape.com/api/v10"


def parse_url(url):
    m = re.search(r"/documents/([0-9a-f]{24})/([wvm])/([0-9a-f]{24})/e/([0-9a-f]{24})", url)
    if not m:
        sys.exit("could not parse Onshape URL")
    return m.groups()


class Client:
    def __init__(self, out):
        self.out = out
        self.log_path = os.path.join(out, "api_log.json")
        self.log = json.load(open(self.log_path)) if os.path.exists(self.log_path) else []
        ak, sk = os.environ.get("ONSHAPE_ACCESS_KEY"), os.environ.get("ONSHAPE_SECRET_KEY")
        self.auth = ("Basic " + base64.b64encode(f"{ak}:{sk}".encode()).decode()) if ak and sk else None

    def call(self, method, path, body=None, accept="application/json", raw=False):
        url = path if path.startswith("http") else BASE + path
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", accept)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self.auth:
            req.add_header("Authorization", self.auth)
        t = time.time()
        entry = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "method": method, "path": url.replace(BASE, "")}
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                payload = r.read()
                entry.update(status=r.status, bytes=len(payload))
        except urllib.error.HTTPError as e:
            entry.update(status=e.code, error=e.read()[:300].decode(errors="replace"))
            self._save(entry, t)
            raise
        self._save(entry, t)
        return payload if raw else json.loads(payload)

    def _save(self, entry, t):
        entry["ms"] = int((time.time() - t) * 1000)
        self.log.append(entry)
        json.dump(self.log, open(self.log_path, "w"), indent=2)
        print(f"[onshape] {entry['method']} {entry['path']} -> {entry.get('status')}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--out", default="cache")
    ap.add_argument("--skip-gltf", action="store_true", help="only definition + BOM (2 calls)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    did, wvm, wvmid, eid = parse_url(a.url)
    c = Client(a.out)
    asm = f"/assemblies/d/{did}/{wvm}/{wvmid}/e/{eid}"

    p = os.path.join(a.out, "assembly_definition.json")
    if not os.path.exists(p):
        d = c.call("GET", asm + "?includeMateFeatures=false&includeMateConnectors=false&includeNonSolids=false")
        json.dump(d, open(p, "w"), indent=1)
    p = os.path.join(a.out, "bom.json")
    if not os.path.exists(p):
        d = c.call("GET", asm + "/bom?indented=false&generateIfAbsent=false")
        json.dump(d, open(p, "w"), indent=1)

    glb = os.path.join(a.out, "assembly.glb")
    if a.skip_gltf or os.path.exists(glb):
        return
    tr = c.call("POST", asm + "/translations", {
        "formatName": "GLTF", "storeInDocument": False, "flattenAssemblies": False,
        "yAxisIsUp": True, "includeExportIds": True, "resolution": "fine",
    })
    tid = tr["id"]
    json.dump(tr, open(os.path.join(a.out, "translation_request.json"), "w"), indent=1)
    for wait in (5, 10, 20, 30, 30, 30, 60, 60, 120):
        time.sleep(wait)
        st = c.call("GET", f"/translations/{tid}")
        if st.get("requestState") == "DONE":
            break
        if st.get("requestState") == "FAILED":
            sys.exit(f"translation failed: {st.get('failureReason')}")
    else:
        sys.exit("translation still running; re-run later (cached steps are skipped)")
    fid = st["resultExternalDataIds"][0]
    blob = c.call("GET", f"/documents/d/{did}/externaldata/{fid}", accept="application/octet-stream", raw=True)
    open(glb, "wb").write(blob)
    print(f"saved {glb} ({len(blob)} bytes); total API calls logged: {len(c.log)}")


if __name__ == "__main__":
    main()
