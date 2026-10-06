"""Integer rendering port of PixelLogic.h and PusherCore.h."""

from .models import PALETTE


def pusher(model, s, node, pulse):
    if node < s.get("first", 1) or node > model["count"]:
        return (0, 0, 0)
    k = 0
    while (
        k + 1 < len(model["checkpoints"])
        and model["checkpoints"][k + 1]["node"] <= node
    ):
        k += 1
    p = model["checkpoints"][k]
    marker = p["node"] == node
    level = min(s.get("level", 12), s.get("cap", 12), 64)
    dim = max(1, level // 6)
    mode = s.get("mode", 0)

    def tint(v):
        return tuple((c * v + 127) // 255 for c in PALETTE[p["colour"]])

    if mode in (4, 5, 6):
        return tuple(level if i == mode - 4 else 0 for i in range(3))
    if mode == 1:
        return tint(level) if marker else (dim, dim, dim)
    if mode == 3 and node == s.get("node", 1) and pulse:
        return (level,) * 3
    if mode == 2 and k == s.get("run", 0):
        return (level,) * 3 if marker and pulse else tint(level)
    return tint(level if marker else dim)


def tools(count, s, n, tick):
    base = min(s.get("level", 12), s.get("cap", 12), 64)
    step = (tick // 100) % 12
    triangle = step % 6 if step < 6 else 11 - step
    pulse = base * (45 + 55 * triangle // 5) // 100
    white = (base,) * 3
    off = (0, 0, 0)
    mode = s.get("mode", 0)
    current = s.get("node", 1)
    if mode == 0:
        return off
    if mode == 1:
        per = s.get("per", 50)
        strands = s.get("strands", 1)
        tail = s.get("tail", 0)
        total = per * strands + tail
        if n in (total, total + 1):
            return (pulse, 0, 0)
        if any(
            n in (b, b + 1) for b in range(per, per * strands + 1, per) if b < total
        ):
            return (0, 0, pulse)
        if n <= per * strands:
            return white
        if n <= total:
            return (base, 0, base)
        return off
    if mode == 2:
        for end in s.get("ends", []) + [count]:
            if n == end:
                return (pulse, 0, 0)
            if n == end + 1:
                return (0, 0, pulse)
        if n == current:
            return (pulse,) * 3
        if n == current - 1:
            return (base, 0, 0)
        if n == current + 1:
            return (0, 0, base)
        return (base // 3,) * 3 if n < current else off
    if mode in (3, 4):
        if mode == 4:
            current = 1 + (tick // s.get("walk_ms", 500)) % count
        return (
            (pulse,) * 3
            if n == current
            else (base, 0, 0)
            if n == current - 1
            else (0, 0, base)
            if n == current + 1
            else off
        )
    if mode == 5:
        return white if s.get("start", 1) <= n <= s.get("finish", count) else off
    if mode in (6, 7, 8, 9):
        return (
            white
            if mode == 9
            else tuple(base if i == mode - 6 else 0 for i in range(3))
        )
    if mode == 10:
        hue = ((n - 1) * 256 // count + tick // 20) % 256
        ramp = (hue % 85) * 3
        up = ramp * base // 255
        down = (255 - ramp) * base // 255
        return ((down, up, 0), (0, down, up), (up, 0, down))[min(2, hue // 85)]
    if mode == 11:
        return white if n == tick // 35 % count + 1 else off
    if mode == 12:
        phase = tick // 25 % (count * 3)
        return (
            tuple(base if i == phase // count else 0 for i in range(3))
            if n <= phase % count + 1
            else off
        )
    return off


def frame(model, state, tick):
    return [
        pusher(model, state, n, tick % 1200 < 600)
        if state.get("tool", "pusher") == "pusher"
        else tools(model["count"], state, n, tick)
        for n in range(1, model["count"] + 1)
    ]
