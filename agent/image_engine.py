"""
agent/image_engine.py — Kie.ai Image Generator with Canonical Reference Conditioning.

Generates photorealistic, identity-locked images of Han Seo-yeon through Kie.ai:
  - Model: gpt-image-2-5-sunburst-image-to-image (project canon)
  - References: Conditioned on personas/seoyeon/master/a/a1_front.png via Kie file host
  - Aspect: 3:4 portrait (or 1:1) at 1K resolution (clean sensor grain, fast, budget-efficient)
  - Supports DRY_RUN mode (simulates full pipeline without consuming Kie credits)
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from typing import List, Optional, Tuple
from PIL import Image

from .config import PROJECT_ROOT, config
from .visual_identity import build_image_prompt

KIE_API_BASE = "https://api.kie.ai"
KIE_UPLOAD_BASE = "https://kieai.redpandaai.co"
MASTER_A1_PATH = PROJECT_ROOT / "personas" / "seoyeon" / "master" / "a" / "a1_front.png"


def _is_url_alive(url: str) -> bool:
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "SeoYeonAgent/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status in (200, 206)
    except Exception:
        return False


def get_or_upload_master_reference(path: pathlib.Path, api_key: str) -> Optional[str]:
    """
    Uploads the master identity face reference to Kie file host with disk caching.
    Reuses existing cached URL in .url sidecar if still alive.
    """
    if not path.exists():
        return None

    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    sidecar = path.with_suffix(path.suffix + ".url")

    if sidecar.exists():
        try:
            parts = sidecar.read_text(encoding="utf-8").strip().split()
            if len(parts) == 2 and parts[0] == digest and parts[1].startswith("http"):
                if _is_url_alive(parts[1]):
                    return parts[1]
        except Exception:
            pass

    # Upload base64 to Kie
    ext = path.suffix.lower().lstrip(".") or "png"
    mime = "jpeg" if ext == "jpg" else ext
    b64_content = base64.b64encode(path.read_bytes()).decode("utf-8")
    payload = {
        "base64Data": f"data:image/{mime};base64,{b64_content}",
        "uploadPath": "images/persona",
        "fileName": f"{path.stem}_{digest[:10]}.{ext}",
    }

    url = f"{KIE_UPLOAD_BASE}/api/file-base64-upload"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            remote_url = (data.get("data") or {}).get("url") or data.get("url")
            if remote_url:
                sidecar.write_text(f"{digest} {remote_url}\n", encoding="utf-8")
                return remote_url
    except Exception as e:
        print(f"[ImageEngine] Warning: Kie reference upload failed: {e}")

    return None


class ImageEngine:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.kie_api_key

    def generate_image(
        self,
        scene_description: str,
        mood: Optional[str] = None,
        aspect: str = "3:4",
        dry_run: Optional[bool] = None,
    ) -> Tuple[Optional[bytes], str, Optional[str]]:
        """
        Generates an identity-locked image through Kie.ai API.
        Returns: (image_bytes, prompt_used, error_or_notes)
        """
        is_dry = dry_run if dry_run is not None else config.dry_run
        prompt = build_image_prompt(scene_description, mood=mood)

        if is_dry:
            print(f"[DRY-RUN Kie ImageEngine] Model: {config.kie_image_model}")
            print(f"[DRY-RUN Kie ImageEngine] Master Ref: {MASTER_A1_PATH.name}")
            print(f"[DRY-RUN Kie ImageEngine] Prompt: \"{prompt[:130]}...\"")
            buf = io.BytesIO()
            dummy_img = Image.new("RGB", (400, 533), color=(215, 210, 205))
            dummy_img.save(buf, format="JPEG")
            return buf.getvalue(), prompt, None

        if not self.api_key:
            return None, prompt, "KIE_API_KEY is not configured (check kie_key.txt or .env)."

        # 1. Obtain master face reference URL
        ref_url = get_or_upload_master_reference(MASTER_A1_PATH, self.api_key)
        model = config.kie_image_model

        # 2. Build task payload
        task_input: dict = {
            "prompt": prompt,
            "aspect_ratio": aspect,
            "resolution": "1K",
        }
        if ref_url and "image-to-image" in model:
            task_input["input_urls"] = [ref_url]
            task_input["background"] = "auto"
            print(f"[Kie ImageEngine] Model: {model} | Identity Reference Fed: {MASTER_A1_PATH.name} -> {ref_url}")
        else:
            print(f"[Kie ImageEngine] Model: {model} | Notice: Running text-to-image without reference conditioning")

        print(f"[Kie ImageEngine] Generating image with prompt: \"{prompt[:160]}...\"")

        payload = {
            "model": model,
            "input": task_input,
        }

        # 3. Create task on Kie
        create_url = f"{KIE_API_BASE}/api/v1/jobs/createTask"
        req = urllib.request.Request(
            create_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                task_id = (data.get("data") or {}).get("taskId")
                if not task_id:
                    return None, prompt, f"Kie did not return taskId: {json.dumps(data)}"
        except Exception as e:
            return None, prompt, f"Kie createTask failed: {e}"

        # 4. Poll task completion
        print(f"[Kie ImageEngine] Task {task_id} queued on Kie ({model}). Polling...")
        poll_url = f"{KIE_API_BASE}/api/v1/jobs/recordInfo?taskId={task_id}"
        poll_headers = {"Authorization": f"Bearer {self.api_key}"}

        start_time = time.time()
        timeout = 240.0  # 4 minutes

        while time.time() - start_time < timeout:
            time.sleep(4.0)
            try:
                poll_req = urllib.request.Request(poll_url, headers=poll_headers)
                with urllib.request.urlopen(poll_req, timeout=20) as p_resp:
                    p_data = json.loads(p_resp.read().decode("utf-8"))
                    job_data = p_data.get("data") or {}
                    state = str(job_data.get("state", job_data.get("status", ""))).lower()

                    if state in ("success", "succeeded", "completed", "1"):
                        raw = job_data.get("resultJson") or job_data.get("result") or "{}"
                        res = json.loads(raw) if isinstance(raw, str) else raw
                        urls = (
                            res.get("resultUrls")
                            or res.get("urls")
                            or res.get("images")
                            or res.get("resultUrl")
                            or []
                        )
                        if isinstance(urls, str):
                            urls = [urls]
                        if not urls:
                            return None, prompt, "Kie reported success but returned no resultUrls."

                        img_url = urls[0]
                        print(f"[Kie ImageEngine] Image ready at: {img_url}")

                        # 5. Download image binary
                        dl_req = urllib.request.Request(img_url, headers={"User-Agent": "SeoYeonAgent/1.0"})
                        with urllib.request.urlopen(dl_req, timeout=30) as dl_resp:
                            return dl_resp.read(), prompt, None

                    elif state in ("fail", "failed", "error", "2", "3"):
                        fail_msg = (
                            job_data.get("failMsg")
                            or job_data.get("errorMessage")
                            or "generation failed"
                        )
                        return None, prompt, f"Kie generation failed: {fail_msg}"

            except Exception as e:
                print(f"[Kie ImageEngine] Polling notice: {e}")

        return None, prompt, f"Kie task {task_id} timed out after {timeout}s"


image_engine = ImageEngine()
