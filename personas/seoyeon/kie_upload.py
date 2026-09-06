"""
kie_upload.py — put a local image on Kie's own file host and get a URL back.

Removes the imgur step completely: reference images no longer need third-party
hosting, and generated frames can be fed straight back in as references for the
next angle.

UPLOADS EXPIRE. This file used to say "~3 days, which is longer than a build
session" and cache the URL forever on that basis. The project is now weeks old,
so every sidecar written in week one points at nothing, and the failure surfaces
as a generation error rather than an upload error:

    FAIL  The parameter `image` ... Error while downloading: https://tempfile...

A cached URL is therefore CHECKED before it is reused. The digest still decides
whether the FILE changed; a liveness check decides whether the LINK survived.
Cost is one HEAD per reference, against a wasted generation if we skip it.

The exact endpoint path is not in the public quickstart, so we try the known
candidates once and cache whichever answers.
"""
from __future__ import annotations

import base64
import json
import pathlib

import requests

UPLOAD_BASE = "https://kieai.redpandaai.co"
CANDIDATES = [
    "/api/file-base64-upload",
    "/api/v1/file/base64-upload",
    "/api/file/base64-upload",
    "/api/v1/files/base64",
]
_working: str | None = None
_cache: dict[str, str] = {}


def _alive(url: str) -> bool:
    """Is this cached URL still serving? Uploads are temporary storage.

    A dead link does not fail at upload time — it fails inside the generation
    call, after the money is committed. Better to spend one HEAD here.
    Anything we cannot positively confirm is treated as dead: a needless
    re-upload costs seconds, a wrong reuse costs a generation.
    """
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        if r.status_code == 200:
            return True
        if r.status_code in (403, 405, 501):        # HEAD not supported here
            g = requests.get(url, timeout=10, stream=True,
                             headers={"Range": "bytes=0-0"})
            g.close()
            return g.status_code in (200, 206)
        return False
    except Exception:
        return False


def upload(path: pathlib.Path, api_key: str) -> str:
    """Local file -> public URL.

    Cached to disk next to the file, so a seed is uploaded ONCE ever. Re-running
    any script reuses the URL instead of re-sending megabytes and risking a hang.
    """
    global _working
    # Key on CONTENT, not on path. locations/window.png is a fixed name whose
    # bytes change every time a new plate is locked; a path-keyed cache would
    # keep sending the OLD plate forever. The sidecar stores "<sha> <url>" and
    # is ignored when the hash no longer matches the file on disk.
    import hashlib as _h
    digest = _h.sha256(path.read_bytes()).hexdigest()[:16]
    key = digest
    if key in _cache:
        return _cache[key]
    side = path.with_suffix(path.suffix + ".url")
    if side.exists():
        raw = side.read_text().strip().split()
        if len(raw) == 2 and raw[0] == digest and raw[1].startswith("http"):
            if _alive(raw[1]):
                _cache[key] = raw[1]
                print(f"  reusing uploaded URL from {side.name}")
                return raw[1]
            print(f"  {path.name}: cached URL has expired — re-uploading")
        else:
            print(f"  {path.name} changed since it was uploaded — re-uploading")

    ext = path.suffix.lower().lstrip(".") or "png"
    mime = {"jpg": "jpeg"}.get(ext, ext)
    payload = {
        "base64Data": f"data:image/{mime};base64,"
                      + base64.b64encode(path.read_bytes()).decode(),
        "uploadPath": "images/persona",
        # Content hash in the REMOTE name. Uploading a changed file under the
        # same fileName returns the same URL, and the CDN keeps serving the
        # OLD bytes — the new plate never reaches the model. A unique remote
        # name per content hash makes a changed file a genuinely new object.
        "fileName": f"{path.stem}_{digest[:10]}{path.suffix}",
    }
    headers = {"Authorization": f"Bearer {api_key}",
               "Content-Type": "application/json"}

    paths = [_working] if _working else CANDIDATES
    errors = []
    for p in paths:
        try:
            r = requests.post(UPLOAD_BASE + p, json=payload,
                              headers=headers, timeout=45)
            if r.status_code == 404:
                errors.append(f"{p}: 404")
                continue
            r.raise_for_status()
            d = r.json()
            url = ((d.get("data") or {}).get("fileUrl")
                   or (d.get("data") or {}).get("downloadUrl"))
            if not url:
                errors.append(f"{p}: no fileUrl in {json.dumps(d)[:160]}")
                continue
            _working = p
            _cache[key] = url
            try:
                side.write_text(f"{digest} {url}")   # re-uploaded only if it changes
                # Say so. A silent success looked like a skipped file on a
                # six-reference video call, which is exactly the moment you
                # want to see what is actually being sent.
                print(f"  uploaded {path.name}")
            except OSError:
                pass
            return url
        except Exception as e:
            errors.append(f"{p}: {str(e)[:120]}")
    raise RuntimeError(
        "Could not upload to Kie's file host. Tried:\n    "
        + "\n    ".join(errors)
        + "\n  Check the current path at https://docs.kie.ai/file-upload-api/quickstart"
          "\n  and set CANDIDATES in kie_upload.py.")
