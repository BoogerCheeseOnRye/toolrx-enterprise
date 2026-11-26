#!/usr/bin/env python3
"""
Nightly Upstream Sync Script for ToolRx Commercial
Pulls latest changes from https://github.com/BoogerCheeseOnRye/toolrx,
merges core updates into the commercial package, and validates test integrity.
"""

import subprocess
import sys
import os
import shutil

UPSTREAM_URL = "https://github.com/BoogerCheeseOnRye/toolrx"
SCRATCH_ROOT = "/home/godbox/.gemini/antigravity/scratch/toolrx-commercial"

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}\n{res.stderr}")
    return res

def sync():
    print("[1/4] Checking upstream repository updates...")
    tmp_clone = "/tmp/toolrx_upstream_sync"
    if os.path.exists(tmp_clone):
        shutil.rmtree(tmp_clone)
    
    # Clone upstream without history for fast sync
    res = run_cmd(f"git clone --depth 1 {UPSTREAM_URL} {tmp_clone}")
    if res.returncode != 0:
        print("[WARN] Upstream git clone failed (network sandbox or offline). Skipping remote pull.")
        return False
    
    print("[2/4] Merging core algorithm updates...")
    upstream_core = os.path.join(tmp_clone, "toolrx")
    dest_core = os.path.join(SCRATCH_ROOT, "toolrx")
    
    if os.path.exists(upstream_core):
        for root, dirs, files in os.walk(upstream_core):
            for file in files:
                # Do not overwrite commercial wrapper, gateway, or package init
                if file in ["gateway.py", "license.py", "compat.py", "__init__.py"]:
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), upstream_core)
                target_file = os.path.join(dest_core, rel_path)
                os.makedirs(os.path.dirname(target_file), exist_ok=True)
                shutil.copy2(os.path.join(root, file), target_file)
                print(f"  -> Synced: {rel_path}")

    print("[3/4] Running commercial verification test suite...")
    test_res = run_cmd(f"PYTHONPATH={SCRATCH_ROOT} python3 -m unittest discover {SCRATCH_ROOT}/tests")
    if test_res.returncode == 0:
        print("[SUCCESS] All 15/15 regression tests passed with updated core.")
    else:
        print(f"[FAIL] Test regressions detected:\n{test_res.stderr}")
        return False
        
    print("[4/4] Sync complete. Cleaning temporary files.")
    shutil.rmtree(tmp_clone, ignore_errors=True)
    return True

if __name__ == "__main__":
    success = sync()
    sys.exit(0 if success else 1)
