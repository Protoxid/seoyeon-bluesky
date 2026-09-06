"""
run_comfy_exclusive.py

Automates generation of Seoyeon exclusive / Fanvue shots through a local ComfyUI instance running FLUX.2 with native multi-reference conditioning.

Usage:
  python run_comfy_exclusive.py --shot ex_bed_shirt
  python run_comfy_exclusive.py --shot ex_towel_mirror --seed 12345
  python run_comfy_exclusive.py --list
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import argparse
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent
COMFY_DIR = PROJECT_ROOT / "comfyui"
API_WORKFLOW_PATH = COMFY_DIR / "flux2_seoyeon_api.json"
CONTENT_EXCLUSIVE_DIR = BASE_DIR / "content" / "exclusive"
MASTER_A1 = BASE_DIR / "master" / "a" / "a1_front.png"
MASTER_C5 = BASE_DIR / "master" / "c" / "c5_relax_front.png"

COMFY_HOST = "127.0.0.1:8188"

def check_comfy_alive():
    """Verify if ComfyUI server is reachable."""
    url = f"http://{COMFY_HOST}/system_stats"
    try:
        req = urllib.request.urlopen(url, timeout=3)
        return req.status == 200
    except Exception:
        return False

def upload_image_to_comfy(file_path: Path, subfolder="", overwrite=True):
    """Upload reference image directly to ComfyUI input folder via API."""
    import mimetypes
    url = f"http://{COMFY_HOST}/upload/image"
    
    boundary = "----WebKitFormBoundary" + str(int(time.time() * 1000))
    body = []
    
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="image"; filename="{file_path.name}"'.encode())
    mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    body.append(f"Content-Type: {mime_type}".encode())
    body.append(b"")
    with open(file_path, "rb") as f:
        body.append(f.read())
        
    if subfolder:
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="subfolder"')
        body.append(b"")
        body.append(subfolder.encode())
        
    if overwrite:
        body.append(f"--{boundary}".encode())
        body.append(b'Content-Disposition: form-data; name="overwrite"')
        body.append(b"")
        body.append(b"true")
        
    body.append(f"--{boundary}--".encode())
    body.append(b"")
    payload = b"\r\n".join(body)
    
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def queue_prompt(prompt_workflow):
    """Submit a prompt graph to ComfyUI's queue."""
    url = f"http://{COMFY_HOST}/prompt"
    data = json.dumps({"prompt": prompt_workflow}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get_history(prompt_id):
    """Fetch status and outputs for prompt_id."""
    url = f"http://{COMFY_HOST}/history/{prompt_id}"
    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {}

def download_output_image(filename, subfolder, folder_type, dest_path: Path):
    """Download generated output image from ComfyUI."""
    params = urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
    url = f"http://{COMFY_HOST}/view?{params}"
    with urllib.request.urlopen(url) as resp:
        dest_path.write_bytes(resp.read())

def get_shot_prompt(shot_name):
    """Retrieve prompt text from exclusive_shots.py."""
    sys.path.insert(0, str(BASE_DIR))
    try:
        import exclusive_shots
        if hasattr(exclusive_shots, "SHOTS"):
            for s in exclusive_shots.SHOTS:
                if s.get("id") == shot_name:
                    return s.get("text") or s.get("prompt")
    except Exception as e:
        print(f"[!] Error loading exclusive_shots: {e}")
    return None

def main():
    parser = argparse.ArgumentParser(description="Generate Seoyeon Fanvue shots locally via FLUX.2 in ComfyUI.")
    parser.add_argument("--shot", type=str, default="ex_bed_shirt", help="Shot ID from exclusive_shots.py")
    parser.add_argument("--seed", type=int, default=None, help="Custom seed")
    parser.add_argument("--list", action="store_true", help="List available exclusive shots")
    args = parser.parse_args()

    sys.path.insert(0, str(BASE_DIR))
    import exclusive_shots

    available_shots = []
    if hasattr(exclusive_shots, "SHOTS"):
        available_shots = [s.get("id") for s in exclusive_shots.SHOTS if "id" in s]

    if args.list:
        print("\nAvailable Exclusive Shots:")
        for s in available_shots:
            print(f"  - {s}")
        return

    if not check_comfy_alive():
        print(f"[!] ComfyUI is not reachable at http://{COMFY_HOST}.")
        print("    Please start your ComfyUI server first (e.g., run_nvidia_gpu.bat).")
        return

    print(f"[+] ComfyUI detected online at http://{COMFY_HOST}")

    # Ensure reference images are uploaded
    if MASTER_A1.exists():
        print(f"[+] Uploading reference 1: {MASTER_A1.name} ...")
        upload_image_to_comfy(MASTER_A1)
    if MASTER_C5.exists():
        print(f"[+] Uploading reference 2: {MASTER_C5.name} ...")
        upload_image_to_comfy(MASTER_C5)

    # Load workflow template
    with open(API_WORKFLOW_PATH, "r", encoding="utf-8") as f:
        workflow = json.load(f)

    # Update prompt if shot exists
    shot_prompt = get_shot_prompt(args.shot)
    if shot_prompt:
        print(f"[+] Applying prompt for shot '{args.shot}':")
        print(f"    \"{shot_prompt[:90]}...\"")
        workflow["5"]["inputs"]["text"] = shot_prompt
    else:
        print(f"[*] Shot '{args.shot}' not found in exclusive_shots. Using default prompt.")

    # Apply seed
    import random
    seed = args.seed if args.seed is not None else random.randint(100000, 999999999)
    workflow["17"]["inputs"]["seed"] = seed
    print(f"[+] Using seed: {seed}")

    # Set reference images
    workflow["8"]["inputs"]["image"] = MASTER_A1.name
    workflow["12"]["inputs"]["image"] = MASTER_C5.name

    # Queue execution
    print("[+] Queueing generation on FLUX.2 ...")
    res = queue_prompt(workflow)
    prompt_id = res.get("prompt_id")
    if not prompt_id:
        print(f"[!] Failed to queue prompt: {res}")
        return

    print(f"[+] Prompt ID: {prompt_id}. Waiting for generation to complete...")

    CONTENT_EXCLUSIVE_DIR.mkdir(parents=True, exist_ok=True)

    # Poll status
    start_time = time.time()
    while time.time() - start_time < 300:
        hist = get_history(prompt_id)
        if prompt_id in hist:
            outputs = hist[prompt_id].get("outputs", {})
            for node_id, out_data in outputs.items():
                if "images" in out_data:
                    for img in out_data["images"]:
                        fname = img["filename"]
                        sfolder = img.get("subfolder", "")
                        ftype = img.get("type", "output")
                        dest = CONTENT_EXCLUSIVE_DIR / f"{args.shot}_{seed[:6] if isinstance(seed, str) else str(seed)[-6:]}.png"
                        download_output_image(fname, sfolder, ftype, dest)
                        print(f"\n[✔] Image successfully generated and saved to:")
                        print(f"    {dest}")
                        return
        time.sleep(2)
        print(".", end="", flush=True)

    print("\n[!] Timed out waiting for image generation.")

if __name__ == "__main__":
    main()
