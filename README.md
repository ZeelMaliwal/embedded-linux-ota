# OTA Updater

Reliable A/B partition-based OTA update system for embedded Linux devices.

Designed for Ubuntu Core and Yocto-based systems to support safe, unattended firmware updates with automatic rollback protection.

---

## Features

- A/B root filesystem updates
- Automatic rollback on boot failure
- Ed25519 firmware signature verification
- Delta updates for bandwidth optimization
- Update manifest with compatibility checks
- REST API support for fleet management
- Bootloader environment switching

---

## Architecture

```text
Update Server
    |
    |--> manifest.json
    |--> firmware.img.gz
    |
OTA Agent (Device)
    |
    |--> Verify Signature
    |--> Write to Inactive Partition
    |--> Update Boot Slot
    |--> Reboot
    |
Health Check
    |
    |--> Mark Good
    |--> OR Rollback
```

---

## Update Workflow

1. Device checks update server for new firmware
2. Firmware image and manifest are downloaded
3. Signature and compatibility are verified
4. Firmware is written to inactive partition
5. Bootloader switches active slot
6. Device reboots into updated firmware
7. Health check validates successful boot
8. System either confirms update or rolls back automatically

---

## Technologies

- Python
- Embedded Linux
- U-Boot
- Yocto / Ubuntu Core
- Ed25519 Cryptography
- REST API

---

## Use Cases

- IoT Gateways
- Industrial Linux Devices
- Robotics Platforms
- Edge Computing Systems
- Remote Embedded Deployments

---

## Future Improvements

- HTTPS/TLS support
- Differential binary patching
- Web dashboard
- Device authentication
- Update scheduling
- Multi-device fleet orchestration
```