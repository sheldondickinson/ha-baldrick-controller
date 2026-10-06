/* Exact model colours used by both the on-board map and the desktop preview.
 * The C++ implementation in PusherCore.h is cross-checked against this file.
 */
function runForNode(model, node) {
  let k = 0;
  while (k + 1 < model.checkpoints.length && model.checkpoints[k + 1].node <= node) k++;
  return k;
}
function pixelRGB(data, state, node, pulse) {
  const model = data.models[state.model];
  if (!state.enabled || node < state.first || node > model.count) return [0, 0, 0];
  const k = runForNode(model, node), marker = model.checkpoints[k].node === node;
  const dim = Math.max(1, Math.floor(state.level / 6));
  const tint = level => data.palette[model.checkpoints[k].colour].rgb.map(v => Math.floor((v * level + 127) / 255));
  if (state.mode === 4) return [state.level, 0, 0];
  if (state.mode === 5) return [0, state.level, 0];
  if (state.mode === 6) return [0, 0, state.level];
  if (state.mode === 1) return marker ? tint(state.level) : [dim, dim, dim];
  if (state.mode === 3 && node === state.node && pulse) return [state.level, state.level, state.level];
  if (state.mode === 2 && k === state.run) {
    if (marker && pulse) return [state.level, state.level, state.level];
    return tint(state.level);
  }
  return tint(marker ? state.level : dim);
}
if (typeof module !== 'undefined') module.exports = {runForNode, pixelRGB};
