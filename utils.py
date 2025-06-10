import smtplib
from email.mime.text import MIMEText
import mysql.connector
from datetime import datetime
from config import EMAIL_CONFIG
import re

def validate_email(email):
    """Validation simple d'email avec regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_db_connection():
    """Établit une connexion à la base de données MySQL"""
    try:
        conn = mysql.connector.connect(
            host=EMAIL_CONFIG['db']['host'],
            user=EMAIL_CONFIG['db']['user'],
            passwd= '',
            database=EMAIL_CONFIG['db']['database'],
            connect_timeout=5
        )
        print("Connexion DB réussie")
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
    
    if not conn:
        print("Échec de la connexion à la base")
        return recipients

    try:
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT DISTINCT email 
        FROM destination_email
        WHERE email IS NOT NULL 
        AND email != ''
        """
        cursor.execute(query)
        
        for row in cursor:
            email = row['email'].strip().lower()
            if validate_email(email):
                recipients.append(email)
            else:
                print(f"Email invalide ignoré: {email}")

        print(f"{len(recipients)} emails valides trouvés")
        
    except mysql.connector.Error as e:
        print(f"Erreur SQL: {e}")
    finally:
        if conn.is_connected():
            conn.close()
    
    return recipients

def send_email(subject, body, config, recipients=None):
    """
    Envoie un email aux destinataires.
    Si recipients=None, les récupère depuis la base de données
    """
    if not config.get('enabled', False):
        print("Notifications email désactivées")
        return False

    # Récupération des destinataires si non fournis
    if recipients is None:
        recipients = get_active_recipients()

    if not recipients:
        print("Aucun destinataire valide")
        return False

    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = config['sender']
        msg['To'] = ', '.join(recipients)

        with smtplib.SMTP_SSL(config['server'], config['port']) as server:
            server.login(config['username'], config['password'])
            server.sendmail(config['sender'], recipients, msg.as_string())
        
        print(f"Email envoyé à {len(recipients)} destinataires")
        return True
        
    except smtplib.SMTPException as e:
        print(f"Erreur SMTP: {str(e)}")
    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")
    
    return False

if __name__ == "__main__":
    # Exemple d'utilisation
    send_email(
        subject="Test d'envoi",
        body="Ceci est un test de fonctionnement",
        config=EMAIL_CONFIG
    )