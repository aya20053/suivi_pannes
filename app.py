from flask import Flask, render_template, request, redirect, url_for
import pymysql

def get_db_connection():
    conn = pymysql.connect(
        host='localhost',  # Hôte de la base de données
        user='root',  # Nom d'utilisateur
        password='',  # Mot de passe
        database='suivi_pannes_'  # Nom de la base de données
    )
    return conn

app = Flask(__name__) 


@app.route('/')
def index():
    return render_template('login.html')  # Page de login

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Connexion à la base de données
    conn = get_db_connection()
    cursor = conn.cursor()

    # Requête SQL pour vérifier si l'utilisateur existe
    cursor.execute('SELECT * FROM Users WHERE username = %s', (username,))
    users = cursor.fetchone()  # Retourne le premier utilisateur correspondant

    # Vérification si l'utilisateur existe et si le mot de passe est correct
    if users and users[2] == password:  # user[2] représente le mot de passe dans la table User
        return redirect(url_for('home'))  # Redirige vers la page d'accueil après une connexion réussie
    else:
        return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect")

    # Fermer la connexion et le curseur
    cursor.close()
    conn.close()

@app.route('/home')
def home():
    return render_template('home.html')  # Page d'accueil après connexion réussie

if __name__ == '_main_':    app.run(debug=True)