from utils import send_email
from config import EMAIL_CONFIG

print(f"DEBUG (test_email.py): EMAIL_CONFIG['recipients'] = {EMAIL_CONFIG['recipients']}")

send_email(
    subject="Test SMTP avec .env",
    body="Ce mail est envoyé via SMTP et un fichier .env 🎯",
    recipients=EMAIL_CONFIG['recipients'],
    config=EMAIL_CONFIG
)