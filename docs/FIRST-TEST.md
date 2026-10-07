# First prop test

1. Confirm the physical pixel type, required supply voltage, connected count and data-input end. Use a suitable external pixel supply and shared ground.
2. Stop xLights/FPP and controller native tests. PixelTool cannot guarantee that another sender stays stopped.
3. Upload a supported custom .xmodel/.xml. Selection imports automatically. Check numbering and preview; checkpoints are suggestions until physically confirmed.
4. Create a named prop instance. Choose the destination, port, starting pixel and first model node. The mapping text is port,start_pixel,node,count, one segment per line.
5. Save and select/validate the mapping. Overlaps, capacity errors and unsupported controller transformations are rejected. Selecting a mapping does not start output.
6. Start with the default low brightness and an inclusive range of three known pixels. Set range values while Tools is Off, apply them, then choose Inclusive range or Apply/start output.
7. Confirm location/colour, press STOP/blackout and visually confirm darkness. Then check red/green/blue and the intended end pixel.
8. Test idle release. The default is 60 seconds, configurable 30–600. Background polling must not keep a session alive. Restart never resumes output.
9. Release PixelTool before resuming show output.

MARK compares selected positions; it does not detect inserted pixels. The ESP can receive HA-rendered uploaded models, but those models are not copied into its standalone firmware.

If nothing lights, stop and check identity, mapping, packet reception, data direction, power and ground. Don't start by increasing brightness. A larger number is not a wiring diagram.
