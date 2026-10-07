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

1. The HA repository is public with owner approval. HACS custom-repository validation and hassfest pass. This is not a HACS default-list submission.
2. The existing PixelTool-C6 repository/history includes vendor geometry, generated embedded geometry, reference PDFs/screenshots and private bench identifiers. Do not make that complete history public without rights/privacy review. A clean demo export is the safer prepared distribution path.
3. The ESP feature PR is merged privately after CI passed. Only the clean demo source and firmware are distributed publicly.
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

The HA repository and HTTPS project/ESP installer site were published on 08/10/2026. No HACS default-list submission or Facebook posting has happened.

## Final candidate checks

Hassfest and the HA 2026.9 coordinator runtime job pass. The companion's 45 tests, formatting/type checks and firmware/demo-package CI pass. Known live token/PIN checks over tracked text history found no matches; that is not a substitute for the ESP asset/history review.

The demo source and installer were compiled, checksum-checked and previewed locally without connecting/flashing a board. Its source export is self-contained and strictly file-allowlisted. The personal C6 0.2.1 build passed checks but remains unflashed pending current physical-setup confirmation. The installer is publicly hosted at https://sheldondickinson.github.io/ha-baldrick-controller/esp/.

The HA/companion 0.2.1 copy update is deployed and output remains stopped/unowned. Public HACS custom-repository validation passes.
