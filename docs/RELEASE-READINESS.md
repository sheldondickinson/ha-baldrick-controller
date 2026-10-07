# Release readiness — 08/10/2026

## Prepared

- HACS metadata, custom repository/setup badges and fresh-install instructions.
- Companion Docker deployment, persistent storage, health checks and disarmed restart.
- Board compatibility matrix and honest limits.
- Source licences/attribution, redacted fixtures, tests and CI.
- Updates/removal, first-output guide and privacy-safe sharing materials.
- Independent, original British-style copy; clear safety/control language.
- ESP browser-flashing package prepared separately using only generated demo geometry.

## Publication gates

1. HACS does not support private repositories. The badge is prepared, but publication needs the owner's explicit approval. It is not a HACS default-list submission.
2. The existing PixelTool-C6 repository/history includes vendor geometry, generated embedded geometry, reference PDFs/screenshots and private bench identifiers. Do not make that complete history public without rights/privacy review. A clean demo export is the safer prepared distribution path.
3. The ESP feature PR is now merged into its existing default branch after CI passed. Publication still requires the asset/history decision; a private merge is not a public release.
4. HA 2026.9 isolated coordinator runtime CI now passes. Full config-flow qualification across every supported release is still broader work.
5. ESP connected-pixel, electrical signal and final LCD readability checks remain outstanding.
6. Installer hosting must use HTTPS (or localhost for preview) and publicly accessible firmware assets. A private GitHub URL or file:// page is not a working public installer.
7. No Improv Wi-Fi support is claimed. Configure Wi-Fi through the device AP/GUI or documented USB commands.
8. Generic demo firmware differs from the owner's personal compiled models. Do not replace the personal board image incidentally.

## Other gaps worth tracking

- More representative imported model fixtures, including unsupported/non-contiguous numbering.
- Runtime HA config-flow and coordinator CI at the supported version floor.
- More firmware/model combinations and actual native-control hardware checks.
- A first-time companion setup/pairing helper, rather than hand-editing private JSON.
- Container release images and a documented version matrix so HACS, companion and ESP updates stay in step.
- Existing hard-crash Baldrick frame retention; software ownership cannot lock out external DDP.
- Battery enclosure, power path and real-load validation remain a hardware project.

No public repository switch, HACS submission or public site publication has happened.

## Final candidate checks

Hassfest and the HA 2026.9 coordinator runtime job pass. The companion's 45 tests, formatting/type checks and firmware/demo-package CI pass. Known live token/PIN checks over tracked text history found no matches; that is not a substitute for the ESP asset/history review.

The demo source and installer were compiled, checksum-checked and previewed locally without connecting/flashing a board. Its source export is self-contained and strictly file-allowlisted. The personal C6 0.2.1 build passed checks but remains unflashed pending current physical-setup confirmation. The installer is not publicly hosted.

The HA/companion 0.2.1 copy update is deployed and output remains stopped/unowned. HACS validation itself remains gated while private, as required by HACS availability.
