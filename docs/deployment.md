# Deployment, updates, backup and removal

## Docker companion

`deploy/compose.yaml` is the reproducible template. Set `PIXELTOOL_BIND_IP`, `PIXELTOOL_PORT`, `PIXELTOOL_DATA_DIR` and `PIXELTOOL_CONFIG_PATH` for the chosen host. The default bind is loopback; bind a reachable private address for the HA bridge. Restrict access to that interface and HA host as appropriate. Run `docker compose config --quiet`, build, then start. Non-root, read-only filesystem, dropped capabilities, resource limits, health check and `unless-stopped` are configured.

Create the private mounted JSON outside Git:

```json
{"token":"GENERATE_A_LONG_RANDOM_SECRET","source_ip":"COMPANION_PRIVATE_IP","boards":[{"id":"VERIFIED_12_HEX_BOARD_ID","host":"BOARD_HOSTNAME"}]}
```

Keep it readable by container UID 65534, never copy it into the image or web assets. Include independently verified boards; DMX may be registered for identification but is excluded from pixel targets. API requests require its bearer token. `/health` reveals only health/version/armed state.

## HA bridge

Create `baldrick_pixeltool.json` in the HA configuration directory, outside source:

```json
{"url":"http://COMPANION_PRIVATE_IP:18099","token":"SAME_SECRET"}
```

HA serves the panel shell and makes authenticated companion calls internally. The browser uses the HA origin, including its existing HTTPS proxy and authentication. Restart after installing/replacing Python integration files, following `ha core check`. Reloading entries alone does not reliably reload imported Python modules. If deployment preserves timestamps and file sizes, rebuild bytecode with `python -m compileall -f` inside the HA container before restarting; verify the installed source/loaded version.

## Updates and backups

Stop/release PixelTool first. Back up the integration directory, private configuration and SQLite database using SQLite's online backup API (or stop the companion before copying the database together with WAL files). Keep backup permissions private. Rebuild the generated frontend, run checks, rebuild the container, restart it and confirm health/disarmed state plus persisted models. Back up existing HA dashboard/resource configuration before intentional dashboard edits. Validate HA configuration before restart, then compare device/entity IDs and inspect logs.

Restore the prior integration/container and database backup if needed. Do not downgrade a database across unsupported migrations. Version 1 schema migrations are idempotent and non-destructive.

## Removal

Stop/release output. Remove Baldrick config entries and the dedicated dashboard through HA, remove its resource and PixelTool panel/integration files, check configuration and restart. Stop/remove the companion container. Retain `/data` and secret files until their removal is explicitly intended; deleting models/backups is a separate deliberate action. Existing standalone PixelTool-C6, board firmware and xLights files are unaffected.

When packaging on macOS, use `COPYFILE_DISABLE=1 tar --no-xattrs` so AppleDouble metadata is not included as Python or SQL input. The Docker context excludes `._*` metadata files.

## Portable PixelTool ESP destination

Firmware 0.2.0 in the existing private PixelTool-C6 repository adds the verified receiver. Retrieve its private access file over owner-controlled USB once, retain it outside Git, and register `{ "id": "VERIFIED_MAC_WITHOUT_COLONS", "host": "ESP_PRIVATE_IP", "kind": "esp", "pin": "PRIVATE_ACCESS_PIN" }` in the companion's private board list. Restart the disarmed companion. HA's `_pixeltool._tcp` zeroconf flow verifies and updates an already-paired destination's private address. Baldrick monitoring entries remain separate. The browser sees capacity and identity, never the PIN. The existing ESP GUI and recovery AP continue to work without HA.
