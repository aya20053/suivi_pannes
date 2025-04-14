from flask import Flask, render_template, request, redirect, url_for, session
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
app.secret_key = 'ton_secret_key'  # N'oublie pas de définir une clé secrète pour la gestion des sessions

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
    if users and users[2] == password:  # users[2] représente le mot de passe dans la table Users
        session['username'] = username  # Enregistrer l'utilisateur dans la session
        return redirect(url_for('dashboard'))  # Redirige vers la page du tableau de bord après une connexion réussie
    else:
        return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect")

    cursor.close()
    conn.close()


@app.route('/home')
def home():
    return render_template('home.html')  # Page d'accueil après connexion réussie

if __name__ == '_main_':    app.run(debug=True)
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirige vers la page de login si non connecté
    return render_template('dashboard.html')  # Page du tableau de bord

@app.route('/network-stats')
def network_stats():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirige vers la page de login si non connecté
    return render_template('network_stats.html')  # Page des statistiques réseau

@app.route('/alerts')
def alerts():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirige vers la page de login si non connecté
    return render_template('alerts.html')  # Page des alertes

@app.route('/manage-networks')
def manage_networks():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirige vers la page de login si non connecté
    return render_template('manage_networks.html')  # Page de gestion des réseaux

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirige vers la page de login si non connecté
    return render_template('profile.html', username=session['username'])  # Page du profil avec le nom de l'utilisateur

@app.route('/logout')
def logout():
    session.pop('username', None)  # Supprime l'utilisateur de la session
    return redirect(url_for('index'))  # Redirige vers la page de login

if __name__ == '__main__':
    app.run(debug=True)
