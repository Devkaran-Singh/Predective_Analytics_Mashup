from flask import Flask, request, jsonify, render_template
import subprocess
import uuid
import zipfile
import os
import smtplib
from email.message import EmailMessage
import threading

job_status = {}
app = Flask(
    __name__,
    template_folder = "webpage",
    static_folder = "webpage"
)
PYTHON_SCRIPT = "102303262.py"
OUTPUT_FILE = "mashup.mp3"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

def zip_results(zip_name, audio_file):
    zip_path = f"{zip_name}.zip" 
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(audio_file, arcname = audio_file)
    return zip_path

def send_email(receiver_email, zip_file):
    msg = EmailMessage()
    msg["Subject"] = "Your Mashup Song Files"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg.set_content("Hi,\n\nYour mashup audio file is attached as a ZIP.\n\nEnjoy!")
    with open(zip_file, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype = "application",
            subtype = "zip",
            filename = os.path.basename(zip_file)
        )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

def process_request(data, job_id):
    singer = data["singer"]
    videos = str(data["videos"])
    duration = str(data["duration"])
    email = data["email"]
    zip_name = singer.replace(" ", "_") + "_mashup"

    subprocess.run([
        "python",
        PYTHON_SCRIPT,
        singer,
        videos,
        duration,
        OUTPUT_FILE
    ])
    zip_file = zip_results(zip_name, OUTPUT_FILE)
    send_email(email, zip_file)
    if os.path.exists(zip_file):
        os.remove(zip_file)
    job_status[job_id] = "done"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    job_id = str(uuid.uuid4())
    job_status[job_id] = "processing"
    thread = threading.Thread(target = process_request, args = (data, job_id))
    thread.start()
    return jsonify({
        "job_id": job_id,
        "message": "Mashup generation started. You will receive a ZIP file via email."
    })

@app.route("/status/<job_id>")
def status(job_id):
    return jsonify({
        "status": job_status.get(job_id, "unknown")
    })


if __name__ == "__main__":
    app.run(debug=True)
