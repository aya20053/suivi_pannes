import smtplib
from email.mime.text import MIMEText

def send_email(subject, body, recipients, config):
    print("DEBUG (utils.send_email): Function called")
    if not config['enabled']:
        print("DEBUG (utils.send_email): Email sending is disabled")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config['sender']
    msg['To'] = ', '.join(recipients)

    print(f"DEBUG (utils.send_email): Attempting to connect to {config['server']}:{config['port']}")
    try:
        with smtplib.SMTP(config['server'], config['port']) as server:
            print("DEBUG (utils.send_email): SMTP connection established")
            server.starttls()
            print("DEBUG (utils.send_email): TLS started")
            server.login(config['username'], config['password'])
            print("DEBUG (utils.send_email): Login successful")
            server.sendmail(config['sender'], recipients, msg.as_string())
            print(f"DEBUG (utils.send_email): Email sent to: {recipients}")
    except smtplib.SMTPException as e:
        print(f"DEBUG (utils.send_email): SMTPException occurred: {e}")
    except Exception as e:
        print(f"DEBUG (utils.send_email): General Exception occurred: {e}")