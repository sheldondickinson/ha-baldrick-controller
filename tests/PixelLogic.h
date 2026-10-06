#pragma once
#include <ctype.h>
#include <stddef.h>
#include <stdint.h>
#include <stdlib.h>

namespace pixeltool {
constexpr int MAX_PIXELS = 1000;
constexpr int MAX_BOUNDARIES = 96;
struct RGB {
  uint8_t r, g, b;
};
struct Model {
  int count = 500;
  int ends[MAX_BOUNDARIES] = {};
  int used = 0;
};
inline int clamp(int v, int lo, int hi) {
  return v < lo ? lo : (v > hi ? hi : v);
}

// Expected section ends, 1-based and strictly increasing; the final total is
// implicit.
inline bool parseEnds(const char *src, Model &out, int count) {
  if (count < 1 || count > MAX_PIXELS)
    return false;
  Model next;
  next.count = count;
  const char *p = src;
  while (*p) {
    while (*p && (isspace((unsigned char)*p) || *p == ',' || *p == ';'))
      ++p;
    if (!*p)
      break;
    if (!isdigit((unsigned char)*p) || next.used >= MAX_BOUNDARIES)
      return false;
    char *end;
    const long value = strtol(p, &end, 10);
    if (end == p || value < 1 || value >= count ||
        (next.used && value <= next.ends[next.used - 1]))
      return false;
    next.ends[next.used++] = (int)value;
    p = end;
    if (*p && !isspace((unsigned char)*p) && *p != ',' && *p != ';')
      return false;
  }
  out = next;
  return true;
}
inline int cutTotal(int per, int strands, int tail) {
  if (per < 1 || strands < 1 || tail < 0)
    return -1;
  const int64_t total = (int64_t)per * strands + tail;
  return total <= MAX_PIXELS ? (int)total : -1;
}
inline int expected(const Model &m, int transition) {
  if (transition < 0 || transition >= m.used)
    return m.count;
  return m.ends[transition];
}
inline int markDifference(const Model &m, int section, int position) {
  return position - expected(m, section);
}
inline RGB rainbow(uint8_t hue, uint8_t cap) {
  const int region = hue / 85;
  const int ramp = (hue % 85) * 3;
  const uint8_t up = ramp * cap / 255;
  const uint8_t down = (255 - ramp) * cap / 255;
  if (region == 0)
    return {down, up, 0};
  if (region == 1)
    return {0, down, up};
  return {up, 0, down};
}
inline RGB colour(int index, int mode, int current, int start, int finish,
                  int per, int strands, int tail, const Model &model,
                  uint8_t base, uint8_t pulse, unsigned long tick) {
  const int n = index + 1;
  const RGB off = {0, 0, 0}, white = {base, base, base};
  if (index < 0 || index >= MAX_PIXELS || model.count < 1 ||
      model.count > MAX_PIXELS)
    return off;
  switch (mode) {
  case 0:
    return off;
  case 1: { // Strand cutter: preserve the existing blue virtual / red physical
            // cut pairs.
    const int total = cutTotal(per, strands, tail);
    if (total < 0)
      return off;
    if (n == total || n == total + 1)
      return {pulse, 0, 0};
    for (int s = 1; s <= strands; ++s) {
      const int boundary = s * per;
      if (boundary >= total)
        break;
      if (n == boundary || n == boundary + 1)
        return {0, 0, pulse};
    }
    if (n <= per * strands)
      return white;
    if (n <= total)
      return {base, 0, base};
    return off;
  }
  case 2: { // Guide: the expected boundary stays visible while current position
            // moves.
    if (n > model.count)
      return off;
    for (int b = 0; b <= model.used; ++b) {
      if (n == expected(model, b))
        return {pulse, 0, 0};
      if (n == expected(model, b) + 1)
        return {0, 0, pulse};
    }
    if (n == current)
      return {pulse, pulse, pulse};
    if (n == current - 1)
      return {base, 0, 0};
    if (n == current + 1)
      return {0, 0, base};
    const uint8_t dim = base / 3;
    return n < current ? RGB{dim, dim, dim} : off;
  }
  case 3: // Finder: previous red, target white, next blue.
  case 4: // Walk: same pattern, automatically advances.
    if (n == current)
      return {pulse, pulse, pulse};
    if (n == current - 1)
      return {base, 0, 0};
    if (n == current + 1)
      return {0, 0, base};
    return off;
  case 5:
    return n <= model.count && n >= start && n <= finish ? white : off;
  case 6:
    return n <= model.count ? RGB{base, 0, 0} : off;
  case 7:
    return n <= model.count ? RGB{0, base, 0} : off;
  case 8:
    return n <= model.count ? RGB{0, 0, base} : off;
  case 9:
    return n <= model.count ? white : off;
  case 10: { // Smooth full-spectrum rainbow, animated along the model.
    if (n > model.count)
      return off;
    return rainbow((uint8_t)((index * 256 / model.count + tick / 20) % 256),
                   base);
  }
  case 11: { // Single pixel scan.
    const int active = (tick / 35) % model.count + 1;
    return n == active ? white : off;
  }
  case 12: { // RGB wipe.
    if (n > model.count)
      return off;
    const int phase = (tick / 25) % (model.count * 3);
    if (n > phase % model.count + 1)
      return off;
    switch (phase / model.count) {
    case 0:
      return {base, 0, 0};
    case 1:
      return {0, base, 0};
    default:
      return {0, 0, base};
    }
  }
  }
  return off;
}
} // namespace pixeltool
