"""Serve an immutable snapshot, so validators and body describe the same frame."""

from pathlib import Path
import hashlib
from flask import Blueprint, current_app, Response, jsonify, request

frame_bp = Blueprint("frame", __name__)


@frame_bp.route("/api/current_frame")
def current_frame():
    path = Path(current_app.config["DEVICE_CONFIG"].current_image_file).with_name(
        "current_frame.bin"
    )
    try:
        with path.open("rb") as f:
            import os

            stamp = int(os.fstat(f.fileno()).st_mtime)
            payload = f.read()
    except FileNotFoundError:
        return jsonify(error="Frame not found"), 404
    response = Response(payload, mimetype="application/octet-stream")
    response.last_modified = stamp
    response.set_etag(hashlib.sha256(payload).hexdigest())
    response.cache_control.no_cache = True
    return response.make_conditional(request)
