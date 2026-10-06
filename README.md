# Baldrick Controller and PixelTool

Local Home Assistant monitoring plus a separate Docker PixelTool rendering/output service. Integration domain: `baldrick_controller`. Initial release 0.1.1. Tested against Home Assistant 2026.10.0b0; HACS minimum 2026.9.

## What works

UI setup, verified board IDs, duplicate prevention, address reconfiguration, shared asynchronous polling, offline/recovery, last contact, temperatures, uptime, firmware, reported warnings, traffic/activity and configured ports. A native-card dashboard builds its views from registered devices. Monitoring does not depend on PixelTool.

PixelTool provides a private uploadable custom `.xmodel` library, saved physical instances and mapping, checkpoint editing/provenance, persistent progress, colour runs, white plus markers, focus, locate, checkpoint navigation, MARK comparisons, front/rear maps, fit/zoom/numbering and first-node offsets. Tools include strand cutting, finder, automatic walk, inclusive ranges, solid colours, rainbow, scan, RGB wipe and manual guide section ends. Rendering and DDP run on the server at 20 fps.

Read [compatibility and API evidence](docs/compatibility.md), [architecture](docs/decisions/001-local-components.md), [output and mapping](docs/output.md), [companion API](docs/companion-api.md), [deployment](docs/deployment.md), [validation](docs/validation.md) and [attribution](NOTICE.md). Unsupported firmware writes and ambiguous mappings fail closed. Native pixel tests are limited to identified first-50-pixel loads and five seconds. DMX channel sweeps, relay switching and callback changes are not implemented.

## Home Assistant

Copy `custom_components/baldrick_controller` into the HA configuration directory, check configuration and restart. Add **Baldrick Controller** in Settings → Devices & services, entering each board hostname/IP. Independently verified Turnip buddy advertisements offer additional boards for confirmation; no unverified mDNS or subnet scan claim is made.

Create a dedicated dashboard with:

```yaml
strategy:
  type: custom:baldrick-controller
```

The integration registers `/baldrick_controller_static/baldrick-controller-strategy.js?v=0.1.1` as a module resource. In YAML resource mode add that URL yourself. Existing dashboards are preserved. New registered boards appear when the dashboard is refreshed.

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

Node.js and a C++ compiler are required for cross-language rendering parity tests. Edit `pixeltool/static/` source templates, then build the HA shell. Do not edit generated shell copies or the standalone ESP32 project. CI uses the same SQL migrations and validation rules. HA-dependent flows are additionally verified on the deployed HA instance; local mypy does not replace HA runtime verification.

HACS custom-repository packaging is included (`hacs.json`, manifest, translations). This repository remains private; it has not been submitted to HACS or published publicly.
