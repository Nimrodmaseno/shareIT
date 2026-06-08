from flask import Flask, render_template, request, send_from_directory, redirect, jsonify
import os, uuid, qrcode, base64, time
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

sessions = {}  
# { session_id: [ {filename, time} ] }


# 🧹 CLEAN OLD FILES (2 min expiry)
def cleanup():
    now = time.time()
    for sid in list(sessions.keys()):
        folder = os.path.join(UPLOAD_FOLDER, sid)

        if sid in sessions:
            updated = []

            for f in sessions[sid]:
                if now - f["time"] < 120:
                    updated.append(f)
                else:
                    try:
                        os.remove(os.path.join(folder, f["name"]))
                    except:
                        pass

            sessions[sid] = updated


@app.route("/")
def home():
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = []

    return redirect(f"/session/{session_id}")


@app.route("/session/<session_id>", methods=["GET"])
def session(session_id):
    cleanup()

    if session_id not in sessions:
        sessions[session_id] = []

    link = request.url

    qr = qrcode.make(link)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_b64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template(
        "index.html",
        session_id=session_id,
        qr=qr_b64,
        link=link
    )


@app.route("/upload/<session_id>", methods=["POST"])
def upload(session_id):
    cleanup()

    file = request.files["file"]

    folder = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(folder, exist_ok=True)

    filepath = os.path.join(folder, file.filename)
    file.save(filepath)

    if session_id not in sessions:
        sessions[session_id] = []

    sessions[session_id].append({
        "name": file.filename,
        "time": time.time()
    })

    return jsonify({"status": "ok"})


@app.route("/files/<session_id>")
def files(session_id):
    cleanup()

    return jsonify(sessions.get(session_id, []))


@app.route("/download/<session_id>/<filename>")
def download(session_id, filename):
    folder = os.path.join(UPLOAD_FOLDER, session_id)

    return send_from_directory(folder, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
