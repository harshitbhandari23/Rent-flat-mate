import os, smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.environ.get('SMTP_HOST')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USER = os.environ.get('SMTP_USER')
SMTP_PASS = os.environ.get('SMTP_PASS')

def send_email(to, subject, body):
    if not SMTP_HOST or not SMTP_USER:
        print(f"[EMAIL - console fallback] To: {to} | Subject: {subject}\n{body}\n")
        return
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "Rent flatmate<harshitbhandari518@gmail.com>"
        msg['To'] = to
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
              server.set_debuglevel(1)
              server.ehlo()
              server.starttls()
              server.ehlo()
              server.login(SMTP_USER, SMTP_PASS)
              server.sendmail("harshitbhandari518@gmail.com", [to], msg.as_string())
    except Exception as e:
        print(f"[EMAIL FAILED] {e} -- To: {to} | Subject: {subject}\n{body}")
