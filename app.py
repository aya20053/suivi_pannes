from flask import Flask, render_template, request, redirect, url_for, session
import pymysql

def get_db_connection():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='suivi_pannes_'  # ⚠️ Vérifie bien le nom exact de ta BDD
    )
    return conn

app = Flask(__name__)
app.secret_key = 'ton_secret_key'

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Users WHERE username = %s', (username,))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    # Assure-toi que l'indice utilisé ici correspond au champ mot de passe
    if user and user[7] == password:  # Ajuste l'indice en fonction de la structure de ta table
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect")

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    try:
        # Connexion à la base de données
        conn = get_db_connection()
        cursor = conn.cursor()

        # Requête pour récupérer le nombre d'utilisateurs
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        # Requête pour récupérer les autres statistiques
        cursor.execute("SELECT COUNT(*) FROM monitored_sites WHERE last_status = 'En ligne'")
        total_online = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM monitored_sites WHERE last_status = 'Hors ligne'")
        total_offline = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM monitored_sites")
        total_sites = cursor.fetchone()[0]

        # Dernière vérification (à adapter selon ta logique)
        cursor.execute("SELECT MAX(last_checked) FROM monitored_sites")
        last_check = cursor.fetchone()[0]

        return render_template('dashboard.html', 
                               total_online=total_online, 
                               total_offline=total_offline,
                               total_sites=total_sites,
                               user_count=user_count,  # Ajouter le nombre d'utilisateurs
                               last_check=last_check)
    except Exception as e:
        app.logger.error(f"Erreur dans le rendu de la page : {e}")
        return "Une erreur est survenue. Veuillez réessayer plus tard.", 500

@app.route('/network-stats')
def network_stats():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('network_stats.html')

@app.route('/alerts')
def alerts():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('alerts.html')

@app.route('/manage-networks')
def manage_networks():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('manage_networks.html')

def get_user():
    # Utilisation de la connexion à la base de données avec l'utilisateur en session
    conn = get_db_connection()
    cursor = conn.cursor()

    username = session.get('username')
    if username:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "id": row[0],
                "username": row[1],
                "prenom": row[2],
                "email": row[3],
                "poste": row[4],
                "telephone": row[5],
                "photo_profile": row[6]
            }
    return None



@app.route('/profile')
def profile():
    user = get_user()
    if user:
        return render_template('profile.html', user=user)
    return redirect(url_for('index'))




@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))

# ✅ C’est bien "__main__" ici
if __name__ == '__main__':
    app.run(debug=True)
