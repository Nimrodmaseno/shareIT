from flask import Flask, render_template, request, send_from_directory, redirect
import os
import uuid
import qrcode
import base64
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

sessions = {}

@app.route("/")
def home():

    session_id = str(uuid.uuid4())[:8]

    if session_id not in sessions:
        sessions[session_id] = []

    return redirect(f"/session/{session_id}")

@app.route("/session/<session_id>", methods=["GET", "POST"])
def session(session_id):

    session_folder = os.path.join(
        UPLOAD_FOLDER,
        session_id
    )

    os.makedirs(session_folder, exist_ok=True)

    if session_id not in sessions:
        sessions[session_id] = []

    if request.method == "POST":

        file = request.files["file"]

        if file.filename:

            filepath = os.path.join(
                session_folder,
                file.filename
            )

            file.save(filepath)

            if file.filename not in sessions[session_id]:
                sessions[session_id].append(
                    file.filename
                )

    link = request.url

    qr = qrcode.make(link)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_b64 = base64.b64encode(
        buffer.getvalue()
    ).decode()

    return render_template(
        "index.html",
        qr=qr_b64,
        link=link,
        session_id=session_id,
        files=sessions[session_id]
    )

@app.route("/download/<session_id>/<filename>")
def download(session_id, filename):

    folder = os.path.join(
        UPLOAD_FOLDER,
        session_id
    )

    return send_from_directory(
        folder,
        filename,
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )