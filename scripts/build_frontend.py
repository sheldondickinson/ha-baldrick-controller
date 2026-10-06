"""Build the HA served shell from maintained companion source templates."""

import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dest = root / "custom_components/baldrick_controller/frontend/pixeltool"
dest.mkdir(parents=True, exist_ok=True)
for source in (root / "pixeltool/static").iterdir():
    shutil.copy2(source, dest / source.name)
