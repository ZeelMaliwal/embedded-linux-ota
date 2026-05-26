"""main update agent. downloads, verifies, applies updates."""

import urllib.request
import gzip
import subprocess
import os
import sys
import json
import time

from manifest import Manifest
from partitions import ABPartitions

class OTAUpdater:
    def __init__(self, config_path='/etc/ota-updater.conf'):
        self.config = self._load_config(config_path)
        self.parts = ABPartitions(self.config.get('partitions'))
        self.download_dir = self.config.get('download_dir', '/tmp/ota')

    def _load_config(self, path):
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    def check_for_update(self, server_url):
        """fetch manifest from update server"""
        manifest_url = f"{server_url}/manifest.json"
        try:
            resp = urllib.request.urlopen(manifest_url, timeout=30)
            data = json.loads(resp.read())
            return Manifest(data)
        except Exception as e:
            print(f"failed to fetch manifest: {e}")
            return None

    def download_image(self, url, dest):
        """download with progress"""
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        print(f"downloading {url}")

        resp = urllib.request.urlopen(url, timeout=300)
        total = int(resp.headers.get('content-length', 0))
        downloaded = 0

        with open(dest, 'wb') as f:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  {pct}% ({downloaded}/{total})", end='', flush=True)
        print()
        return True

    def apply_image(self, image_path, target_device, compressed=False):
        """write image to partition"""
        print(f"writing to {target_device}...")

        if compressed:
            # decompress and write
            with gzip.open(image_path, 'rb') as gz:
                with open(target_device, 'wb') as dev:
                    while True:
                        chunk = gz.read(1024 * 1024)
                        if not chunk:
                            break
                        dev.write(chunk)
        else:
            # dd-style copy
            subprocess.run(
                ['dd', f'if={image_path}', f'of={target_device}', 'bs=4M', 'conv=fsync'],
                check=True
            )
        print("write complete")

    def run_update(self, server_url):
        manifest = self.check_for_update(server_url)
        if not manifest:
            print("no update available")
            return False

        current = self.config.get('version', '0.0.0')
        device = self.config.get('device_type', '*')

        ok, msg = manifest.check_compatibility(current, device)
        if not ok:
            print(f"update not compatible: {msg}")
            return False

        print(f"update available: {current} -> {manifest.version}")

        target_dev = self.parts.inactive_device()
        if not target_dev:
            print("error: can't determine target partition")
            return False

        for image in manifest.images:
            local = os.path.join(self.download_dir, os.path.basename(image['url']))

            if not self.download_image(image['url'], local):
                return False

            if not manifest.verify_image(image, local):
                print("image verification failed, aborting")
                return False

            self.apply_image(local, target_dev, image.get('compressed', False))

        # run post-install hooks
        for cmd in manifest.post_install:
            print(f"running: {cmd}")
            subprocess.run(cmd, shell=True, check=True)

        # switch boot slot
        self.parts.switch_slot()
        print(f"update applied. reboot to activate.")
        return True

if __name__ == '__main__':
    server = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080'
    updater = OTAUpdater()
    updater.run_update(server)
