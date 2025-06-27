
# File: deploy.py
# Finalized & Hardened Deployment Script for Cryptex AI Windmill Project

import os
import requests
import json
import yaml
import time
import re

# --- CONFIG: Use environment variables or Windmill secrets for secure deployment ---
WINDMILL_BASE_URL = os.getenv("WINDMILL_BASE_URL")  # e.g., http://your-vps-ip
WINDMILL_TOKEN = os.getenv("WINDMILL_TOKEN")        # your Windmill auth token
WORKSPACE = os.getenv("WINDMILL_WORKSPACE", "cryptex_ai_omega")
PROJECT_DIR = "cryptex_project"
# ------------------------------------------------------------------------------------

HEADERS = {
    "Authorization": f"Bearer {WINDMILL_TOKEN}",
    "Content-Type": "application/json"
}

def extract_summary_from_script(content):
    """Extracts top-level docstring or fallback summary for Windmill UI."""
    summary = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    return summary[0].strip() if summary else "Cryptex script"

def deploy_resource(filepath):
    """Determines the resource type and deploys it with the correct API payload."""
    path_in_windmill = os.path.splitext(os.path.relpath(filepath, PROJECT_DIR))[0].replace(os.path.sep, "/")
    payload = None
    item_type = None

    if filepath.endswith((".py", ".ts")):
        item_type = "script"
        language = "python3" if filepath.endswith(".py") else "typescript"
        api_path_create = f"/api/w/{WORKSPACE}/scripts/create"
        api_path_update = f"/api/w/{WORKSPACE}/scripts/update"
        with open(filepath, "r", encoding='utf-8') as f:
            content = f.read()
        summary = extract_summary_from_script(content)
        payload = {
            "path": path_in_windmill,
            "content": content,
            "language": language,
            "summary": summary
        }

    elif filepath.endswith((".yml", ".yaml")):
        item_type = "flow"
        api_path_create = f"/api/w/{WORKSPACE}/flows/create"
        api_path_update = f"/api/w/{WORKSPACE}/flows/update"
        with open(filepath, "r", encoding='utf-8') as f:
            content_yaml = yaml.safe_load(f)
        flow_path = os.path.splitext(os.path.relpath(filepath, PROJECT_DIR))[0].replace(os.path.sep, "/")
        payload = {
            "path": flow_path,
            "summary": content_yaml.get("summary", "Cryptex flow"),
            "value": content_yaml
        }

    if not payload:
        return

    create_url = f"{WINDMILL_BASE_URL}{api_path_create}"
    update_url = f"{WINDMILL_BASE_URL}{api_path_update}"

    try:
        print(f"> Deploying {item_type.upper()} to {path_in_windmill}")
        response = requests.post(create_url, headers=HEADERS, json=payload, timeout=30)

        if response.status_code == 409:
            print(f"⚠️  Already exists. Updating {path_in_windmill}...")
            response = requests.post(update_url, headers=HEADERS, json=payload, timeout=30)

        response.raise_for_status()
        print(f"✅ Deployed {item_type.upper()}: {filepath}")

    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED to deploy {item_type.upper()}: {filepath}")
        error_text = e.response.text if hasattr(e, 'response') and e.response else str(e)
        print(f"   Error: {error_text}")
        print("   Retrying in 2 seconds...")
        time.sleep(2)
        try:
            response = requests.post(update_url, headers=HEADERS, json=payload, timeout=30)
            response.raise_for_status()
            print(f"♻️  Retry successful: {filepath}")
        except Exception as e2:
            print(f"   ❌ Retry failed: {str(e2)}")

def main():
    if not WINDMILL_BASE_URL or not WINDMILL_TOKEN:
        print("ERROR: Missing WINDMILL_BASE_URL or WINDMILL_TOKEN. Please set environment variables.")
        return

    if not os.path.isdir(PROJECT_DIR):
        print(f"ERROR: Project directory '{PROJECT_DIR}' not found.")
        return

    print(f"--- Deploying {PROJECT_DIR} to Windmill workspace: {WORKSPACE} ---")
    for root, _, files in os.walk(PROJECT_DIR):
        for file in files:
            if file.endswith((".py", ".ts", ".yml", ".yaml")):
                deploy_resource(os.path.join(root, file))
            else:
                print(f"INFO: Skipping non-deployable file: {file}")
    print("🚀 Deployment complete.")

if __name__ == "__main__":
    main()
