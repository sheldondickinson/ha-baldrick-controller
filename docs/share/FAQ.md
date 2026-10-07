# Follow-up answers

## Is it available to download?

It is currently an early personal deployment in private repositories. Public packaging, wider hardware testing and redistribution review still need to happen before presenting it as a public release. Do not post private repository links as a working download link.

## Does it replace xLights or FPP?

It provides monitoring, prop assembly and test workflows alongside them. Stop their output before a PixelTool test, then release PixelTool before resuming show output. Existing xLights files and controller mappings remain in place.

## Can it use any controller?

The currently verified destinations are Baldrick8, Baldrick17 and the updated PixelTool ESP32-C6. BaldrickDMX monitoring is implemented. Other controller families need verified adapters; this is not universal controller support.

## Does the ESP need Home Assistant?

Its original standalone GUI and local GPIO tester remain usable independently. HA PixelTool adds a network destination: the companion renders uploaded models and sends pixel data to the ESP. The full HA model library is not copied into the ESP's standalone firmware.

## Is the portable battery tester finished?

The firmware and network receiver are deployed and bench-tested. The battery adapter, regulators and enclosure are a planned hardware build. External pixels need a suitable separate supply at their required voltage and a common data ground; the ESP/USB does not power a prop.

## Does MARK know where I've inserted a pixel?

It compares user-selected positions. It does not physically detect inserted pixels or infer verified physical turns from animation submodels.

## Which models can I upload?

Both .xmodel and .xml are accepted by content. The current parser supports contiguous, individually numbered custom RGB geometry, with a 2 MiB upload limit. Unsupported structures or numbering are rejected with an error. Selecting a file starts import automatically and shows staged progress.

## What stops output being left on?

PixelTool has a prominent Stop/blackout action, low initial brightness, ownership checks and a configurable 30–600-second UI idle release. Restart does not resume output. The ESP additionally stops/releases after two seconds without complete frames. A Baldrick can retain its last frame after a hard sender failure; don't claim an absolute blackout guarantee or a network-wide DDP lock.

## What has actually been tested?

Baldrick8/17: monitoring, DDP reception and supervised colour/range/blackout checks on the owner's loads. BaldrickDMX: read-only monitoring. ESP32-C6: verified USB update, authenticated wireless OTA, settings retention, discovery, receiver/ownership/packet-loss checks and actual HA UI streaming on a USB-only bench. Connected pixels and LCD readability on the updated ESP still await owner confirmation. The companion currently has 45 automated tests, alongside the C6 host/sanitiser and rendering parity checks.

## What about models and licensing?

Uploads stay private. Third-party model assets are not included in this sharing pack. The source retains applicable licences and attribution, including the Falcon HA reference experience and the existing PixelTool-C6 project.
