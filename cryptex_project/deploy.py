# File: deploy.py
# --- FINAL CORRECTED VERSION v13 ---
# This version fixes the critical SyntaxError and all previous bugs.
# It is simplified to ONLY deploy the cryptex_project.

import os
import requests
import json
import yaml

# --- CONFIGURATION: Please confirm these are 100% correct ---
WINDMILL_BASE_URL = "http://5.78.138.105:8088"
WINDMILL_TOKEN = "8fzLR4Rkkh2CMpDhOOaJSrmBr62TTToj"
WORKSPACE = "cryptex_ai_omega"
PROJECT_DIR = "cryptex_project"
# -------------------------------------------------------------

HEADERS = {"Authorization": f"Bearer {WINDMILL_TOKEN}", "Content-Type": "application/json"}

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
        payload = {"path": path_in_windmill, "content": content, "language": language, "summary": f"Script at {path_in_windmill}"}

    elif filepath.endswith((".yml", ".yaml")):
        item_type = "flow"
        api_path_create = f"/api/w/{WORKSPACE}/flows/create"
        api_path_update = f"/api/w/{WORKSPACE}/flows/update"
        with open(filepath, "r", encoding='utf-8') as f:
            content_yaml = yaml.safe_load(f)
        flow_path = os.path.splitext(os.path.relpath(filepath, PROJECT_DIR))[0].replace(os.path.sep, "/")
        payload = {"path": flow_path, "summary": content_yaml.get("summary", ""), "value": content_yaml}

    if not payload:
        return

    create_url = f"{WINDMILL_BASE_URL}{api_path_create}"
    update_url = f"{WINDMILL_BASE_URL}{api_path_update}"

    try:
        response = requests.post(create_url, headers=HEADERS, json=payload, timeout=30)
        if response.status_code == 409:
            print(f"INFO: {item_type.capitalize()} '{path_in_windmill}' exists. Updating...")
            response = requests.post(update_url, headers=HEADERS, json=payload, timeout=30)

        response.raise_for_status()
        print(f"✅ Successfully deployed {item_type.upper()}: {filepath}")

    except requests.exceptions.RequestException as e:
        # BUG FIX: Correctly formatted the f-string that caused the SyntaxError.
        print(f"❌ FAILED to deploy {item_type.upper()}: {filepath}")
        error_text = e.response.text if hasattr(e, 'response') and e.response else str(e)
        print(f"   Error: {error_text}")


def main():
    """Main function to find and deploy all project files."""
    if not os.path.isdir(PROJECT_DIR):
        print(f"ERROR: Project directory '{PROJECT_DIR}' not found.")
        return

    print(f"\n--- Deploying {PROJECT_DIR} to workspace: {WORKSPACE} ---")
    for root, _, files in os.walk(PROJECT_DIR):
        for file in files:
            if file.endswith((".py", ".ts", ".yml", ".yaml")):
                deploy_resource(os.path.join(root, file))
            else:
                print(f"INFO: Skipping non-deployable file: {file}")

    print("\n🚀 Deployment complete!")


if __name__ == "__main__":
    if "YOUR_VPS_IP_ADDRESS" in WINDMILL_BASE_URL or "YOUR_WINDMILL_AUTH_TOKEN" in WINDMILL_TOKEN:
        print("ERROR: Please edit the deploy.py script and fill in your variables.")
    else:
        main()