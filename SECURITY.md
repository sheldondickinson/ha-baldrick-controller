# Security and private data

Use this beta on a trusted local network. Keep the companion API and ESP off the public internet. HA access uses the existing authenticated administrator session.

Never post tokens, access PINs, Wi-Fi passwords, full flash backups, private inventories or uploaded model assets in public issues. Diagnostics are redacted, but review attachments before sharing. Report a suspected secret exposure privately to the repository owner; do not include the secret itself.

The ESP GUI's optional PIN and its always-protected receiver/OTA access are different controls. Firmware backups contain saved credentials. Store them outside Git with owner-only permissions.

Output ownership excludes competing PixelTool sessions. Baldrick cannot enforce a network-wide DDP lock. ESP sender filtering is a practical LAN restriction, not cryptographic UDP authentication. Keep xLights/FPP stopped during tests.
