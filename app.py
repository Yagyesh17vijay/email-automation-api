import os
import re
import logging

from dotenv import load_dotenv

from flask import Flask, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase
from email_history import save_email_activity
from history_api import history_bp

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.register_blueprint(history_bp)
app.config["MAX_CONTENT_LENGTH"] = 6 * 1024 * 1024

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

if not SENDER_EMAIL or not APP_PASSWORD:
    raise RuntimeError(
        "SENDER_EMAIL or APP_PASSWORD is missing from .env"
    )

def send_email(receiver_email, message, subject=None, attachments=None, email_type="plain"):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = subject or ""

    email_type = email_type.lower()
    msg.attach(MIMEText(message, email_type))

    if attachments:
        for attachment in attachments:
            if not attachment or not attachment.filename:
                continue

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)

            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{attachment.filename}"'
            )
            msg.attach(part)

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        logger.exception("Failed to send email")

        try:
            save_email_activity(
                recipient=receiver_email,
                subject=subject or "",
                message=message,
                status="FAILED",
                error_message=str(e)
            )
        except Exception:
            logger.exception("Failed to save email failure record")

        return False, "Failed to send email. Please check the email configuration and try again."

    logger.info("Email sent successfully")

    try:
        save_email_activity(
            recipient=receiver_email,
            subject=subject or "",
            message=message,
            status="SENT"
        )
    except Exception:
        logger.exception(
            "Email was sent, but saving its database record failed"
        )

    return True, "Email sent successfully"

    
@app.route('/')
def home():
    return "Email Automation API Running"


@app.route('/send-email', methods=['POST'])
def send_email_api():
    try:

        receiver_email = request.form.get("email")
        message = request.form.get("message")
        subject= request.form.get("subject")
        attachments= request.files.getlist("attachments")
        email_type = request.form.get("email_type", "").strip().lower() or "plain"

        if not receiver_email or not message:
            return jsonify({"error": "Email and message required"}), 400

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", receiver_email):
            return jsonify({"error": "Invalid email address format"}), 400

        MAX_FILE_SIZE = 5 * 1024 * 1024
        ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

        for attachment in attachments:
            if not attachment or not attachment.filename:
                continue

            extension = os.path.splitext(attachment.filename)[1].lower()

            if extension not in ALLOWED_EXTENSIONS:
                return jsonify({
                    "error": "Only PDF, PNG, JPG, and JPEG files are allowed"
                }), 400

            attachment.stream.seek(0, os.SEEK_END)
            file_size = attachment.stream.tell()
            attachment.stream.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                "error": "Each attachment must be 5 MB or smaller"
            }), 400

        if email_type not in {"plain", "html"}:
            return jsonify({
                "error": "email_type must be either 'plain' or 'html'"
            }), 400

        success, response = send_email(receiver_email, message, subject, attachments, email_type)

        if success:
            return jsonify({"status": response}), 200
        else:
            return jsonify({"error": response}), 500

    except Exception:
        app.logger.exception("Unexpected error in send_email_api")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=True)

