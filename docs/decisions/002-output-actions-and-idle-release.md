# ADR 002: Output actions acquire ownership; inactivity releases it

Date: 07/10/2026. Status: accepted at the owner's request.

Replace separate browser acknowledgement/Arm steps with automatic acquisition and start on an output action. Model upload, source preview, timeout editing and mapping selection do not start output. Keep low initial brightness, capacity checks, verified firmware, stream/native-test guards, configuration reconciliation, blackout, restart disarming and a prominent Stop control.

Track actual pointer, keyboard and input activity rather than background polling. Persist a shared 30–600-second UI idle timeout, default 60, in the existing settings table without a schema change. Heartbeats report idle duration and only renew the remaining interval; idle expiry stops output and releases ownership. UI closure or loss of communication also expires the server lease. Explicit Stop releases a locally owned session immediately.

Show that PixelTool cannot be used while another device is controlling the controllers. Block conflicting software sessions and reported input streams. This does not create a network lock: external DDP senders can be undetected or start later. The interface tells the operator to stop xLights/FPP and board tests before output actions. This replaces the earlier explicit browser acknowledgement decision in ADR 001 while preserving protocol-side checks and the reusable authenticated API.
