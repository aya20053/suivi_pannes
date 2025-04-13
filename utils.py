import smtplib
from email.mime.text import MIMEText
# from utils import send_email # Supprimé car on intègre la fonction ici
from config import EMAIL_CONFIG

def send_email(subject, body, recipients, config):
    """
    Envoie un email en utilisant SMTP.

    Args:
        subject (str): Le sujet de l'email.
        body (str): Le corps (contenu) de l'email.
        recipients (list): Une liste des adresses email des destinataires.
        config (dict): Un dictionnaire contenant les paramètres de configuration de l'email
                        (serveur, port, nom d'utilisateur, mot de passe, expéditeur, enabled).
    """
    print("DEBUG (utils.send_email): Fonction appelée")
    if not config.get('enabled', False):
        print("DEBUG (utils.send_email): L'envoi d'emails est désactivé")
        return

    # Filtrer toutes les valeurs None de la liste des destinataires
    valid_recipients = [recipient for recipient in recipients if recipient is not None]

    if not valid_recipients:
        print("DEBUG (utils.send_email): Aucun destinataire valide trouvé. Email non envoyé.")
        return

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = config.get('sender')
    msg['To'] = ', '.join(valid_recipients)

    print(f"DEBUG (utils.send_email): Tentative de connexion à {config.get('server')}:{config.get('port')}")
    try:
        with smtplib.SMTP_SSL(config.get('server'), config.get('port')) as server:
            print("DEBUG (utils.send_email): Connexion SMTP_SSL établie")
            server.login(config.get('username'), config.get('password'))
            print("DEBUG (utils.send_email): Connexion réussie")
            server.sendmail(config.get('sender'), valid_recipients, msg.as_string())
            print(f"DEBUG (utils.send_email): Email envoyé à : {valid_recipients}")
    except smtplib.SMTPException as e:
        print(f"DEBUG (utils.send_email): Une exception SMTPException s'est produite : {e}")
    except Exception as e:
        print(f"DEBUG (utils.send_email): Une exception générale s'est produite : {e}")



print(f"DEBUG (test_email.py): EMAIL_CONFIG['recipients'] = {EMAIL_CONFIG['recipients']}")
