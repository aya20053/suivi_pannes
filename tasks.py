import subprocess
import platform
from datetime import datetime
import time

import pymysql
from db import get_db_connection, close_db_connection, execute_query
from utils import send_email
from config import EMAIL_CONFIG, NOTIFICATION_CONFIG

def ping(host):
    """Effectue un ping sur l'hôte et retourne True si réussi, False sinon."""
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', host]
    return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def check_site_status(host):
    """Vérifie le statut d'un site web ou d'une IP en utilisant ping."""
    is_up = ping(host)
    reason = "Ping réussi" if is_up else "Ping échoué"
    return is_up, reason

def send_alert(site_name, url_or_ip, reason):
    """Envoie une alerte par email et/ou notification."""
    subject = f"ALERTE: Site/IP '{site_name}' ({url_or_ip}) est hors ligne"
    body = f"Le site/l'IP '{site_name}' ({url_or_ip}) est actuellement hors ligne.\n\nRaison : {reason}\nDernière vérification : {datetime.utcnow()} (UTC)."

    if EMAIL_CONFIG['enabled']:
        send_email(subject, body, EMAIL_CONFIG['recipients'], EMAIL_CONFIG)
        print(f"Email envoyé pour {site_name}")

    if NOTIFICATION_CONFIG['enabled']:
        print(f"Notification envoyée pour : {site_name} - {reason}")  # À remplacer par ta logique de notif réelle

def monitor_all_sites():
    """Surveille tous les sites web actifs dans la base de données."""
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
                    send_alert(name, url_or_ip, reason)  # Envoie toujours une alerte
                else:
                    failed_pings_count = 0  # Reset en cas de succès

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

