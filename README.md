# InkyPi NeoFrame backend

Build and run on an amd64 Docker host:

```sh
docker compose up --build -d
curl -f http://localhost:8084/api/current_frame -o current_frame.bin
```

Firmware image_url: `http://<inkypi-host>:8084/api/current_frame`.
The original `/api/current_image` PNG route is unchanged. The frame endpoint returns 404 before a successful render and 960000 packed bytes afterwards. Identical packed output preserves mtime and ETag; changed output is atomically replaced. Conditional requests support both If-Modified-Since and If-None-Match. Failures are logged and preserve the last successful frame. Visit `http://<inkypi-host>:8084/api/current_frame?preview` in a browser to view the packed bytes decoded back into a PNG, oriented as the mounted panel will display them (not raw pixel-for-pixel bytes — no caching headers).

The Docker build clones pinned upstream InkyPi, copies the added modules, and applies two checked registration edits. It never changes content plugins or the PNG handler. Override `INKYPI_REF` at build time to upgrade; incompatible registration seams fail the build. This avoids shipping stale full replacements for upstream files. `src/display/abstract_display.py` is a copy for standalone development only and is not overlaid.

Configuration and images persist in Compose named volumes. On an existing installation, update its persisted device.json to display_type `neoframe` and resolution `[1200,1600]`; an existing volume takes precedence over image defaults. Set orientation `vertical` and `inverted_image` true for the native frame. Upstream enhancements and inversion run before packing. Python's reference-faithful dithering can take several seconds per frame.

The panel is native 1200×1600 (GD's `EPD_WIDTH`/`EPD_HEIGHT`), matching the `../neoframe` P0 firmware's `nf_row_offset` layout (600-byte/1200-pixel rows × 1600 rows, split 300/300 between its two controllers). It is mounted rotated 90° clockwise inside the NeoFrame enclosure, so `device.json` uses InkyPi's own `orientation`/`inverted_image` handling (rather than a custom rotate in `neoframe_display.py`) to rotate composed content 270° before it reaches the packer: `orientation: vertical` rotates 90° pre-resize, `inverted_image: true` adds another 180° post-resize. This is unrelated to the stock-format comparison below, which targets a different device's convention.

## Verification

```sh
uv venv .venv
uv pip install --python .venv/bin/python pillow flask pytest requests nodejs-wheel
.venv/bin/python -m pytest -s tests
```

To fetch the pinned reference sources:

```sh
mkdir -p .reference
git clone https://github.com/fatihak/InkyPi.git .reference/inkypi-src
git -C .reference/inkypi-src checkout 2ff58067d05356802d95884c0bb7d8d03d205087
git clone https://github.com/deftdawg/neoframe.git .reference/neoframe-src
git -C .reference/neoframe-src checkout a4ccd6104d15368fc7ee15fa2ed433cc2ce44f55
```

Tests need reference checkouts in `.reference/inkypi-src` and `.reference/neoframe-src`, at the commits listed in REFERENCES.md. Node 24 executes the original TypeScript directly. Tests compare small random fixtures and a full-resolution gradient byte-for-byte, exercise the actual upstream display manager and unchanged PNG route, and check publication failures and HTTP validators. Full-size comparison artifacts are written to `artifacts/`.

To verify a captured stock upload, export the exact final 1600×1200 PNG and process it in the stock tool with contrast 1, Floyd–Steinberg strength 1, sixColor, rotation 0, no scaling and no QR overlay:

```sh
.venv/bin/python scripts/compare_stock.py final.png image_data.bin
```

Source parity does not establish physical panel acceptance. M3's captured working-stock byte dump and M4's firmware/panel test still require your stock output and hardware. Point the firmware at the endpoint, check its first download and panel colors/orientation, then confirm an unchanged request returns 304 and a changed render downloads a new frame.

See REFERENCES.md for format provenance and VALIDATION.md for results and environment limitations.

## Home Assistant OS

This repository is itself a Home Assistant add-on repository (`repository.yaml`), with the self-contained add-on in `inkypi_neoframe/`. In Home Assistant, add `https://github.com/tomschut/inkypi-neoframe` under **Settings → Add-ons → Add-on store → ⋮ → Repositories**, then install **InkyPi NeoFrame** from the store. See `inkypi_neoframe/DOCS.md` for full steps, including an offline fallback. Run `python3 scripts/package_addon.py` after changing the backend to keep `inkypi_neoframe/` in sync (also regenerates `dist/inkypi-neoframe-haos.tar.gz` for the offline install path). Currently supports amd64 HAOS.
