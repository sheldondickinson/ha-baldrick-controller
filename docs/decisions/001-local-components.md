# ADR 001: Local monitoring and separate pixel output

Date: 06/10/2026. Status: accepted.

Use one capability-based asynchronous Turnip client shared by a HA custom integration and a Docker companion. Each independently addressable board has a config entry keyed by its verified hardware board ID. Addresses are assignments, not identity. Unknown firmware retains common read interfaces but cannot use uncertain writes.

Continuous rendering, exclusive expiring PixelTool sessions and DDP transmission belong in the companion. HA provides monitoring and an authenticated same-origin panel bridge. A stopped companion does not affect board polling. No browser UDP, cloud service, firmware flash or active xLights modification is required.

Store original private geometry, checkpoints, physical instances and progress separately in SQLite, with source hashes and append-only revision records. Versioned SQL files run identically in all environments. Checkpoints are suggestions until confirmed; manual guide ends and pusher starts remain distinct. Model node identifiers retain their imported numbering; instance UUIDs remain stable when assignments change.

Initially allow only verified custom RGB geometry and simple configured RGB output transformations. Block grouping, null pixels, reversal and ambiguous configurations until their precise firmware semantics have fixtures/tests. This trades breadth for accurate output. The renderer/output interfaces are reusable independently of HA; no XRig product is included.

Reuse the existing Docker services host and HA authentication. Secrets and actual deployment inventory remain outside distributable source. Persistent model assets are private, irrespective of source licensing.
