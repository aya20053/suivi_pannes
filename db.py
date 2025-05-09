import pymysql
from datetime import datetime, timedelta

def get_db_connection():
    """Établit et retourne une connexion à la base de données MySQL."""
    try:
        conn = pymysql.connect(
            host='localhost',  # Hôte de la base de données
            user='root',      # Nom d'utilisateur
            password='',      # Mot de passe
            database='suivi_pannes_',  # Nom de la base de données
            cursorclass=pymysql.cursors.DictCursor  # Pour retourner des dictionnaires
        )
        return conn
    except pymysql.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")
        return None

def close_db_connection(conn):
    """Ferme une connexion à la base de données MySQL."""
    if conn:
        conn.close()

def execute_query(query, params=()):
    """Exécute une requête SQL et retourne les résultats."""
    conn = get_db_connection()
    results = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            conn.commit()
            results = cursor.fetchall()
    except pymysql.Error as e:
        print(f"Erreur lors de l'exécution de la requête '{query}': {e}")
    finally:
        close_db_connection(conn)
    return results

def fetch_one(query, params=()):
    """Exécute une requête SQL et retourne la première ligne de résultat."""
    conn = get_db_connection()
    result = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
    except pymysql.Error as e:
        print(f"Erreur lors de l'exécution de la requête '{query}': {e}")
    finally:
        close_db_connection(conn)
    return result

def enregistrer_pdf(file_name, file_path):
    query = """
        INSERT INTO weekly_report (file_name, file_path)
        VALUES (%s, %s)
    """
    execute_query(query, (file_name, file_path))
def get_db_connection():
    """Retourne la connexion à la base de données."""
    return pymysql.connect(host='localhost', user='root', password='', database='suivi_pannes', cursorclass=pymysql.cursors.DictCursor)

def get_data_for_last_7_days(site_id):
    """Récupère les événements pour un site sur les 7 derniers jours."""
    seven_days_ago = datetime.now() - timedelta(days=7)

    # Connexion à la base de données
    conn = get_db_connection()
    cursor = conn.cursor()

    # Requête SQL pour récupérer les événements
    query = """
    SELECT status, timestamp 
    FROM monitoring_events 
    WHERE site_id = %s AND timestamp >= %s
    ORDER BY timestamp ASC
    """
    cursor.execute(query, (site_id, seven_days_ago))
    data = cursor.fetchall()

    # Fermer la connexion
    cursor.close()
    conn.close()

    return data
