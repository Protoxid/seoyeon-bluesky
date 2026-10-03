import os
import sys
import subprocess
import time
import sqlite3
import json

def log(msg):
    print(f"[SETUP] {msg}", flush=True)

def main():
    model_path = os.path.expandvars(r"%USERPROFILE%\.lmstudio\models\bartowski\Qwen2.5-Coder-14B-Instruct-abliterated-GGUF\Qwen2.5-Coder-14B-Instruct-abliterated-Q4_K_M.gguf")
    
    if not os.path.exists(model_path):
        part_path = model_path + ".part"
        if os.path.exists(part_path):
            size_mb = os.path.getsize(part_path) / (1024*1024)
            log(f"Download still in progress... currently at {size_mb:.1f} MB.")
            return False
        else:
            log(f"Model file not found at {model_path}!")
            return False

    size_gb = os.path.getsize(model_path) / (1024*1024*1024)
    log(f"Found Qwen 2.5 Coder 14B Abliterated GGUF ({size_gb:.2f} GB).")

    identifier = "qwen2.5-coder-14b-instruct-abliterated"

    # 1. Unload old model
    log("Unloading current models from LM Studio...")
    subprocess.run(["lms", "unload", "--all"], capture_output=True)

    # 2. Load Qwen 2.5 Coder 14B Abliterated
    log("Loading Qwen 2.5 Coder 14B Abliterated with 100% GPU offload, 16K context, parallel=1...")
    cmd = ["lms", "load", identifier, "--gpu", "max", "-c", "16384", "--parallel", "1", "-y", "--identifier", identifier]
    res = subprocess.run(cmd, capture_output=True, text=True)
    log(f"LM Studio Load Result: {res.stdout.strip() or res.stderr.strip()}")

    # 3. Update Roo Code configuration in state.vscdb
    log("Updating Roo Code settings for Operator...")
    db_path = os.path.expandvars(r"%APPDATA%\Code\User\globalStorage\state.vscdb")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT value FROM ItemTable WHERE key = 'RooVeterinaryInc.roo-cline'")
        row = c.fetchone()
        if row:
            val = json.loads(row[0])
            val['lmStudioModelId'] = identifier
            for item in val.get('listApiConfigMeta', []):
                if item.get('name') == 'default':
                    item['modelId'] = identifier
            c.execute("UPDATE ItemTable SET value = ? WHERE key = 'RooVeterinaryInc.roo-cline'", (json.dumps(val),))
            conn.commit()
            log(f"Updated Roo Code database to use {identifier}.")
        conn.close()

    # 4. Update orchestrator/config.py
    config_py = r"c:\AI-Project\orchestrator\config.py"
    if os.path.exists(config_py):
        with open(config_py, "r", encoding="utf-8") as f:
            content = f.read()
        for old_id in ["huihui-qwen3.8-27b-abliterated", "qwen2.5-coder-14b-instruct"]:
            content = content.replace(old_id, identifier)
        with open(config_py, "w", encoding="utf-8") as f:
            f.write(content)
        log(f"Updated orchestrator/config.py to use {identifier}.")

    # 5. Update start script
    start_ps1 = r"c:\AI-Project\scripts\start_lmstudio_operator.ps1"
    if os.path.exists(start_ps1):
        with open(start_ps1, "r", encoding="utf-8") as f:
            content = f.read()
        import re
        content = re.sub(r'\$modelKey\s*=\s*"[^"]+"', f'$modelKey = "{identifier}"', content)
        with open(start_ps1, "w", encoding="utf-8") as f:
            f.write(content)
        log(f"Updated start_lmstudio_operator.ps1 to default to {identifier}.")

    log("Setup complete! Model is active and ready.")
    return True

if __name__ == "__main__":
    main()
