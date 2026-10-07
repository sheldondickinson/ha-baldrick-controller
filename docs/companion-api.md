# Companion API

All operations use `POST /api` with `Authorization: Bearer <private token>` and JSON `{ "op": "operation", "data": {}, "session": "lease token when required" }`. HA exposes this only through authenticated administrator POST `/api/baldrick_controller/pixeltool`; browser bundles never receive the bearer credential.

Read operations: `status`, `boards`, `library`. `claim` returns a random lease token; `heartbeat`, `release`, `select`, `state`, `arm`, `native_test`, uploads and edits require ownership. `stop` is available to an authenticated caller even without that lease for emergency disarming. Invalid requests return HTTP 400 with useful errors; unauthenticated requests return 401. The HA proxy reports companion unavailability separately. There are no automatic retries of output commands.

`upload`: base64 XML, maximum decoded 2 MiB. `model_save`: ID, optional title/checkpoints. Checkpoints specify integer `node`, palette `colour` 0–6, label and explicit `confirmed`. `instance_save`: stable ID when updating, model ID, board ID, first model node, mapping segments `{port,start_pixel,node,count}` and saved progress. `remove`: kind and ID; referenced models cannot be removed. The library preserves source XML/hash and versioned revisions separately from output assignments.

`select` validates and snapshots an instance; `state` validates workflow/mode, integer channel level/cap, finder/range/cutter/guide values and checkpoints. `preview` returns rendered colours without sending packets. `mark` returns selected/expected/difference, with no physical detection. `arm` and `native_test` require `external_output_stopped: true`; the UI supplies this on a user-requested output action after showing the takeover requirement; it is not a lock against xLights/FPP.

This API and the independent rendering/mapping/output modules can be reused by a future local application. Session capabilities and controller evidence must remain enforced by any future client.

`preferences_save`: owned operation with integer `idle_timeout` (30–600 seconds), persisted in the existing settings table. Status includes `idle_timeout`. `heartbeat` accepts elapsed `idle_seconds`; the server renews only the remaining idle interval, and stops/releases when that interval is exhausted. Browser test actions acquire/select/update/start automatically; there is no separate UI checkbox or Arm button.
