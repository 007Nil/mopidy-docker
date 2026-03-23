from flask import Flask, jsonify, request, send_file
import subprocess
import threading
import time
import os
import urllib.parse
import requests
import logging

app = Flask(__name__)

MOPIDY_RPC = "http://localhost:6680/mopidy/rpc"
MUSIC_ROOT = "/music/"  # Set to Mopidy's local.media_dir

LOG_FILE = "/tmp/scan_server.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

scan_state = {
    "running": False,
    "last_started": None,
    "last_finished": None,
    "last_status": "idle"
}
lock = threading.Lock()

def run_scan():
    global scan_state
    with lock:
        scan_state["running"] = True
        scan_state["last_started"] = time.time()
        scan_state["last_status"] = "running"

    try:
        subprocess.run(
            ["mopidy", "--config", "/config/mopidy.conf", "local", "scan"],
            check=True
        )
        status = "success"
    except Exception as e:
        log.error("Scan failed: %s", e)
        status = "failed"

    with lock:
        scan_state["running"] = False
        scan_state["last_finished"] = time.time()
        scan_state["last_status"] = status


@app.route("/rescan", methods=["POST"])
def rescan():
    if scan_state["running"]:
        return jsonify({"status": "already_running"}), 409

    thread = threading.Thread(target=run_scan)
    thread.start()

    return jsonify({"status": "scan_started"}), 202


@app.route("/scan-status", methods=["GET"])
def scan_status():
    return jsonify(scan_state), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route('/artwork', methods=['POST'])
def upload_artwork():
    track_uri = request.form.get('track_uri', '').strip()
    image = request.files.get('image')

    log.debug("=== /artwork request ===")
    log.debug("track_uri=%r", track_uri)
    log.debug("image=%r", image)

    if not track_uri or not image:
        log.error("Missing track_uri or image")
        return jsonify({'status': 'error', 'message': 'Missing track_uri or image'}), 400

    try:
        encoded_path = track_uri.replace('local:track:', '', 1)
        decoded_path = urllib.parse.unquote(encoded_path)
        track_file = os.path.join(MUSIC_ROOT, decoded_path)
        album_dir = os.path.dirname(track_file)

        log.debug("encoded_path=%r", encoded_path)
        log.debug("decoded_path=%r", decoded_path)
        log.debug("track_file=%r", track_file)
        log.debug("album_dir=%r", album_dir)
        log.debug("os.path.isdir(album_dir)=%r", os.path.isdir(album_dir))

        # List parent to help debug mismatches
        parent = os.path.dirname(album_dir)
        try:
            entries = os.listdir(parent)
            log.debug("Contents of %r: %r", parent, entries)
        except Exception as list_err:
            log.debug("Could not list %r: %s", parent, list_err)

        if not os.path.isdir(album_dir):
            return jsonify({'status': 'error', 'message': f'Album directory not found: {album_dir}'}), 404

        cover_path = os.path.join(album_dir, 'cover.jpg')
        image.save(cover_path)
        log.info("Saved artwork to %r", cover_path)

        # Trigger Mopidy to re-index
        try:
            requests.post(
                MOPIDY_RPC,
                json={'jsonrpc': '2.0', 'id': 1, 'method': 'core.library.refresh', 'params': {}},
                timeout=5
            )
            log.info("Triggered Mopidy library refresh")
        except Exception as rpc_err:
            log.warning("Mopidy refresh failed (artwork saved OK): %s", rpc_err)

        return jsonify({'status': 'ok', 'path': cover_path})
    except Exception as e:
        log.exception("Unexpected error in /artwork")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/cover', methods=['GET'])
def serve_cover():
    track_uri = request.args.get('track_uri', '').strip()
    if not track_uri:
        return jsonify({'status': 'error', 'message': 'Missing track_uri'}), 400
    try:
        encoded_path = track_uri.replace('local:track:', '', 1)
        decoded_path = urllib.parse.unquote(encoded_path)
        track_file = os.path.join(MUSIC_ROOT, decoded_path)
        album_dir = os.path.dirname(track_file)
        cover_path = os.path.join(album_dir, 'cover.jpg')
        log.debug("/cover: cover_path=%r exists=%r", cover_path, os.path.isfile(cover_path))
        if not os.path.isfile(cover_path):
            return jsonify({'status': 'error', 'message': 'No cover found'}), 404
        return send_file(cover_path, mimetype='image/jpeg')
    except Exception as e:
        log.exception("Unexpected error in /cover")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete', methods=['POST'])
def delete_track():
    track_uri = request.form.get('track_uri', '').strip()
    if not track_uri:
        return jsonify({'status': 'error', 'message': 'Missing track_uri'}), 400
    try:
        encoded_path = track_uri.replace('local:track:', '', 1)
        decoded_path = urllib.parse.unquote(encoded_path)
        track_file = os.path.join(MUSIC_ROOT, decoded_path)
        log.debug("/delete: track_file=%r exists=%r", track_file, os.path.isfile(track_file))
        if not os.path.isfile(track_file):
            return jsonify({'status': 'error', 'message': f'File not found: {track_file}'}), 404
        os.remove(track_file)
        log.info("Deleted track file: %r", track_file)
        try:
            requests.post(
                MOPIDY_RPC,
                json={'jsonrpc': '2.0', 'id': 1, 'method': 'core.library.refresh', 'params': {}},
                timeout=5
            )
            log.info("Triggered Mopidy library refresh after delete")
        except Exception as rpc_err:
            log.warning("Mopidy refresh failed (file deleted OK): %s", rpc_err)
        return jsonify({'status': 'ok'})
    except Exception as e:
        log.exception("Unexpected error in /delete")
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == "__main__":
    log.info("Starting scan server, MUSIC_ROOT=%r", MUSIC_ROOT)
    app.run(host="0.0.0.0", port=9000)
