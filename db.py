import pymysql

conn = pymysql.connect(
    host='localhost',  # Hôte de la base de données
    user='root',  # Nom d'utilisateur
    password='',  # Mot de passe
    database='suivi_pannes'  # Nom de la base de données
)



conn.close()