from datetime import datetime
from flask_mail import Message


# Function to send email
def send_email(recipient,subject,html):
    from app import app, mail
    with app.app_context():
        msg = Message(subject=subject, recipients=[recipient])
        msg.html = html
        mail.send(msg)
        print("Email sent successfully at", datetime.now())