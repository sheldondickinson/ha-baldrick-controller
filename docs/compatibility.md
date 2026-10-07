# API and compatibility matrix

Evidence checked 06/10/2026. Status describes evidence, not a promise that all catalogue products have identical APIs.

| Model / firmware | Identity and discovery | Interfaces / commands | Telemetry | Status |
|---|---|---|---|---|
| Baldrick8 v3.8.8 | `/system_state` board_id; manual HTTP | `/settings`, `/system_state`, `/colour_orders`; Turnip test config POST with reconciliation; DDP | seconds uptime, °C processor temperature, RAM bytes, fps, active sources, packet rates, port models | Two owned boards read-tested; low-level DDP packet/counter tests; visual validation pending; native writes source-verified |
| Baldrick17 v3.8.8 + secondary v3.8.4 | Same board ID; Turnip buddies HTTP-verified before add | Same pixel interfaces; 17 ports, DDP | Dual temperature/firmware arrays, shared telemetry | Owned board read-tested; DDP packet/counter tests; visual validation pending |
| BaldrickDMX v3.8.8 | Same board ID; buddy advertisement | Common reads; UI exposes preset test interface but no unknown-load activation | Configured DMX outputs, shared 512-channel universe; source/activity/health | Owned board read-tested; no live DMX output commands |
| BaldrickSwitchy / untested firmware | Official network product; no owned response | Relay/timed functions described by vendor; adapter writes disabled | No fabricated relay or power states | Catalogue/source evidence only; not certified runtime support |
| BaldrickInput1 / untested firmware | Official network input product | Callback setup intentionally not changed | No polling claim for short presses | Catalogue evidence; no verified event adapter |
| BaldrickInput8 / untested firmware | Official network input product | Same limitations; eight inputs described | No fabricated input/event entities | Catalogue evidence only |
| BaldrickBadge | Wearable product; no independently verified network interface | No native network integration claimed | None exposed | Unsupported directly |
| BaldrickSignals | Auxiliary/status product; no verified independently addressable API | No direct integration claimed | None exposed | Unsupported directly |
| BaldrickEmbed / BaldrickScene | Additional xLights controller identifiers | Catalogue inclusion/current shipping not established | None claimed | Source identifiers only |
| PixelTool ESP32-C6 / 0.2.0 | MAC identity; `_pixeltool._tcp` via HA | `/api/receiver`; PIN-authenticated claim/renew/release; dense DDP | GPIO, capacity, colour order, cap, frame/drop counts and ownership | USB/OTA and protocol bench validation; disconnected pixel load |
| Unknown Baldrick firmware | Verified common board_id + valid common reads | Writes/DDP eligibility disabled | Only present common fields, missing values unavailable | Conservative read-only adapter |

Official catalogue: https://www.baldrickboard.com/en/boards and its individual model pages. xLights authoritative controller/output evidence: `src-core/controllers/ILightThat.cpp`, `src-core/outputs/DDPOutput.cpp`, `controllers/ilightthat.xcontroller` on the inspected default `master` branch. No Falcon endpoint is assumed.

Owned-board UI modules were captured read-only. `/js_files` identifies modules; `turnip_test/test.js` and test UI modules establish POST `/turnip_test/test_config` fields: `test_mode_active`, `test_pattern`, `test_brightness`, `test_ports`, `test_target`, and DMX presets. GET `/turnip_test_ui/patterns` establishes firmware pattern identifiers. Writes are limited to exact verified firmware/model and disabled when network test synchronisation is enabled. POST failures are not blindly retried; requested state is read back.

`throughput` is retained as a raw diagnostic because the UI's Kbps conversion does not establish whether the source quantity is bytes or bits. Packet receive/drop fields behave as rates, not cumulative lifetime counters. Missing fields are `None`, never invented zeros. Real replaceable fuses on pixel boards are not electronic-fuse controls; pixel-data blackout does not disconnect port power. Voltage/current measurements are not present in the captured API and are not exposed.

Read requests are serialised per client with a five-second timeout and 1 MiB bound. Polling defaults to 15 seconds, adjustable 10–300 seconds, with bounded failure backoff. Sanitised fixtures originate from all four owned boards; names/IDs/network secrets are replaced. Other products have no fabricated hardware fixture claims.
