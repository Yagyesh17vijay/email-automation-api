from dotenv import dotenv_values

from flask import Flask, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase

app = Flask(__name__)
import os
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

print("email =", SENDER_EMAIL)

def send_email(receiver_email, message, subject=None, attachment=None):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        if attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

            encoders.encode_base64(part)

            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{attachment.filename}"'
            )

            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)

        server.send_message(msg)
        server.quit()

        return True, "Email sent successfully"

    except Exception as e:
        return False, str(e)


@app.route('/')
def home():
    return "Email Automation API Running"


@app.route('/send-email', methods=['POST'])
def send_email_api():
    try:

        receiver_email = request.form.get("email")
        message = request.form.get("message")
        subject= request.form.get("subject")
        attachment= request.files.get("attachment")

        if not receiver_email or not message:
            return jsonify({"error": "Email and message required"}), 400
        
        success, response = send_email(receiver_email, message, subject, attachment)

        if success:
            return jsonify({"status": response}), 200
        else:
            return jsonify({"error": response}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)