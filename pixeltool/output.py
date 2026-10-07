"""DDP display packets and verified configured RGB channel mapping."""

import struct


def packets(data, offset=0, sequence=1, max_payload=1440):
    if (
        not data
        or offset < 0
        or offset + len(data) > 2**32
        or not 1 <= sequence <= 15
        or not 1 <= max_payload <= 1440
    ):
        raise ValueError("Invalid DDP frame")
    for i in range(0, len(data), max_payload):
        body = data[i : i + max_payload]
        last = i + len(body) == len(data)
        yield struct.pack(
            "!BBBBIH", 0x41 if last else 0x40, sequence, 0, 1, offset + i, len(body)
        ) + bytes(body)
        sequence = sequence % 15 + 1


def configured_outputs(board):
    if not board.pixel_output:
        raise ValueError("Pixel output not verified for this model/firmware")
    settings = board.settings
    if settings.get("fixed_universes_per_port"):
        raise ValueError("Fixed universe layout needs verification")
    offset = 0
    outputs = []
    for i, port in enumerate(settings["ports"]):
        models = port.get("models", [])
        if port["port_type"] != "pixel":
            raise ValueError("Mixed output layouts not yet verified")
        size = sum(m["num_channels"] for m in models)
        expected = 0
        for m in models:
            if m.get("start_channel") != expected:
                raise ValueError("Non-contiguous model channel layout")
            if (
                m["colour_order"] not in ("RGB", "RBG", "GRB", "GBR", "BRG", "BGR")
                or m["num_channels"] % 3
            ):
                raise ValueError("Only configured RGB outputs supported")
            if any(
                m.get(k) not in (None, 0, False)
                for k in (
                    "null_pixels",
                    "group_count",
                    "grouping",
                    "reverse",
                    "direction",
                )
            ):
                raise ValueError("Unverified controller transformation")
            expected += m["num_channels"]
        if size > (3000 if board.model == "PixelTool ESP32-C6" else 2250):
            raise ValueError("Port exceeds source-verified 2250 channel capacity")
        outputs.append(
            {"port": i + 1, "pixels": size // 3, "offset": offset, "models": models}
        )
        offset += size
    return outputs


def mapping(board, instance, model, others=()):
    outputs = configured_outputs(board)
    used = set()
    logical = set()
    result = []
    first = instance.get("first", 1)
    if type(first) is not int or not 1 <= first <= model["count"]:
        raise ValueError("Invalid first model node")
    for segment in instance.get("segments", []):
        port, start, node, count = (
            segment.get(k) for k in ("port", "start_pixel", "node", "count")
        )
        if (
            any(type(x) is not int for x in (port, start, node, count))
            or not 1 <= port <= len(outputs)
            or start < 1
            or count < 1
        ):
            raise ValueError("Invalid mapping segment")
        out = outputs[port - 1]
        if (
            start + count - 1 > out["pixels"]
            or node < first
            or node + count - 1 > model["count"]
        ):
            raise ValueError("Mapping exceeds configured output or model capacity")
        for j in range(count):
            ch = out["offset"] + (start + j - 1) * 3
            if ch in used or node + j in logical:
                raise ValueError("Overlapping segment")
            used.add(ch)
            logical.add(node + j)
            result.append((node + j, ch))
    if not result:
        raise ValueError("Map at least one configured output")
    for other in others:
        if other["id"] == instance["id"] or other.get("board_id") != instance.get(
            "board_id"
        ):
            continue
        for segment in other.get("segments", []):
            out = outputs[segment["port"] - 1]
            start = out["offset"] + (segment["start_pixel"] - 1) * 3
            if any(start <= ch < start + segment["count"] * 3 for ch in used):
                raise ValueError("Overlaps another saved instance")
    return result


def mapped_chunks(colours, translation):
    # Sparse chunks only touch owned nodes. Controller performs colour order/brightness once.
    ordered = sorted((ch, bytes(colours[node - 1])) for node, ch in translation)
    chunks = []
    start = None
    buf = bytearray()
    for ch, rgb in ordered:
        if start is None:
            start = ch
        if ch != start + len(buf):
            chunks.append((start, bytes(buf)))
            start = ch
            buf = bytearray()
        buf.extend(rgb)
    if buf:
        chunks.append((start, bytes(buf)))
    return chunks
