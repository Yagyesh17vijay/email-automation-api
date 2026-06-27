from dotenv import dotenv_values
print(dotenv_values(".env"))

from flask import Flask, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
import os
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

print("email =", SENDER_EMAIL)
print("password =", APP_PASSWORD)

def send_email(receiver_email, message, subject):
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = receiver_email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

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
        data = request.json

        receiver_email = data.get("email")
        message = data.get("message")
        subject= data.get("subject")

        if not receiver_email or not message:
            return jsonify({"error": "Email and message required"}), 400
        
        success, response = send_email(receiver_email, message, subject)

        if success:
            return jsonify({"status": response}), 200
        else:
            return jsonify({"error": response}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)