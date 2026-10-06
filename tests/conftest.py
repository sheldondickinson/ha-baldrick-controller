# Unit tests isolate the client from Home Assistant package startup.
import pathlib
import sys
import types

p = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(p))
for name, path in [
    ("custom_components", p / "custom_components"),
    (
        "custom_components.baldrick_controller",
        p / "custom_components/baldrick_controller",
    ),
]:
    m = types.ModuleType(name)
    m.__path__ = [str(path)]
    sys.modules[name] = m
