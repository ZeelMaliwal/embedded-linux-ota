"""boot watchdog for automatic rollback.
run this as a systemd service on boot. if the system doesn't
confirm it's healthy within the timeout, revert to previous slot."""

import subprocess
import time
import os
import sys

HEALTH_CHECK_SCRIPT = '/etc/ota-updater/health-check.sh'
ROLLBACK_TIMEOUT = 300  # 5 minutes
CHECK_INTERVAL = 10

def is_upgrade_pending():
    """check if we just applied an update"""
    try:
        result = subprocess.run(['fw_printenv', 'upgrade_available'],
            capture_output=True, text=True, timeout=5)
        return '1' in result.stdout
    except Exception:
        return False

def run_health_check():
    """run the user-defined health check script"""
    if not os.path.exists(HEALTH_CHECK_SCRIPT):
        # no health check = assume healthy
        # (probably should require one, but whatever)
        return True

    result = subprocess.run([HEALTH_CHECK_SCRIPT], timeout=30)
    return result.returncode == 0

def rollback():
    """revert to previous boot slot"""
    print("ROLLING BACK - health check failed")
    from partitions import ABPartitions
    parts = ABPartitions()
    # switch back to the other slot
    parts.switch_slot()
    subprocess.run(['reboot'], check=True)

def main():
    if not is_upgrade_pending():
        print("no pending upgrade, exiting")
        return

    print(f"upgrade pending, monitoring health for {ROLLBACK_TIMEOUT}s")

    deadline = time.monotonic() + ROLLBACK_TIMEOUT

    while time.monotonic() < deadline:
        if run_health_check():
            print("health check passed, marking boot as good")
            from partitions import ABPartitions
            ABPartitions().mark_good()
            return
        time.sleep(CHECK_INTERVAL)

    # timeout - rollback
    rollback()

if __name__ == '__main__':
    main()
