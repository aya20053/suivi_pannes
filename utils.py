import smtplib
from email.mime.text import MIMEText
import mysql.connector
from datetime import datetime
from config import EMAIL_CONFIG

def get_db_connection():
    """Établit une connexion à la base de données MySQL"""
    try:
        conn = mysql.connector.connect(**EMAIL_CONFIG['db'])
        return conn
    except mysql.connector.Error as e:
        print(f"Erreur de connexion MySQL : {e}")
        return None

def get_active_recipients():
    """
    Récupère tous les emails actifs de la table destination_email
    Retourne une liste d'adresses email valides
    """
    recipients = []
    conn = get_db_connection()

    if conn:
        try:
            cursor = conn.cursor(dictionary=True)  # ✅ Fix ici
            query = """
            SELECT email 
            FROM destination_email
            WHERE email IS NOT NULL AND email != ''
            """
            cursor.execute(query)

            for row in cursor:
                email = row['email'].strip()
                if '@' in email:
                    recipients.append(email)

            print(f"Destinataires trouvés : {len(recipients)}")

        except mysql.connector.Error as e:
            print(f"Erreur lors de la récupération des emails : {e}")
        finally:
            conn.close()

    return recipients


def send_email(subject, body, config, recipients=None):
    """
    Envoie un email aux destinataires.
    Si recipients=None, les récupère depuis la base de données
    """
    if not config.get('enabled', False):
        print("Envoi d'emails désactivé dans la configuration.")
        return

    # Si aucun destinataire n'est fourni, on les récupère depuis la base
    if recipients is None:
        recipients = get_active_recipients()

    if not recipients:
        print("Aucun destinataire valide trouvé.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config['sender']
    msg['To'] = ', '.join(recipients)

    try:
        print(f"Connexion au serveur SMTP {config['server']}...")
        with smtplib.SMTP_SSL(config['server'], config['port']) as server:
            server.login(config['username'], config['password'])
            server.sendmail(config['sender'], recipients, msg.as_string())

        print(f"Email envoyé avec succès à {len(recipients)} destinataires.")
        print(f"Dernier envoi : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except smtplib.SMTPException as e:
        print(f"Erreur SMTP : {e}")
    except Exception as e:
        print(f"Erreur inattendue : {e}")



if __name__ == "__main__":
    send_email(
        subject="Newsletter - Mise à jour importante",
        body="Bonjour,\n\nVoici les dernières actualités...",
        config=EMAIL_CONFIG
    )
