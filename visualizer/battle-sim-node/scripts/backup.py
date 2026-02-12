#!/usr/bin/env python3
import os
import tarfile
import json
import argparse
from datetime import datetime

def create_backup(version, description):
    backup_dir = "backups"
    manifest_path = os.path.join(backup_dir, "manifest.json")
    filename = f"darwins-island-v{version}.tar.gz"
    filepath = os.path.join(backup_dir, filename)

    # 1. Define Exclusions
    exclude_list = [
        "node_modules", ".git", "dist", "backups", "tmp", 
        "test-results", "playwright-report", ".next", "out"
    ]

    def filter_func(tarinfo):
        for ex in exclude_list:
            if tarinfo.name == ex or tarinfo.name.startswith(ex + "/"):
                return None
        # Ensure run.sh and scripts are executable in the archive
        if tarinfo.name.endswith(".sh") or tarinfo.name.startswith("scripts/"):
            tarinfo.mode = 0o755
        return tarinfo

    print(f"Creating backup: {filename}...")
    
    # 2. Create the Tarball
    with tarfile.open(filepath, "w:gz") as tar:
        # We add each item in the current directory individually to avoid a top-level folder
        for item in os.listdir("."):
            if item in exclude_list:
                continue
            tar.add(item, filter=filter_func)

    # 3. Update Manifest
    manifest = {"backups": []}
    if os.path.exists(manifest_path):
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

    new_entry = {
        "version": version,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "filename": filename,
        "description": description,
        "activeFeatures": [] # To be filled manually or by discovery
    }
    
    # Check if version exists, update it, otherwise append
    updated = False
    for i, entry in enumerate(manifest["backups"]):
        if entry["version"] == version:
            manifest["backups"][i] = new_entry
            updated = True
            break
    
    if not updated:
        manifest["backups"].append(new_entry)

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Success! Backup saved to {filepath}")
    print(f"Manifest updated at {manifest_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Darwin's Island Backup Utility")
    parser.add_argument("version", help="Version number (e.g., 0.02)")
    parser.add_argument("--desc", help="Description of the backup", default="Manual backup.")
    
    args = parser.parse_args()
    create_backup(args.version, args.desc)
