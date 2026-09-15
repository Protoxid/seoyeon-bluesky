"""
kie_api.py — verified-shape client for Kie.ai job API.

Payload shape confirmed against the user's working example:
    POST /api/v1/jobs/createTask
    {"model": "gpt-image-2-text-to-image",
     "callBackUrl": "...",                      # optional; we poll instead
     "input": {"prompt": "...", "aspect_ratio": "auto"}}

Image-to-image uses the sibling model id with an image_urls array. If your
account's docs show a different id, change MODEL_I2I below -- it is the only
unverified constant in this file.
"""
from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path

import requests

from model_schemas import build_input

API_BASE = "https://api.kie.ai"
# BOTH ENDPOINTS ARE GPT IMAGE 2. This is the project default and every
# script that does not name a model explicitly gets it from here.
#
# Text-to-image: its loose commitment to a spec is a feature at seed stage --
# you sift a dozen candidates and keep one, so variety is what you want. The
# 0.496 self-consistency number governed SEED SELECTION only, and the seed is
# chosen by hand, so it stopped applying the moment a seed was picked.
MODEL_T2I = "gpt-image-2-text-to-image"
# Image-to-image. THIS LINE USED TO SAY SEEDREAM, and the reason it gave was
# "Seedream's image_urls field is DOCUMENTED and verified, unlike gpt-image-2's,
# which I inferred and which may never have been read at all."
# That reason is dead. gpt-image-2's i2i reference field is `input_urls`, it is
# verified, and `build_input()` in model_schemas.py reads it from SCHEMAS -- so
# nothing here has to know the field name. The bake-off that made Seedream look
# better was run while those references were going to `image_urls`, a field
# gpt-image-2 does not read, so it was scored with no identity input at all.
# The other justification -- "Seedream returns one full-resolution frame per
# call instead of dividing a canvas N ways" -- is also dead: gpt-image-2 returns
# one frame per call and has done for the whole grid.
# Leaving this on Seedream was a live trap, not a stale comment: kie_api's own
# fallback below (`model or MODEL_I2I`) meant any reference-conditioned call
# that did not name a model went to a different renderer than the grid, and
# nothing would have said so.
MODEL_I2I = "gpt-image-2-5-sunburst-image-to-image"

# per-image USD, for the budget guard only; never sent upstream
PRICE = {"seedream/5-pro-text-to-image": 0.07,
         "seedream/5-pro-image-to-image": 0.07,
         "gpt-image-2-text-to-image": 0.09,
         "gpt-image-2-image-to-image": 0.09,
         "gpt-image-2-5-sunburst-image-to-image": 0.09}


def load_key(folder: Path) -> None:
    """
    Finds the Kie API key and puts it in os.environ. Never prints the value.

    Looks in kie_key.txt first, then .env. Both are forgiving: a bare line
    containing just the key works, and so does KIE_API_KEY=xxx . Blank lines,
    '#' comments, quotes and stray whitespace are all ignored.
    """
    for name in ("kie_key.txt", ".env"):
        f = folder / name
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip().strip('"').strip("'")
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                if k.strip().upper() == "KIE_API_KEY" and v:
                    os.environ["KIE_API_KEY"] = v
                    return
            else:
                # a bare line -- assume the whole thing is the key
                os.environ["KIE_API_KEY"] = line
                return


class Kie:
    def __init__(self, api_key: str, timeout: float = 600.0, poll: float = 4.0):
        self.key = api_key
        self.timeout, self.poll = timeout, poll
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {api_key}",
                               "Content-Type": "application/json"})

    def _req(self, method: str, path: str, retries: int = 4, **kw):
        last = None
        for i in range(retries):
            try:
                r = self.s.request(method, API_BASE + path, timeout=90, **kw)
                if r.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {r.status_code} {r.text[:160]}")
                if r.status_code in (401, 403):
                    raise PermissionError(
                        f"HTTP {r.status_code} -- check KIE_API_KEY in .env")
                r.raise_for_status()
                return r.json()
            except PermissionError:
                raise
            except Exception as e:
                last = e
                if i == retries - 1:
                    break
                time.sleep((2 ** i) + random.uniform(0, 1.5))
        raise RuntimeError(f"{method} {path}: {last}")

    def credit(self):
        try:
            return (self._req("GET", "/api/v1/chat/credit") or {}).get("data")
        except Exception:
            return None

    def generate(self, prompt: str, aspect: str = "1:1",
                 image_urls: list[str] | None = None,
                 model: str | None = None, tier: str = "2k") -> list[str]:
        """Reference images go into whichever field this model expects.

        DO NOT hardcode a field name here, and do not trust a summary of them.
        `build_input()` looks the key up in model_schemas.SCHEMAS per model,
        because they genuinely disagree: nano-banana-pro takes `image_input`,
        gpt-image-2 image-to-image takes `input_urls`, its own text-to-image
        sibling takes `image_urls`, and Seedream takes `image_urls`. An earlier
        version of this docstring said "others want image_urls", which is how
        gpt-image-2 spent a whole bake-off generating from text alone with its
        references silently dropped into a field it does not read."""
        model = model or (MODEL_I2I if image_urls else MODEL_T2I)
        inp = build_input(model, prompt, aspect, tier, refs=image_urls)
        d = self._req("POST", "/api/v1/jobs/createTask",
                      json={"model": model, "input": inp})
        tid = (d.get("data") or {}).get("taskId")
        if not tid:
            raise RuntimeError(f"no taskId: {json.dumps(d)[:300]}")
        return self._wait(tid)

    def _wait(self, tid: str) -> list[str]:
        end = time.time() + self.timeout
        while time.time() < end:
            d = self._req("GET", "/api/v1/jobs/recordInfo", params={"taskId": tid})
            data = d.get("data") or {}
            state = str(data.get("state", data.get("status", ""))).lower()
            if state in ("success", "succeeded", "completed", "1"):
                raw = data.get("resultJson") or data.get("result") or "{}"
                res = json.loads(raw) if isinstance(raw, str) else raw
                urls = (res.get("resultUrls") or res.get("urls")
                        or res.get("images")
                        or res.get("audios") or res.get("resultUrl") or [])
                if isinstance(urls, str):        # a single url, not a list
                    urls = [urls]
                if not urls:
                    raise RuntimeError(f"done but no urls: {str(res)[:250]}")
                return urls
            if state in ("fail", "failed", "error", "2", "3"):
                raise RuntimeError(str(data.get("failMsg")
                                       or data.get("errorMessage")
                                       or "generation failed")[:250])
            time.sleep(self.poll)
        raise TimeoutError(f"task {tid} exceeded {self.timeout}s")

    _uploads: dict = {}

    def upload(self, path) -> str:
        """Same call shape the rest of the project uses. Cached per path: the
        masters go up on every generate call and re-uploading identical files
        for every image in a batch is pure latency.

        Downscaled to 2048px first. Kie bills a FLAT rate so this saves no
        money — it saves time, and the 26 MB of full-size masters we were
        shipping per request was never doing anything for identity that 2048px
        does not."""
        from pathlib import Path as _P
        import os as _os
        path = _P(path).resolve()
        k = str(path)
        if k in self._uploads:
            return self._uploads[k]
        try:
            from PIL import Image
            import io as _io, tempfile
            im = Image.open(path).convert("RGB")
            if max(im.size) > 2048:
                im.thumbnail((2048, 2048), Image.LANCZOS)
                tmp = _P(tempfile.gettempdir()) / f"_ref_{path.stem}.jpg"
                im.save(tmp, "JPEG", quality=92)
                path = tmp
        except Exception:
            pass                       # full size still works, just slower
        from kie_upload import upload as _up
        url = _up(path, self.key if hasattr(self, "key")
                  else _os.environ.get("KIE_API_KEY", ""))
        if not url:
            raise RuntimeError(f"upload of {path.name} returned nothing")
        self._uploads[k] = url
        return url

    def video(self, prompt: str, first_frame_url: str, duration: int = 6,
              resolution: str = "768P", log=None) -> str:
        """minimax-h3/image-to-video on Kie. FIRST FRAME ONLY.

        `end_image_url` is never sent. Two fixed endpoints are interpolation,
        not motion: the model has to land exactly on the second frame, so it
        eases in and out, and that easing is the floatiness in the reel that
        got published.

        NOTE THE FIELD NAME. Kie calls it `first_frame_url`; fal called the
        same thing `image_url`. The field belongs to the PROVIDER as much as
        the model, and make_clip.py was left calling a fal-shaped method that
        this client does not have.
        """
        import json as _j
        body = {"model": "minimax-h3/image-to-video",
                "input": {"prompt": prompt,
                          "first_frame_url": first_frame_url,
                          "duration": int(duration),
                          "resolution": resolution}}
        d = self._req("POST", "/api/v1/jobs/createTask", json=body)
        tid = (d.get("data") or {}).get("taskId")
        if not tid:
            raise RuntimeError(f"no taskId: {_j.dumps(d)[:300]}")
        urls = self._wait(tid)
        if not urls:
            raise RuntimeError("done but no video url")
        return urls[0]

    # ---- reference-to-video ------------------------------------------------
    H3_REF2V = "minimax-h3/reference-to-video"
    REF_ASPECT = (0.4, 2.5)          # width/height bounds for a reference
    REF_SIDE = (256, 5760)
    REF_MAX_BYTES = 30 * 1024 * 1024
    R2V_ASPECTS = ("adaptive", "1:1", "16:9", "21:9", "3:4", "4:3", "9:16")
    R2V_RES = ("768P", "2K")

    @staticmethod
    def check_reference(path) -> None:
        """Validate a reference against H3's published bounds BEFORE upload.

        A reference rejected server-side costs a round trip and tells you very
        little. These are cheap local checks and they are exact."""
        from pathlib import Path as _P
        p = _P(path)
        if not p.is_file():
            raise FileNotFoundError(p)
        if p.stat().st_size > Kie.REF_MAX_BYTES:
            raise ValueError(f"{p.name}: {p.stat().st_size // 1048576} MB, "
                             f"over the 30 MB reference limit")
        try:
            from PIL import Image
        except ImportError:
            return
        w, h = Image.open(p).size
        lo, hi = Kie.REF_SIDE
        if not (lo <= w <= hi and lo <= h <= hi):
            raise ValueError(f"{p.name}: {w}x{h}, sides must be {lo}-{hi} px")
        r = w / h
        a, b = Kie.REF_ASPECT
        if not (a <= r <= b):
            raise ValueError(f"{p.name}: aspect {r:.2f}, must be {a}-{b}")

    # AUDIO REFERENCES. Confirmed against MiniMax's own documentation, not a
    # blog: H3 outputs native stereo audio (32 kHz) and lip-syncs speech, and
    # `reference_audio_urls` is a VOICE TIMBRE reference — MiniMax's wording is
    # "Voice timbre follows reference audio 1", and the model card is explicit
    # that this is timbre matching rather than strict voice cloning.
    #   up to 3 clips, 2-15s each, 15s combined
    #   MPEG / WAV / X-WAV, <=15 MB each (Kie's limit)
    #   CANNOT BE SENT ALONE — needs at least one image or video reference
    #   addressed in the prompt as "Audio 1", the same convention as images
    AUDIO_MAX = 3
    AUDIO_MAX_BYTES = 15 * 1024 * 1024
    AUDIO_SUFFIXES = (".mp3", ".wav", ".mpeg", ".mpga")
    AUDIO_SECONDS = (2.0, 15.0)
    AUDIO_TOTAL_SECONDS = 15.0

    @staticmethod
    def check_audio(paths) -> None:
        """Validate audio references locally, before anything uploads.

        WAV duration is read exactly. An mp3's duration is NOT guessed: a wrong
        guess that passes here and fails server-side is worse than saying the
        check could not run, because it launders an unknown into a green tick.
        """
        from pathlib import Path as _P
        import wave, contextlib
        ps = [_P(x) for x in paths]
        if len(ps) > Kie.AUDIO_MAX:
            raise ValueError(f"{len(ps)} audio references; H3 takes at most "
                             f"{Kie.AUDIO_MAX}")
        total, unknown = 0.0, []
        for q in ps:
            if not q.is_file():
                raise FileNotFoundError(q)
            if q.suffix.lower() not in Kie.AUDIO_SUFFIXES:
                raise ValueError(f"{q.name}: H3 takes "
                                 f"{', '.join(Kie.AUDIO_SUFFIXES)}")
            if q.stat().st_size > Kie.AUDIO_MAX_BYTES:
                raise ValueError(f"{q.name}: "
                                 f"{q.stat().st_size // 1048576} MB, over the "
                                 f"15 MB audio limit")
            if q.suffix.lower() == ".wav":
                with contextlib.closing(wave.open(str(q))) as w:
                    sec = w.getnframes() / float(w.getframerate() or 1)
                lo, hi = Kie.AUDIO_SECONDS
                if not lo <= sec <= hi:
                    raise ValueError(f"{q.name}: {sec:.1f}s, must be "
                                     f"{lo}-{hi}s")
                total += sec
            else:
                unknown.append(q.name)
        if total > Kie.AUDIO_TOTAL_SECONDS:
            raise ValueError(f"audio totals {total:.1f}s, over the "
                             f"{Kie.AUDIO_TOTAL_SECONDS}s combined limit")
        if unknown:
            print(f"  note: could not read the duration of {unknown} "
                  f"locally — H3 needs 2-15s each and 15s combined")

    # THE MODEL ID HERE IS INFERRED, NOT VERIFIED, AND THAT IS FLAGGED ON
    # PURPOSE. Kie's H3 page documents three modes — text-to-video (4-15s,
    # 768P/2K, 9:16 among the ratios, no media required), image-to-video and
    # reference-to-video — but does not print the id strings. The other two
    # are "minimax-h3/image-to-video" and "minimax-h3/reference-to-video", so
    # this follows the pattern. THE PATTERN IS NOT THE PROVIDER'S PROMISE: this
    # project has already been burned assuming a field name transfers within a
    # family. A wrong id fails at createTask, before any generation, so it
    # costs nothing but a round trip — if it 404s, read the real id off the Kie
    # model page and change the one constant below.
    H3_T2V = "minimax-h3/text-to-video"

    def text_video(self, prompt: str, duration: int = 6,
                   resolution: str = "768P", aspect_ratio: str = "9:16",
                   log=None) -> str:
        """H3 text-to-video. No media at all.

        For a shot whose PLACE does not have to be the same place twice. Where
        it does, use ref_video() with a plate: this path has no way to hold a
        location steady between runs, which is a feature here and a bug there.
        """
        import json as _j, time as _t
        if not 4 <= int(duration) <= 15:
            raise ValueError(f"duration {duration}s; H3 takes 4-15")
        if not 1 <= len(prompt) <= 7000:
            raise ValueError(f"prompt is {len(prompt)} chars; H3 takes 1-7000")
        if resolution not in self.R2V_RES:
            raise ValueError(f"resolution {resolution!r}; H3 takes "
                             f"{' or '.join(self.R2V_RES)}")
        if aspect_ratio not in self.R2V_ASPECTS:
            raise ValueError(f"aspect {aspect_ratio!r}; H3 takes "
                             f"{', '.join(self.R2V_ASPECTS)}")
        body = {"model": self.H3_T2V,
                "input": {"prompt": prompt,
                          "duration": int(duration),
                          "resolution": resolution,
                          "aspect_ratio": aspect_ratio}}
        d = self._req("POST", "/api/v1/jobs/createTask", json=body)
        tid = (d.get("data") or {}).get("taskId")
        if not tid:
            raise RuntimeError(
                f"no taskId: {_j.dumps(d)[:300]}\n"
                f"    If this says the model is unknown, H3_T2V is the wrong "
                f"id — see the note above it.")
        got = self._wait(tid)
        if not got:
            raise RuntimeError("done but no video url")
        if log is not None:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(_j.dumps({"ts": _t.time(), "model": self.H3_T2V,
                                   "refs": [], "duration": duration,
                                   "resolution": resolution,
                                   "aspect": aspect_ratio,
                                   "prompt": prompt[:600]},
                                  ensure_ascii=False) + "\n")
        return got[0]

    # KLING 3.0. FIELD NAMES VERIFIED AGAINST KIE'S OWN DOC, NOT INFERRED --
    # and they are NOT H3's. H3 takes `first_frame_url`, a single string;
    # Kling takes `image_urls`, an ARRAY holding first and last frame. Same
    # job, same provider, different model, different field. That is the rule
    # this project has already paid for twice.
    # There is NO negative_prompt field, so negatives live inside the prompt,
    # the same as H3. `mode` is std | pro | 4K and `sound` is a real toggle.
    KLING = "kling-3.0/video"
    KLING_MODES = ("std", "pro", "4K")
    KLING_ASPECTS = ("16:9", "9:16", "1:1")

    def kling_video(self, prompt: str, image_paths=None, duration: int = 5,
                    aspect_ratio: str = "9:16", mode: str = "std",
                    sound: bool = False, log=None) -> str:
        """Kling 3.0 on Kie. First frame (and optionally last) via image_urls."""
        import json as _j, time as _t
        from pathlib import Path as _P
        paths = [_P(x) for x in (image_paths or [])]
        if len(paths) > 2:
            raise ValueError(f"{len(paths)} images; image_urls holds first "
                             f"and last frame only")
        if not 3 <= int(duration) <= 15:
            raise ValueError(f"duration {duration}s; Kling 3.0 takes 3-15")
        if not 1 <= len(prompt) <= 7000:
            raise ValueError(f"prompt is {len(prompt)} chars")
        if mode not in self.KLING_MODES:
            raise ValueError(f"mode {mode!r}; Kling takes "
                             f"{', '.join(self.KLING_MODES)}")
        if aspect_ratio not in self.KLING_ASPECTS:
            raise ValueError(f"aspect {aspect_ratio!r}; Kling takes "
                             f"{', '.join(self.KLING_ASPECTS)}")
        # multi_shots IS REQUIRED, NOT OPTIONAL. Kie's doc lists it as a
        # true/false field alongside the others, which reads as "omit for the
        # default". Omitting it returns 422 "multi_shots cannot be empty".
        # A DOCUMENTED FIELD WITH A STATED DEFAULT IS STILL NOT AN OPTIONAL
        # FIELD -- the doc describes the shape, the API enforces it, and only
        # one of those two is the contract.
        # It also selects which prompt field is read: false -> `prompt`,
        # true -> `multi_prompt`, an array of {prompt, duration} objects. This
        # method only does single-shot, so it pins it false rather than letting
        # a caller set it and then silently ignoring their multi_prompt.
        body = {"model": self.KLING,
                "input": {"prompt": prompt,
                          "duration": int(duration),
                          "aspect_ratio": aspect_ratio,
                          "mode": mode,
                          "sound": bool(sound),
                          "multi_shots": False}}
        if paths:
            body["input"]["image_urls"] = [self.upload(q) for q in paths]
        d = self._req("POST", "/api/v1/jobs/createTask", json=body)
        tid = (d.get("data") or {}).get("taskId")
        if not tid:
            raise RuntimeError(f"no taskId: {_j.dumps(d)[:300]}")
        got = self._wait(tid)
        if not got:
            raise RuntimeError("done but no video url")
        if log is not None:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(_j.dumps({"ts": _t.time(), "model": self.KLING,
                                   "refs": [q.name for q in paths],
                                   "duration": duration, "mode": mode,
                                   "aspect": aspect_ratio,
                                   "prompt": prompt[:600]},
                                  ensure_ascii=False) + "\n")
        return got[0]

    def ref_video(self, prompt: str, reference_paths, duration: int = 8,
                  resolution: str = "768P", aspect_ratio: str = "9:16",
                  reference_audio_paths=None, log=None) -> str:
        """H3 reference-to-video. Identity from up to 9 stills.

        References are addressed inside the prompt as "Image 1", "Image 2" —
        the same convention outside.ROLES already uses for the stills, so the
        identity stack transfers with no translation.
        """
        import json as _j, time as _t
        from pathlib import Path as _P
        paths = [_P(p) for p in reference_paths]
        if not paths:
            raise ValueError("reference-to-video with no references — use "
                             "video() for first-frame conditioning")
        if len(paths) > 9:
            raise ValueError(f"{len(paths)} references; H3 takes at most 9")
        if not 4 <= int(duration) <= 15:
            raise ValueError(f"duration {duration}s; H3 takes 4-15")
        if not 1 <= len(prompt) <= 7000:
            raise ValueError(f"prompt is {len(prompt)} chars; H3 takes 1-7000")
        if resolution not in self.R2V_RES:
            raise ValueError(f"resolution {resolution!r}; H3 takes "
                             f"{' or '.join(self.R2V_RES)}")
        if aspect_ratio not in self.R2V_ASPECTS:
            raise ValueError(f"aspect_ratio {aspect_ratio!r}; H3 takes "
                             f"{', '.join(self.R2V_ASPECTS)}")
        if "Image 1" not in prompt:
            raise ValueError("the prompt never says what Image 1 is for. H3 "
                             "addresses references by ordinal, and a reference "
                             "with no stated job is paid for and averaged in")
        for p in paths:
            self.check_reference(p)

        audio = [str(x) for x in (reference_audio_paths or [])]
        if audio:
            self.check_audio(audio)
            if "Audio 1" not in prompt:
                raise ValueError("audio references attached but the prompt "
                                 "never says what Audio 1 is for. H3 addresses "
                                 "them by ordinal, exactly like the images")

        urls = [self.upload(p) for p in paths]
        body = {"model": self.H3_REF2V,
                "input": {"prompt": prompt,
                          "reference_image_urls": urls,
                          "duration": int(duration),
                          "resolution": resolution,
                          "aspect_ratio": aspect_ratio}}
        if audio:
            # Audio cannot be the only reference input; the image guard above
            # already guarantees at least one image is present.
            body["input"]["reference_audio_urls"] = [self.upload(x)
                                                     for x in audio]
        d = self._req("POST", "/api/v1/jobs/createTask", json=body)
        tid = (d.get("data") or {}).get("taskId")
        if not tid:
            raise RuntimeError(f"no taskId: {_j.dumps(d)[:300]}")
        got = self._wait(tid)
        if not got:
            raise RuntimeError("done but no video url")
        if log is not None:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(_j.dumps({"ts": _t.time(), "model": self.H3_REF2V,
                                   "refs": [p.name for p in paths],
                                   "duration": duration,
                                   "resolution": resolution,
                                   "aspect": aspect_ratio,
                                   "audio": [str(x) for x in audio],
                                   "prompt": prompt[:600]},
                                  ensure_ascii=False) + "\n")
        return got[0]

    # ---- Seedance 2.5 -------------------------------------------------
    # SEEDANCE WAS RULED OUT BECAUSE IT REFUSES HER FACE. Clips with no person
    # in them have no face to refuse, which is the operator's own observation
    # and the reason this exists at all.
    #
    # THE FIELD IS `reference_image_urls`, NOT `image_urls`. The playbook's
    # note that "Seedance takes image_urls" came from an older Seedance on a
    # different provider and does not transfer — which is itself the rule: a
    # field name belongs to the PROVIDER AND THE VERSION, never to the family.
    #
    # WHAT IS DOCUMENTED: model id, the input keys, and that reference images
    # cap at 2. WHAT IS NOT: the duration range, the resolution enum, the
    # aspect enum, and the price. Those are checked at the API, not here — a
    # guard invented from a guess would refuse legal values and pass illegal
    # ones with equal confidence.
    # PRICING, from the operator. Two columns, and WE ARE IN THE EXPENSIVE
    # ONE. "With video input" is cheaper per second only because it is billed
    # Price x (Input + Output) instead of Price x Output — it applies when you
    # supply a reference VIDEO. We supply a reference IMAGE, so every clip here
    # bills at the "no video" rate.
    #   480P   $0.085/s with video   |  $0.140/s no video
    #   720P   $0.190/s with video   |  $0.315/s no video
    #  1080P   $0.3425/s with video  |  $0.570/s no video
    # The 1080P figures include a 28% discount that expires 17 Sep 2026, so a
    # 1080P estimate made after that date will be low. Prices are beta.
    # A high-tier top-up adds 10%, making the effective rate ~10% lower; that
    # is a property of the ACCOUNT, not of a generation, so it is not applied
    # here — an estimate should never flatter itself.
    SEEDANCE = "bytedance/seedance-2-5"
    SEEDANCE_PER_SEC = {                 # (with video input, no video input)
        "480p":  (0.085, 0.140),
        "720p":  (0.190, 0.315),
        "1080p": (0.3425, 0.570),
    }
    SEEDANCE_MAX_REFS = 2

    def seedance(self, prompt: str, reference_paths=None, duration: int = 8,
                 resolution: str = "720p", aspect_ratio: str = "9:16",
                 generate_audio: bool = False, log=None) -> str:
        """Seedance 2.5 reference-to-video."""
        import json as _j, time as _t
        from pathlib import Path as _P
        paths = [_P(x) for x in (reference_paths or [])]
        if len(paths) > self.SEEDANCE_MAX_REFS:
            raise ValueError(f"{len(paths)} references; Seedance 2.5 takes at "
                             f"most {self.SEEDANCE_MAX_REFS}")
        if not 1 <= len(prompt) <= 7000:
            raise ValueError(f"prompt is {len(prompt)} chars")
        for q in paths:
            self.check_reference(q)          # H3's bounds; Seedance's are not
                                             # published, and these are sane
        body = {"model": self.SEEDANCE,
                "input": {"prompt": prompt,
                          "duration": int(duration),
                          "resolution": resolution,
                          "aspect_ratio": aspect_ratio,
                          # the voice-over is added later; a generated track
                          # would only have to be stripped again
                          "generate_audio": bool(generate_audio)}}
        if paths:
            body["input"]["reference_image_urls"] = [self.upload(q)
                                                     for q in paths]
        d = self._req("POST", "/api/v1/jobs/createTask", json=body)
        tid = (d.get("data") or {}).get("taskId")
        if not tid:
            raise RuntimeError(f"no taskId: {_j.dumps(d)[:300]}")
        got = self._wait(tid)
        if not got:
            raise RuntimeError("done but no video url")
        if log is not None:
            with open(log, "a", encoding="utf-8") as fh:
                fh.write(_j.dumps({"ts": _t.time(), "model": self.SEEDANCE,
                                   "refs": [q.name for q in paths],
                                   "duration": duration,
                                   "resolution": resolution,
                                   "aspect": aspect_ratio,
                                   "prompt": prompt[:600]},
                                  ensure_ascii=False) + "\n")
        return got[0]

    @staticmethod
    def download(url: str, dest: Path) -> int:
        with requests.get(url, timeout=180, stream=True) as r:
            r.raise_for_status()
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(dest.suffix + ".part")
            n = 0
            with tmp.open("wb") as f:
                for c in r.iter_content(1 << 16):
                    f.write(c); n += len(c)
            tmp.replace(dest)      # atomic: the QC gate never sees a half file
            return n


# ---------------------------------------------------------------- pricing --
# Kie bills a FLAT rate per generation, references included. No per-pixel
# model, no input-token term — that was fal's shape and it is the reason we
# came back.
def image_cost(aspect: str = "3:4", tier: str = "2k",
               n_refs: int = 0, ref_edge: int | None = None,
               model: str | None = None) -> float:
    """Signature kept identical to fal_api.image_cost so no caller changes.
    n_refs and ref_edge are accepted and ignored: Kie does not charge for
    reference images."""
    return PRICE.get(model or MODEL_I2I, 0.09)


# Published MiniMax rates via Kie: per second of output, plus each input frame.
VIDEO_PER_SEC = {"768P": 0.08, "2K": 0.13}
PER_INPUT_IMAGE = 0.04


def video_cost(seconds: int, resolution: str = "768P", n_refs: int = 0) -> float:
    if resolution not in VIDEO_PER_SEC:
        raise ValueError(f"no rate for resolution {resolution!r}")
    return round(VIDEO_PER_SEC[resolution] * seconds
                 + PER_INPUT_IMAGE * n_refs, 4)


def seedance_cost(seconds: int, resolution: str = "720p",
                  has_video_ref: bool = False) -> float:
    """Seedance 2.5, billed per second of output at a rate set by resolution.

    `has_video_ref` picks the cheaper column and is FALSE for everything this
    project does: the plate is an image. Getting that wrong understates every
    720P estimate by 66%.
    """
    r = Kie.SEEDANCE_PER_SEC.get(str(resolution).lower())
    if r is None:
        raise ValueError(f"unknown Seedance resolution {resolution!r}; "
                         f"known: {sorted(Kie.SEEDANCE_PER_SEC)}")
    return seconds * r[0 if has_video_ref else 1]


def ref_video_cost(seconds: int, resolution: str = "768P",
                   n_refs: int = 3) -> float:
    """Same per-second rate as image-to-video, plus every reference as an
    input image. Nine references is $0.36 of input on its own, so the
    reference count is a cost decision and not only a quality one."""
    return video_cost(seconds, resolution, n_refs)
