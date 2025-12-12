import os, uuid
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from tasks import process_files_task, celery
from celery.result import AsyncResult
from flask_socketio import SocketIO
import eventlet
eventlet.monkey_patch()

load_dotenv()

UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "output")
ALLOWED_EXT = {".pdf", ".docx", ".doc", ".txt", ".jpg", ".jpeg", ".png"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

@app.route("/", methods=["GET"])
def index():
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        tesseract_ok = True
    except Exception:
        tesseract_ok = False
    return render_template("index.html", tesseract_ok=tesseract_ok)

@app.route("/upload", methods=["POST"])
def upload():
    if "files" not in request.files:
        flash("No files part")
        return redirect(url_for("index"))
    files = request.files.getlist("files")
    saved = []
    for f in files:
        if f and os.path.splitext(f.filename)[1].lower() in ALLOWED_EXT:
            name = secure_filename(f.filename)
            uid = uuid.uuid4().hex[:8]
            final = f"{uid}__{name}"
            path = os.path.join(app.config["UPLOAD_FOLDER"], final)
            f.save(path)
            saved.append(path)
    if not saved:
        flash("No valid files uploaded.")
        return redirect(url_for("index"))
    task = process_files_task.delay(saved, app.config["OUTPUT_FOLDER"])
    return redirect(url_for("status", task_id=task.id))

@app.route("/status/<task_id>")
def status(task_id):
    return render_template("status.html", task_id=task_id)

@socketio.on("watch")
def watch(data):
    task_id = data.get("task_id")
    sid = request.sid
    def monitor():
        import time
        while True:
            res = AsyncResult(task_id, app=celery)
            meta = getattr(res, "info", None)
            try:
                socketio.emit("update", {"state": res.state, "meta": meta}, room=sid)
            except Exception:
                pass
            if res.state in ("SUCCESS", "FAILURE", "REVOKED"):
                break
            time.sleep(2)
    socketio.start_background_task(monitor)

@app.route("/api/status/<task_id>")
def api_status(task_id):
    res = AsyncResult(task_id, app=celery)
    info = {"id": task_id, "state": res.state, "result": res.result if res.ready() else None}
    if res.state == "SUCCESS" and isinstance(res.result, dict) and res.result.get("output"):
        info["download_url"] = url_for("download", filename=os.path.basename(res.result["output"]), _external=True)
    return jsonify(info)

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(app.config["OUTPUT_FOLDER"], filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Not found", 404

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))