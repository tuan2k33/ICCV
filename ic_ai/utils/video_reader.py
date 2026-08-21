import sys
from pathlib import Path

_PROJ = Path(__file__).parent.parent
_DECORD_PYTHON = str(_PROJ / "decord" / "python")
try:
    from decord import VideoReader as _VR  # noqa: F401
    del _VR
except (ImportError, AttributeError):
    if _DECORD_PYTHON not in sys.path:
        sys.path.insert(0, _DECORD_PYTHON)
    for _mod in list(k for k in sys.modules if k.startswith("decord")):
        del sys.modules[_mod]

import decord
decord.bridge.set_bridge("torch")


def _decord_device_index(device: str) -> int:
    return int(device.split(":")[1]) if ":" in device else 0


class VideoReader:
    def __init__(self, path, device="cuda"):
        ctx = decord.gpu(_decord_device_index(device))
        self._vr = decord.VideoReader(str(path), ctx=ctx, num_threads=0)
        _shape = self._vr.get_batch([0]).shape
        self._num_frames = len(self._vr)
        self._height = int(_shape[1])
        self._width = int(_shape[2])
        self._fps = float(self._vr.get_avg_fps())

    def __len__(self): return self._num_frames
    def __getitem__(self, idx): return self._vr[idx]
    def get_batch(self, indices): return self._vr.get_batch(indices)
    def get_shape(self): return (self._num_frames, self._height, self._width, 3)
    def get_fps(self): return self._fps
