# Baldrick Controller and PixelTool

[![Open Baldrick Controller in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sheldondickinson&repository=ha-baldrick-controller&category=integration)
[![Set up Baldrick Controller](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=baldrick_controller)

*A modest plan for persuading pixels to behave. Tea is optional.*

**Community beta:** independent of I Light That, Baldrick, xLights and Home Assistant. The repository is currently private. HACS only supports public repositories, so the HACS badge is prepared for publication; it is not a working public download yet.

Start with [installation](docs/INSTALL.md), [first prop test](docs/FIRST-TEST.md), [updates/removal](docs/deployment.md) and [release readiness](docs/RELEASE-READINESS.md).

Local Home Assistant monitoring plus a separate Docker PixelTool rendering/output service. Integration domain: `baldrick_controller`. Version 0.2.1 beta. Runtime-tested against Home Assistant 2026.10.0b0. The declared HACS minimum is 2026.9; that minimum still needs its own runtime qualification.

## What works

UI setup, verified board IDs, duplicate prevention, address reconfiguration, shared asynchronous polling, offline/recovery, last contact, temperatures, uptime, firmware, reported warnings, traffic/activity and configured ports. A native-card dashboard builds its views from registered devices. Monitoring does not depend on PixelTool.

PixelTool provides a private uploadable custom `.xmodel`/`.xml` library, saved physical instances and mapping, checkpoint editing/provenance, persistent progress, colour runs, white plus markers, focus, locate, checkpoint navigation, MARK comparisons, front/rear maps, fit/zoom/numbering and first-node offsets. Tools include strand cutting, finder, automatic walk, inclusive ranges, solid colours, rainbow, scan, RGB wipe and manual guide section ends. Rendering and DDP run on the server at 20 fps.

Read [compatibility and API evidence](docs/compatibility.md), [architecture](docs/decisions/001-local-components.md), [output and mapping](docs/output.md), [companion API](docs/companion-api.md), [deployment](docs/deployment.md), [validation](docs/validation.md) and [attribution](NOTICE.md). Unsupported firmware writes and ambiguous mappings fail closed. Native pixel tests are limited to identified first-50-pixel loads and five seconds. DMX channel sweeps, relay switching and callback changes are not implemented.

## Home Assistant

Copy `custom_components/baldrick_controller` into the HA configuration directory, check configuration and restart. Add **Baldrick Controller** in Settings → Devices & services, entering each board hostname/IP. Independently verified Turnip buddy advertisements offer additional boards for confirmation; Baldrick discovery uses verified Turnip buddy advertisements; paired PixelTool ESP discovery uses its separate mDNS service.

Create a dedicated dashboard with:

```yaml
strategy:
  type: custom:baldrick-controller
```

The integration registers `/baldrick_controller_static/baldrick-controller-strategy.js?v=0.2.0` as a module resource. In YAML resource mode add that URL yourself. Existing dashboards are preserved. New registered boards appear when the dashboard is refreshed.

PixelTool is a same-origin HA custom panel at `/pixeltool`, available to HA administrators. Its shell contains no credentials or model data. Authenticated HA API requests are proxied server-side to the companion; this works through the existing HA HTTPS entry point without mixed-content requests or a second login. Configure the private bridge file as documented below.

## Development

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt pytest pytest-asyncio ruff mypy
python3 scripts/build_frontend.py
.venv/bin/ruff format --check custom_components pixeltool tests scripts
.venv/bin/ruff check custom_components pixeltool tests scripts
.venv/bin/mypy pixeltool custom_components
.venv/bin/pytest -q
```

`scripts/verify_installed_ha.py` additionally verifies coordinator recovery inside an installed HA container using isolated scratch state and a synthetic client; it does not connect to production storage.

Node.js and a C++ compiler are required for cross-language rendering parity tests. Edit `pixeltool/static/` source templates, then build the HA shell. Do not edit generated shell copies or the standalone ESP32 project. CI uses the same SQL migrations and validation rules. HA-dependent flows are additionally verified on the deployed HA instance; local mypy does not replace HA runtime verification.

HACS custom-repository packaging is included (`hacs.json`, manifest, translations). This repository remains private; it has not been submitted to HACS or published publicly.

Output actions automatically acquire ownership and start the selected test. Stop xLights/FPP and board tests first. The configurable UI idle timeout (30–600 seconds, default 60) stops and releases output; passive status polling does not keep a session alive. Uploads, previews and mapping selection do not start output.

Selecting a `.xmodel` or `.xml` file automatically uploads and saves it. Feedback shows file-reading percentage, an indeterminate upload/validation stage through the HA bridge, preview loading and completion. Import failures retain a useful error and re-enable the picker, including retrying the same file. Importing never starts pixel output.

PixelTool-C6 firmware 0.2.0 is also a portable destination: one GPIO output, maximum 1000 pixels, a private receiver lease and HA zeroconf discovery for an already-paired device. Its standalone GUI remains independent. See the [ESP destination decision](docs/decisions/003-esp-destination.md).
