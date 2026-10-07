# ADR 003: ESP32-C6 portable output destination

Date: 07/10/2026. Status: accepted.

Add a versioned PixelTool ESP adapter to the companion destination layer, without treating it as a Baldrick controller or changing Baldrick monitoring. The existing PixelTool-C6 repository owns firmware, standalone GUI, GPIO, LCD and OTA behaviour. The companion owns uploaded geometry, checkpoints, assignments, rendering and session expiry. Its one-output ESP mapping uses the existing 1000-pixel firmware capacity. DDP is dense for the ESP so the receiver can prove a complete frame before commit; sparse model assignments become black gaps within that frame.

A private PIN authenticates the ESP receiver lease. The firmware restricts packets to the lease's HTTP source, limits brightness without applying a second multiplier, and stops after two seconds without complete frames. It needs a renewal within 15 seconds. This is stronger practical ownership filtering than Baldrick offers, but is not cryptographic UDP authentication. Explicit stop sends black frames and releases the remote lease. A receiver which already expired is reconciled read-only rather than blindly retried.

The ESP advertises `_pixeltool._tcp`. HA's native zeroconf receives LAN advertisements and submits the resolved private address to the companion. The companion verifies permanent MAC identity and only updates an already-paired destination's address. The PIN stays in private server configuration; address changes are recorded in the existing revision/settings tables. No new database schema is required, and credentials are not sent to browsers or included in advertisements. Unpaired devices do not gain output capability from discovery alone.

Preserve standalone C6 settings and models, boot-off behaviour, original flash partition layout and USB recovery. OTA credentials remain private and persist across reboot. Uploaded HA models are rendered centrally; they are not compiled into the portable firmware.
