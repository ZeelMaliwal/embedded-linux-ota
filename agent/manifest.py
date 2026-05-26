"""parse and validate OTA update manifests."""

import json
import hashlib
import os

class Manifest:
    def __init__(self, data):
        self.version = data['version']
        self.device_type = data.get('device_type', '*')
        self.images = data.get('images', [])
        self.pre_install = data.get('pre_install', [])
        self.post_install = data.get('post_install', [])
        self.min_version = data.get('min_version')
        self.rollback_timeout = data.get('rollback_timeout', 300)

    @classmethod
    def from_file(cls, path):
        with open(path) as f:
            return cls(json.load(f))

    def verify_image(self, image_entry, local_path):
        """check sha256 of downloaded image"""
        expected = image_entry.get('sha256')
        if not expected:
            return True  # no hash specified, skip (bad practice tho)

        h = hashlib.sha256()
        with open(local_path, 'rb') as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                h.update(chunk)
        actual = h.hexdigest()
        if actual != expected:
            print(f"hash mismatch: expected {expected}, got {actual}")
            return False
        return True

    def check_compatibility(self, current_version, device_type):
        if self.device_type != '*' and self.device_type != device_type:
            return False, f"wrong device type: {self.device_type} vs {device_type}"
        if self.min_version and current_version < self.min_version:
            return False, f"current version {current_version} too old, need >= {self.min_version}"
        return True, "ok"

# example manifest:
# {
#   "version": "2.1.0",
#   "device_type": "gateway-v2",
#   "min_version": "1.5.0",
#   "rollback_timeout": 300,
#   "images": [
#     {"name": "rootfs", "url": "https://updates.example.com/rootfs-2.1.0.img.gz",
#      "sha256": "abc123...", "partition": "rootfs_b", "compressed": true}
#   ],
#   "pre_install": ["systemctl stop myapp"],
#   "post_install": ["fw_setenv boot_part b"]
# }
