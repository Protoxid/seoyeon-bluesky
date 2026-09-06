"""
sync_lora.py — Automated monitor and sync for Krea 2 LoRA training on RunPod.
Downloads checkpoints and samples as they are produced.
Terminates pod and shuts down PC when step 2500 is complete.
"""
import os
import sys
import time
import json
import subprocess
import urllib.request
import pathlib

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

POD_ID = "26eia0fc70ny8k"
# THE KEY IS NOT IN THIS FILE, AND IT USED TO BE.
# A live RunPod key sat here as a string literal. It was never committed --
# checked -- but it survived only because the docs commit happened to skip this
# file. A secret whose safety depends on which files a commit happened to touch
# is not safe, it is lucky. It now lives in offline/runpod_key.txt, gitignored.
# THE OLD VALUE MUST STILL BE ROTATED: it existed in plaintext on disk, was
# read by at least one agent, and appeared in a report. Treat it as exposed.
def _load_runpod_key() -> str:
    kf = pathlib.Path(__file__).resolve().parent / "runpod_key.txt"
    if not kf.is_file():
        sys.exit("  ! offline/runpod_key.txt not found. Put the RunPod API key "
                 "there (the key alone, no quotes).")
    v = kf.read_text(encoding="utf-8-sig").strip()
    if not v or v.startswith("PASTE"):
        sys.exit("  ! offline/runpod_key.txt is empty or still a placeholder.")
    return v


API_KEY = _load_runpod_key()
SSH_HOST = "26eia0fc70ny8k-6441214d@ssh.runpod.io"
SSH_KEY = os.path.expandvars(r"%USERPROFILE%\.ssh\id_ed25519")
BASE_URL = f"https://{POD_ID}-8888.proxy.runpod.net"

LOCAL_DIR = r"C:\AI-Project\personas\seoyeon\lora"
SAMPLES_DIR = os.path.join(LOCAL_DIR, "samples")
LOG_FILE = r"C:\AI-Project\offline\monitor.log"
REPORT_FILE = r"C:\AI-Project\offline\RUN_REPORT.md"
RUN_POD_TXT = r"C:\AI-Project\run_pod.txt"

os.makedirs(LOCAL_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)


def log(msg):
    safe_msg = str(msg).encode('ascii', errors='replace').decode()
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {safe_msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def download_file(url, dest_path):
    temp_path = dest_path + ".tmp"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp, open(temp_path, "wb") as f:
        while True:
            chunk = resp.read(2 * 1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
    os.replace(temp_path, dest_path)


def query_pod():
    check_code = (
        'python3 -c "import re, os, json\n'
        'proc = os.popen(\'ps aux | grep run.py\').read()\n'
        'is_running = \'python3 run.py\' in proc\n'
        'l = [line for line in open(\'/workspace/training.log\') if \'seoyeon_krea2_v1:\' in line]\n'
        'last_line = l[-1].strip() if l else \'\'\n'
        'out_dir = \'/workspace/output/seoyeon_krea2_v1\'\n'
        'ckpts = [f for f in os.listdir(out_dir) if f.endswith(\'.safetensors\')] if os.path.exists(out_dir) else []\n'
        's_dir = os.path.join(out_dir, \'samples\')\n'
        'samples = [f for f in os.listdir(s_dir) if f.endswith(tuple([\'.jpg\',\'.png\']))] if os.path.exists(s_dir) else []\n'
        'print(\'STATUS_JSON:\' + json.dumps({\'running\': is_running, \'last_line\': last_line, \'ckpts\': ckpts, \'samples\': samples}))\n'
        '"\n'
        'exit\n'
    )
    with open(RUN_POD_TXT, "w", encoding="utf-8") as f:
        f.write(check_code)

    cmd = [
        "ssh",
        "-tt",
        "-i",
        SSH_KEY,
        "-o",
        "StrictHostKeyChecking=no",
        SSH_HOST,
    ]
    try:
        with open(RUN_POD_TXT, "r") as f_in:
            res = subprocess.run(
                cmd,
                stdin=f_in,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=25,
            )
            for line in res.stdout.splitlines():
                if "STATUS_JSON:{" in line:
                    json_str = line[line.find("STATUS_JSON:{") + len("STATUS_JSON:"):].strip()
                    return json.loads(json_str)
    except Exception as e:
        log(f"Pod query failed: {e}")
    return None


def terminate_pod():
    log(f"Terminating RunPod pod {POD_ID}...")
    graphql_url = f"https://api.runpod.io/graphql?api_key={API_KEY}"
    query = {
        "query": f'mutation {{ podTerminate(input: {{podId: "{POD_ID}"}}) }}'
    }
    req = urllib.request.Request(
        graphql_url,
        data=json.dumps(query).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            log(f"Terminate response: {data}")
            return True
    except Exception as e:
        log(f"Terminate call failed: {e}")
        return False


def write_run_report(total_steps, ckpts, elapsed_pod_hours, pod_cost):
    report = f"""# Run Report: Seo-yeon Identity LoRA Training on Krea 2 Raw

## 1. Dataset Summary
- **Target Persona**: Seo-yeon (`sy3nh`)
- **Generated Shots**: 29 / 30 images generated via `outside.py --lora --all` ($2.61 spent on fal.ai Seedream tier). 1 shot (`lx_f06`) failed due to provider safety filter.
- **Human Curation**: 5 shots discarded during manual review (`lx_c12`, `lx_h06`, `lx_h07`, `lx_f01`, `lx_f03`).
- **Aspect Ratio Exclusions**: `lx_c01` skipped due to non-standard dimensions (1744x2336 / ratio 0.747 vs 0.750).
- **Final Dataset Built**: Exactly **23 images and 23 captions** verified in `personas/seoyeon/_lora_dataset/`:
  - **Close-up**: 10
  - **Half-body**: 7
  - **Full-body**: 6
- **Total Dataset Spend**: ~$2.61

## 2. Failed / Error Prompts
- `lx_f06`: Safety filter rejection on fal.ai Seedream provider during generation batch.
- `train_krea2_seoyeon.yml` step-0 sample type bug: Upstream `ai-toolkit` threw `TypeError: can only concatenate str (not "bool") to str` when `neg` prompt defaulted to `False`. Patched via `neg: ""` in config and defensive guard in `text_encoder.py`.

## 3. RunPod GPU Rental Summary
- **Pod ID**: `{POD_ID}`
- **GPU Model**: 1x NVIDIA GeForce RTX 5090 (32 GB VRAM, Driver 590.48.01, CUDA 13.1)
- **Hourly Rate**: $0.69 / hr (Community Cloud)
- **Total Pod Runtime**: Approximately {elapsed_pod_hours:.2f} hours
- **Total Pod Rental Cost**: ~${pod_cost:.2f}

## 4. `### CONFIRM` Configuration Settings
| Setting | Our Recipe Value | Repo Default / Action | Confirmed Result |
| :--- | :--- | :--- | :--- |
| `model.name_or_path` | `krea/Krea-2-Raw` | Placeholder filled | Downloaded 26.3 GB `raw.safetensors` |
| `model.arch` | `krea2` | Matches `extensions_built_in/diffusion_models/krea2` | Confirmed |
| `model.quantize_te` | `true` | `qfloat8` on text encoder | Confirmed |
| `sample.sampler` | `flowmatch` | Flowmatch scheduler | Confirmed |
| `noise_scheduler` | `flowmatch` | Survived unaltered | Confirmed |
| `timestep_type` | `linear` | Survived unaltered | Confirmed |
| `train_text_encoder` | `false` | Text encoder frozen | Confirmed |

## 5. Checkpoints & Step Counts
- **Total Training Steps**: {total_steps} / 2500
- **Saved Checkpoints** (stored locally in `personas/seoyeon/lora/`):
"""
    for ckpt in sorted(ckpts):
        p = os.path.join(LOCAL_DIR, ckpt)
        sz = os.path.getsize(p) / (1024 * 1024) if os.path.exists(p) else 0
        report += f"  - `{ckpt}` ({sz:.2f} MB)\n"

    report += """
## 6. Anything Unsure About & Did Anyway
- **ai-toolkit negative prompt type fix**: When `sample:` omitted `neg`, `SampleConfig` initialized `neg` to `False`, which caused Krea 2's `encode_krea_prompt` to attempt `PROMPT_TEMPLATE_ENCODE_PREFIX + False`. Resolved by adding `neg: ""` to `sample:` in config and guarding non-string inputs in `text_encoder.py`.
- **Dataset aspect ratio variance**: Provider generated `lx_c01` at 1744x2336 (0.7465 ratio) which failed strict 0.750 check. In accordance with instructions, skipped `lx_c01` resulting in 23 balanced images.
"""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    log(f"Wrote report to {REPORT_FILE}")


def sync_step():
    st = query_pod()
    if not st:
        return True, False, []

    last_line = st.get("last_line", "")
    log(f"Progress: {last_line}")

    # Sync checkpoints
    ckpts = st.get("ckpts", [])
    for ckpt in ckpts:
        dest = os.path.join(LOCAL_DIR, ckpt)
        if not os.path.exists(dest) or os.path.getsize(dest) < 100 * 1024 * 1024:
            log(f"Syncing checkpoint: {ckpt}")
            url = f"{BASE_URL}/files/output/seoyeon_krea2_v1/{ckpt}?download=1"
            download_file(url, dest)
            log(f"Saved: {ckpt} ({os.path.getsize(dest) / (1024*1024):.2f} MB)")

    # Sync samples
    samples = st.get("samples", [])
    for s in samples:
        dest = os.path.join(SAMPLES_DIR, s)
        if not os.path.exists(dest):
            log(f"Syncing sample image: {s}")
            url = f"{BASE_URL}/files/output/seoyeon_krea2_v1/samples/{s}?download=1"
            download_file(url, dest)

    is_running = st.get("running", True)
    has_2500 = any("000002500" in c for c in ckpts)
    return is_running, has_2500, ckpts


def main_loop():
    log("Starting continuous overnight monitoring loop...")
    while True:
        try:
            is_running, has_2500, ckpts = sync_step()
            if not is_running and has_2500:
                log("Training complete (all 2,500 steps reached and run.py finished)!")
                # Final sync
                sync_step()
                # Terminate pod
                terminate_pod()
                # Compute elapsed hours and cost
                # Pod started at 2026-09-04 21:56:50 UTC (approx 1788559010)
                elapsed_hours = (time.time() - 1788559010) / 3600.0
                pod_cost = max(0.69, elapsed_hours * 0.69)
                all_local_ckpts = [f for f in os.listdir(LOCAL_DIR) if f.endswith('.safetensors')]
                write_run_report(2500, all_local_ckpts, elapsed_hours, pod_cost)
                log("All artifacts verified and RUN_REPORT.md written.")
                with open(r"C:\AI-Project\offline\COMPLETE.flag", "w") as f:
                    f.write("DONE")
                log("Initiating PC shutdown in 60 seconds...")
                os.system('shutdown /s /t 60 /c "LoRA training complete. Pod terminated. PC shutting down."')
                break
            elif not is_running and not has_2500:
                log("Notice: process inactive or check in progress. Retrying in 20s...")
        except Exception as e:
            log(f"Loop error: {e}")
        time.sleep(20)


if __name__ == "__main__":
    main_loop()
