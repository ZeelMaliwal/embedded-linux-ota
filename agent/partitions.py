"""A/B partition management. figures out which slot is active,
which is inactive, and handles switching."""

import subprocess
import os

class ABPartitions:
    def __init__(self, config=None):
        # default partition layout - override via config
        self.layout = config or {
            'rootfs_a': '/dev/mmcblk0p2',
            'rootfs_b': '/dev/mmcblk0p3',
            'boot_env': '/dev/mmcblk0p1',
        }
        self._active = None

    def active_slot(self):
        """determine which slot we booted from"""
        if self._active:
            return self._active

        # try reading from u-boot env
        try:
            result = subprocess.run(['fw_printenv', 'boot_part'],
                capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                val = result.stdout.strip().split('=')[-1]
                self._active = val
                return val
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # fallback: check which partition is mounted as /
        try:
            with open('/proc/mounts') as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == '/':
                        dev = parts[0]
                        if dev == self.layout['rootfs_a']:
                            self._active = 'a'
                        elif dev == self.layout['rootfs_b']:
                            self._active = 'b'
                        return self._active
        except Exception:
            pass

        return None

    def inactive_slot(self):
        active = self.active_slot()
        if active == 'a':
            return 'b'
        elif active == 'b':
            return 'a'
        return None

    def inactive_device(self):
        slot = self.inactive_slot()
        if slot:
            return self.layout.get(f'rootfs_{slot}')
        return None

    def switch_slot(self):
        """update bootloader to boot from the other slot"""
        target = self.inactive_slot()
        if not target:
            raise RuntimeError("can't determine inactive slot")

        subprocess.run(['fw_setenv', 'boot_part', target], check=True)
        # set boot counter for rollback detection
        subprocess.run(['fw_setenv', 'boot_count', '0'], check=True)
        subprocess.run(['fw_setenv', 'boot_limit', '3'], check=True)
        print(f"switched to slot {target}, will take effect on reboot")

    def mark_good(self):
        """mark current boot as successful (disables rollback)"""
        subprocess.run(['fw_setenv', 'boot_count', ''], check=True)
        subprocess.run(['fw_setenv', 'upgrade_available', '0'], check=True)
        print("current slot marked as good")
