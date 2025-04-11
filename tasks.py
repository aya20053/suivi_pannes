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
    return_code = subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"PING to {host}: Return code = {return_code}")
    return return_code == 0

def check_site_status(host):
    """Vérifie le statut d'un site web ou d'une IP en utilisant ping."""
    is_up = ping(host)
    reason = "Ping réussi" if is_up else "Ping échoué"
    print(f"Status check for {host}: {'UP' if is_up else 'DOWN'} - Reason: {reason}")
    return is_up, reason

def monitor_all_sites():
    """Surveille tous les sites web actifs dans la base de données."""
    print("--- Starting monitoring cycle ---")
    conn = get_db_connection()
    if not conn:
        print("Error: Could not connect to the database.")
        return

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, url_or_ip, failed_pings_count, alert_sent FROM monitored_sites WHERE enabled = 1")
            sites = cursor.fetchall()
            print(f"Found {len(sites)} sites to monitor.")

            for site in sites:
                site_id = site['id']
                name = site['name']
                url_or_ip = site['url_or_ip']
                failed_pings_count = site['failed_pings_count']
                alert_sent = site['alert_sent']
                print(f"Checking site: {name} ({url_or_ip})")

                is_up, reason = check_site_status(url_or_ip)
                timestamp = datetime.utcnow()

                # Enregistre l'événement
                query_insert = "INSERT INTO monitoring_events (site_id, timestamp, status, reason) VALUES (%s, %s, %s, %s)"
                values_insert = (site_id, timestamp, "En ligne" if is_up else "Hors ligne", reason)
                execute_query(query_insert, values_insert)
                print(f"  Event recorded: Status={'En ligne' if is_up else 'Hors ligne'}, Reason={reason}")

                if not is_up:
                    failed_pings_count += 1
                    if failed_pings_count >= 1 and not alert_sent:
                        send_alert(name, url_or_ip, reason)
                        execute_query("UPDATE monitored_sites SET alert_sent = 1 WHERE id = %s", (site_id,))
                        print(f"  ALERT sent for {name} ({url_or_ip}) - Reason: {reason}")
                else:
                    failed_pings_count = 0
                    execute_query("UPDATE monitored_sites SET alert_sent = 0 WHERE id = %s", (site_id,))

                query_update = "UPDATE monitored_sites SET last_status = %s, last_checked = %s, failed_pings_count = %s WHERE id = %s"
                values_update = ("En ligne" if is_up else "Hors ligne", timestamp, failed_pings_count, site_id)
                execute_query(query_update, values_update)
                print(f"  Site {name} updated in database.")

            conn.commit()
            print("--- Monitoring cycle finished ---")

    except pymysql.Error as e:
        print(f"Error during site monitoring: {e}")
    finally:
        close_db_connection(conn)

def send_alert(site_name, url_or_ip, reason):
    """Envoie une alerte par email et/ou notification."""
    subject = f"ALERTE: Site/IP '{site_name}' ({url_or_ip}) est hors ligne"
    body = f"Le site/l'IP '{site_name}' ({url_or_ip}) est actuellement hors ligne. Raison probable : {reason}. Dernière vérification : {datetime.utcnow()} (UTC)."

    print(f"DEBUG: About to call send_email for {site_name}")
    if EMAIL_CONFIG['enabled']:
        send_email(subject, body, EMAIL_CONFIG['recipients'], EMAIL_CONFIG)
        print("DEBUG: send_email function has returned")

    if NOTIFICATION_CONFIG['enabled']:
        print(f"Notification sent for: {site_name} - {reason}") # Remplacer par votre logique de notification

def run_monitoring_loop():
    print("Starting monitoring loop...")
    while True:
        monitor_all_sites()
        print(f"Sleeping for 60 seconds...")
        time.sleep(60)  # Vérifie toutes les 60 secondes (ajuster selon vos besoins)

if __name__ == "__main__":
    run_monitoring_loop()