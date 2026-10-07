# Installation: a modestly cunning plan

## Choose what you need

Monitoring only: install the HA integration and add controllers. PixelTool testing: also run the Docker companion. Portable ESP: flash the supported C6 board, then pair it as a companion destination. Monitoring remains useful without either PixelTool component.

## 1. Install the Home Assistant integration

The HACS badge in the README opens this public custom repository on your own HA instance. HACS must already be installed. It does not install Docker or ESP firmware. Private repositories cannot be downloaded through HACS.

HACS → three-dot menu → Custom repositories → enter the repository URL → category Integration → add/download Baldrick Controller → check HA configuration → restart HA. Then Settings → Devices & services → Add integration → Baldrick Controller, or use the setup badge.

For manual installation: clone this repository, copy only custom_components/baldrick_controller into your HA config/custom_components directory, check configuration and restart. Do not copy private credentials or model storage into the integration directory.

Enter each controller's verified hostname/IP. One entry represents one independently addressable controller. Reconfigure an address through the entry's menu; don't remove/re-add it to change IP. Set a conservative polling interval through entry options.

## 2. Add the dashboard

Create a new dashboard, open its raw configuration and set:

    strategy:
      type: custom:baldrick-controller

Do not replace an existing dashboard. The strategy builds views from registered controllers. YAML-resource users must register the versioned module URL described in the README; storage-mode resources register automatically.

## 3. Run the PixelTool companion

Clone the same repository on a Linux Docker host reachable from HA and the controllers. Copy deploy/compose.yaml into a deployment folder, keeping its build context pointed at the checked-out repository.

Prepare a persistent data directory writable by container UID/GID 65534. Prepare a private configuration JSON with a long random token and verified board identities:

    {"token":"LONG_RANDOM_SECRET","source_ip":"DOCKER_HOST_LAN_IP","boards":[
      {"id":"VERIFIED_12_HEX_BOARD_ID","host":"CONTROLLER_HOST"}
    ]}

The board ID comes from the controller's read-only /system_state endpoint. Keep the configuration outside Git and readable by container UID 65534. Do not put it in the web directory. source_ip is the LAN source address controllers actually see from the Docker host; it helps detect competing senders.

Set PIXELTOOL_BIND_IP, PIXELTOOL_PORT, PIXELTOOL_DATA_DIR and PIXELTOOL_CONFIG_PATH through a private .env file. The bind must be reachable from HA; the template defaults to loopback. Restrict the companion API to the trusted LAN/HA host, not the internet.

Run docker compose config --quiet, docker compose build, then docker compose up -d. Check /health and confirm output is stopped after every restart. Keep the private token out of command arguments and logs.

## 4. Connect HA to the companion

Create baldrick_pixeltool.json in the HA configuration directory:

    {"url":"http://DOCKER_HOST_LAN_IP:18099","token":"SAME_PRIVATE_TOKEN"}

Restrict its permissions, check HA configuration, then restart. PixelTool appears in the HA sidebar for administrators. Use your normal HA HTTPS address; HA proxies requests internally, so there is no second browser token or HTTP iframe to configure.

## 5. Pair the optional ESP

Follow PixelTool-C6's browser/USB flashing and setup guide. Retrieve its private access file over owner-controlled USB using scripts/device.py ACCESS; do not paste the PIN into an issue.

Add a private board-list entry:

    {"id":"VERIFIED_MAC_WITHOUT_COLONS","host":"ESP_PRIVATE_IP",
     "kind":"esp","name":"Portable PixelTool","pin":"PRIVATE_ACCESS_PIN"}

Restart the disarmed companion. HA discovers the ESP's _pixeltool._tcp advertisement and verifies the identity before updating an already-paired address. Discovery does not bypass pairing or grant output rights to an unknown device.

## Before the first output

Follow FIRST-TEST.md. A controller's configured capacity is not evidence of the connected pixel load. Pixels are clever enough to light up; they are not clever enough to tell us what you plugged in.

## Updates, backups and removal

See deployment.md. HACS updates the integration only. Rebuild the companion for companion releases; ESP firmware updates are separate. Preserve the SQLite library and secret files. Never let a restart automatically resume output.
