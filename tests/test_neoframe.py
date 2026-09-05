import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace
import pytest
from PIL import Image
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from display import neoframe_display as backend
from blueprints.frame import frame_bp


@pytest.mark.parametrize("size", [(6, 1), (64, 48), (1600, 1200)])
def test_original_typescript_parity(tmp_path, size):
    source = ROOT / ".reference/neoframe-src/src/algorithms.ts"
    assert source.exists(), "Fetch pinned reference per README"
    rng = random.Random(184)
    if size == (1600, 1200):
        image = Image.new("RGB", size)
        # Full-size gradients exercise row boundaries and every nibble position.
        image.putdata(
            [
                ((x * 255) // 1599, (y * 255) // 1199, ((x + y) * 19) % 256)
                for y in range(1200)
                for x in range(1600)
            ]
        )
    else:
        image = Image.frombytes("RGB", size, rng.randbytes(size[0] * size[1] * 3))
    image.save(tmp_path / "input.png")
    (tmp_path / "input.rgba").write_bytes(image.convert("RGBA").tobytes())
    runner = tmp_path / "reference.mjs"
    runner.write_text(
        """import {readFileSync,writeFileSync} from 'node:fs';
import {ditherImage,processImageData} from '"""
        + source.as_uri()
        + """';
const image={width:Number(process.argv[2]),height:Number(process.argv[3]),data:new Uint8ClampedArray(readFileSync(process.argv[4]))};
const config={ditherType:'floydSteinberg',ditherStrength:'1',ditherMode:'sixColor'};
ditherImage(image,config);
writeFileSync(process.argv[5],processImageData(image,config));
"""
    )
    expected = tmp_path / "stock-reference.bin"
    subprocess.run(
        [
            str(ROOT / ".venv/bin/node"),
            str(runner),
            str(size[0]),
            str(size[1]),
            str(tmp_path / "input.rgba"),
            str(expected),
        ],
        check=True,
    )
    start = time.monotonic()
    actual = backend.encode_frame(image)
    assert actual == expected.read_bytes()
    print(
        f"Parity {size}: {len(actual)} bytes, Python {time.monotonic() - start:.2f}s, SHA256 {hashlib.sha256(actual).hexdigest()}"
    )
    if size == (1600, 1200):
        out = ROOT / "artifacts"
        out.mkdir(exist_ok=True)
        shutil.copy2(tmp_path / "input.png", out / "reference-input.png")
        shutil.copy2(expected, out / "reference.bin")
        (out / "python.bin").write_bytes(actual)


def test_palette_order():
    image = Image.new("RGB", (6, 1))
    image.putdata(backend.PALETTE)
    assert backend.encode_frame(image) == bytes.fromhex("26 53 01")


@pytest.fixture
def setup(tmp_path):
    config = SimpleNamespace(current_image_file=str(tmp_path / "current_image.png"))
    display = backend.NeoFrameDisplay(config)
    app = Flask(__name__)
    app.config["DEVICE_CONFIG"] = config
    app.register_blueprint(frame_bp)
    return display, app.test_client()


def test_publication_and_http(setup, monkeypatch):
    display, client = setup
    assert client.get("/api/current_frame").status_code == 404
    payload = b"\x12" * 960000
    monkeypatch.setattr(backend, "encode_frame", lambda image: payload)
    monkeypatch.setattr(backend.time, "time", lambda: 1700000000)
    image = Image.new("RGB", (1200, 1600))
    display.display_image(image)
    first = client.get("/api/current_frame")
    assert first.status_code == 200 and first.data == payload
    assert first.mimetype == "application/octet-stream"
    assert first.headers["Cache-Control"] == "no-cache"
    stamp = display.path.stat().st_mtime_ns
    display.display_image(image)
    assert display.path.stat().st_mtime_ns == stamp
    assert (
        client.get(
            "/api/current_frame",
            headers={"If-Modified-Since": first.headers["Last-Modified"]},
        ).status_code
        == 304
    )
    assert (
        client.get(
            "/api/current_frame", headers={"If-None-Match": first.headers["ETag"]}
        ).status_code
        == 304
    )
    assert (
        client.get(
            "/api/current_frame", headers={"If-Modified-Since": "garbage"}
        ).status_code
        == 200
    )
    assert client.head("/api/current_frame").data == b""
    payload = b"\x56" * 960000
    display.display_image(image)
    changed = client.get(
        "/api/current_frame",
        headers={"If-Modified-Since": first.headers["Last-Modified"]},
    )
    assert changed.status_code == 200 and changed.data == payload
    assert changed.headers["Last-Modified"] != first.headers["Last-Modified"]
    assert changed.headers["ETag"] != first.headers["ETag"]
    # ETag takes precedence over an old timestamp.
    assert (
        client.get(
            "/api/current_frame",
            headers={
                "If-None-Match": changed.headers["ETag"],
                "If-Modified-Since": first.headers["Last-Modified"],
            },
        ).status_code
        == 304
    )
    previous = display.path.read_bytes()
    payload = b"\x00" * 960000

    def fail(*args):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(backend.os, "replace", fail)
    display.display_image(image)
    assert display.path.read_bytes() == previous
    assert not list(display.path.parent.glob(".frame-*"))
    display.display_image(Image.new("RGB", (8, 8)))
    assert display.path.read_bytes() == previous


def test_overlay_and_actual_manager(tmp_path):
    upstream = ROOT / ".reference/inkypi-src"
    target = tmp_path / "inkypi"
    shutil.copytree(upstream, target)
    main = (target / "src/blueprints/main.py").read_bytes()
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/apply_overlay.py"), str(target)],
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/apply_overlay.py"), str(target)],
        check=True,
    )
    assert (target / "src/blueprints/main.py").read_bytes() == main
    # Separate interpreter exercises the real upstream manager and route imports.
    code = """
import sys
from pathlib import Path
from PIL import Image
from flask import Flask
from display.display_manager import DisplayManager
from blueprints.main import main_bp
from blueprints.frame import frame_bp
class Config:
    current_image_file=str(Path('src/static/images/current_image.png').resolve())
    def get_resolution(self): return (1200,1600)
    def get_config(self,key,default=None):
        return {'display_type':'neoframe','orientation':'vertical','inverted_image':True,'image_settings':{}}.get(key,default)
c=Config()
Path(c.current_image_file).parent.mkdir(parents=True,exist_ok=True)
m=DisplayManager(c)
img=Image.new('RGB',(1600,1200),'white')
img.paste('black',(0,0,800,1200))
m.display_image(img)
assert Image.open(c.current_image_file).tobytes()==img.tobytes()
bin=Path(c.current_image_file).with_name('current_frame.bin').read_bytes()
# Left/right halves land as top/bottom halves once packed: the panel is native
# 1200x1600 and mounted rotated 90 deg clockwise, so device.json declares
# resolution [1200,1600] with orientation "vertical" and inverted_image true,
# letting InkyPi's own orientation handling rotate content 270 deg (90+180)
# before it reaches NeoFrameDisplay, instead of a custom rotate in our code.
assert len(bin)==960000 and bin[0]==0x00 and bin[479999]==0x00 and bin[480000]==0x11 and bin[959999]==0x11
app=Flask(__name__)
app.config['DEVICE_CONFIG']=c
app.register_blueprint(main_bp)
app.register_blueprint(frame_bp)
client=app.test_client()
assert client.get('/api/current_image').mimetype=='image/png'
assert client.get('/api/current_frame').data==bin
print('Actual upstream render, inversion, PNG and BIN routes passed')
"""
    env = dict(os.environ, PYTHONPATH=str(target / "src"))
    subprocess.run([sys.executable, "-c", code], cwd=target, env=env, check=True)
