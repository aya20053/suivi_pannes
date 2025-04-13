import pymysql

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