import subprocess
import platform
from datetime import datetime
import time
import requests
import re
import pymysql
from db import get_db_connection, close_db_connection, execute_query
from utils import send_email
from config import EMAIL_CONFIG, NOTIFICATION_CONFIG

def ping(host):
    """Effectue un ping sur l'hôte et retourne True si réussi, False sinon."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def is_ip_address(host):
    """Vérifie si le host est une adresse IP (IPv4 simple)."""
    return re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host) is not None

def check_site_status(host):
    """Vérifie le statut d'un site web ou IP (HTTP ou ping selon le cas)."""
    if is_ip_address(host):
        # Utilise le ping
        is_up = ping(host)
        reason = "Ping réussi" if is_up else "Ping échoué"
        return is_up, reason

    elif host.startswith("http://") or host.startswith("https://"):
        # Vérifie par HTTP(S)
        try:
            response = requests.get(host, timeout=5)
            is_up = response.status_code == 200
            reason = f"HTTP {response.status_code}" if is_up else f"Réponse HTTP anormale : {response.status_code}"
            return is_up, reason
        except requests.exceptions.RequestException as e:
            return False, f"Erreur HTTP : {e}"

    else:
        return False, "Format de l'adresse non reconnu"

def send_alert(site_name, url_or_ip, reason):
    """Enregistre une alerte dans la base de données ET envoie un email."""
    conn = get_db_connection()
    if not conn:
        print("Erreur : Connexion à la base de données échouée pour enregistrer l'alerte.")
        return
    try:
        with conn.cursor() as cursor:
            query_insert = """
                INSERT INTO alerts (timestamp, site_name, url_or_ip, reason, is_acknowledged)
                VALUES (%s, %s, %s, %s, %s)
            """
            timestamp = datetime.utcnow()
            cursor.execute(query_insert, (timestamp, site_name, url_or_ip, reason, False))
            conn.commit()
            print(f"Alerte enregistrée dans la base de données pour {site_name}: {reason}")

            # Envoi de l'email (comme vous le faisiez déjà)
            subject = f"ALERTE: Site/IP '{site_name}' ({url_or_ip}) est hors ligne"
            body = f"Le reseau: '{site_name}' ({url_or_ip}) est actuellement hors ligne.\n\n\nDernière vérification : {timestamp} (UTC).\n\nRaison : {reason}"

            if EMAIL_CONFIG['enabled']:
                try: # Ajout d'un try...except autour de l'envoi d'email
                    send_email(subject, body, EMAIL_CONFIG['recipients'], EMAIL_CONFIG)
                    print(f"Email envoyé pour {site_name}")
                except Exception as e:
                    print(f"Erreur lors de l'envoi de l'email pour {site_name}: {e}")

            if NOTIFICATION_CONFIG['enabled']:
                print(f"Notification (console) envoyée pour : {site_name} - {reason}") # Gardez votre logique de notification si vous l'utilisez
    except pymysql.Error as e:
        print(f"Erreur lors de l'enregistrement de l'alerte : {e}")
    finally:
        close_db_connection(conn)

def monitor_all_sites():
    """Surveille tous les sites web actifs et envoie des alertes par email et enregistre en DB."""
    print("\n--- Cycle de surveillance lancé ---")
    conn = get_db_connection()
    if not conn:
        print("Erreur : Connexion à la base de données échouée.")
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, url_or_ip, failed_pings_count FROM monitored_sites WHERE enabled = 1")
            sites = cursor.fetchall()
            print(f"{len(sites)} site(s) à surveiller.")

            for site in sites:
                site_id = site['id']
                name = site['name']
                url_or_ip = site['url_or_ip']
                failed_pings_count = site['failed_pings_count']

                is_up, reason = check_site_status(url_or_ip)
                timestamp = datetime.utcnow()

                # Enregistrement de l’événement
                query_insert = """
                    INSERT INTO monitoring_events (site_id, timestamp, status, reason)
                    VALUES (%s, %s, %s, %s)
                """
                status = "En ligne" if is_up else "Hors ligne"
                execute_query(query_insert, (site_id, timestamp, status, reason))

                if not is_up:
                    failed_pings_count += 1
                    send_alert(name, url_or_ip, reason) # Envoie l'email ET enregistre l'alerte en DB
                else:
                    failed_pings_count = 0 # Reset en cas de succès

                # Mise à jour de l'état dans la base
                query_update = """
                    UPDATE monitored_sites
                    SET last_status = %s,
                        last_checked = %s,
                        failed_pings_count = %s
                    WHERE id = %s
                """
                execute_query(query_update, (status, timestamp, failed_pings_count, site_id))

        conn.commit()
        print("--- Fin du cycle de surveillance ---")

    except pymysql.Error as e:
        print(f"Erreur pendant la surveillance : {e}")
    finally:
        close_db_connection(conn)

def run_monitoring_loop():
    print("Boucle de surveillance démarrée...")
    while True:
        monitor_all_sites()
        print("Pause de 60 secondes...\n")
        time.sleep(60)