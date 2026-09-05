"""Apply only the two registration seams; fail on incompatible upstream changes."""

from pathlib import Path
import shutil
import sys

source = Path(__file__).resolve().parents[1]
target = Path(sys.argv[1]).resolve()
changes = {
    "src/display/display_manager.py": [
        (
            "from display.mock_display import MockDisplay",
            "from display.mock_display import MockDisplay\nfrom display.neoframe_display import NeoFrameDisplay",
        ),
        (
            '        elif display_type == "inky":',
            '        elif display_type == "neoframe":\n            self.display = NeoFrameDisplay(device_config)\n        elif display_type == "inky":',
        ),
    ],
    "src/inkypi.py": [
        (
            "from blueprints.main import main_bp",
            "from blueprints.main import main_bp\nfrom blueprints.frame import frame_bp",
        ),
        (
            "app.register_blueprint(main_bp)",
            "app.register_blueprint(main_bp)\napp.register_blueprint(frame_bp)",
        ),
    ],
}
prepared = {}
for name, replacements in changes.items():
    text = (target / name).read_text()
    for old, new in replacements:
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit(f"Unsupported upstream seam: {name}: {old}")
        text = text.replace(old, new)
    prepared[name] = text
for name, text in prepared.items():
    (target / name).write_text(text)
for name in ("src/display/neoframe_display.py", "src/blueprints/frame.py"):
    shutil.copy2(source / name, target / name)
print("NeoFrame overlay applied")
