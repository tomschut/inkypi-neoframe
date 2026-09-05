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
    "src/blueprints/settings.py": [
        (
            '        if "inky_saturation" in form_data:\n'
            '            settings["image_settings"]["inky_saturation"] = float(form_data.get("inky_saturation", "0.5"))\n'
            "        device_config.update_config(settings)",
            '        if "inky_saturation" in form_data:\n'
            '            settings["image_settings"]["inky_saturation"] = float(form_data.get("inky_saturation", "0.5"))\n'
            '        if "panelRotation" in form_data:\n'
            '            settings["panel_rotation"] = int(form_data.get("panelRotation"))\n'
            "        device_config.update_config(settings)",
        ),
    ],
    "src/templates/settings.html": [
        (
            '                        <input type="checkbox" id="invertImage" name="invertImage" {% if device_settings.inverted_image %}checked{% endif %}>\n'
            "                        </label>\n"
            "                    </div>\n"
            "                </div>\n",
            '                        <input type="checkbox" id="invertImage" name="invertImage" {% if device_settings.inverted_image %}checked{% endif %}>\n'
            "                        </label>\n"
            "                    </div>\n"
            "                </div>\n"
            '                {% if device_settings.display_type == "neoframe" %}\n'
            '                <div class="form-group nowrap">\n'
            '                    <label for="panelRotation" class="form-label">Panel Rotation:</label>\n'
            '                    <select id="panelRotation" name="panelRotation" class="form-input">\n'
            '                        <option value="90" {% if device_settings.panel_rotation == 90 %}selected{% endif %}>90&deg; clockwise</option>\n'
            '                        <option value="270" {% if device_settings.panel_rotation == 270 %}selected{% endif %}>90&deg; counter-clockwise</option>\n'
            "                    </select>\n"
            "                </div>\n"
            "                {% endif %}\n",
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
