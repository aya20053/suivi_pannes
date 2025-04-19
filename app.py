from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from datetime import datetime, timedelta  # Ajoutez cette ligne en haut de votre fichier
from datetime import datetime, timedelta
import json
def get_db_connection():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='suivi_pannes_'  
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
        conn = get_db_connection()
        cursor = conn.cursor()

        # Statistiques de base
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM monitored_sites WHERE last_status = 'En ligne'")
        total_online = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM monitored_sites WHERE last_status = 'Hors ligne'")
        total_offline = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM monitored_sites")
        total_sites = cursor.fetchone()[0]

        cursor.execute("SELECT MAX(last_checked) FROM monitored_sites")
        last_check = cursor.fetchone()[0]

        # Récupérer les données pour les graphiques des 24 dernières heures
        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
        
        # Récupérer tous les sites surveillés avec leur état actuel
        cursor.execute("""
            SELECT ms.id, ms.name, ms.last_status, ms.last_checked
            FROM monitored_sites ms
        """)
        sites = cursor.fetchall()
        
        sites_data = []
        for site in sites:
            site_id, site_name, last_status, last_checked = site
            
            # Récupérer les événements des dernières 24 heures pour ce site
            cursor.execute("""
                SELECT timestamp, status 
                FROM monitoring_events 
                WHERE site_id = %s AND timestamp >= %s
                ORDER BY timestamp
            """, (site_id, twenty_four_hours_ago))
            
            events = cursor.fetchall()
            
            # Calculer les statistiques
            online_count = sum(1 for event in events if event[1] == 'En ligne')
            offline_count = len(events) - online_count
            availability = (online_count / len(events) * 100) if events else 0
            
            # Préparer les données pour le graphique
            timestamps = [event[0].strftime('%H:%M') for event in events]
            statuses = [1 if event[1] == 'En ligne' else 0 for event in events]
            
            # Données agrégées par heure pour un graphique plus lisible
            hourly_data = {}
            for event in events:
                hour = event[0].strftime('%H:00')
                status = 1 if event[1] == 'En ligne' else 0
                if hour not in hourly_data:
                    hourly_data[hour] = {'count': 0, 'sum': 0}
                hourly_data[hour]['count'] += 1
                hourly_data[hour]['sum'] += status
            
            hours = sorted(hourly_data.keys())
            hourly_ratios = [(hourly_data[hour]['sum'] / hourly_data[hour]['count'] * 100) 
                            for hour in hours]
            
            sites_data.append({
                'id': site_id,
                'name': site_name,
                'current_status': last_status,
                'last_checked': last_checked.strftime('%Y-%m-%d %H:%M:%S') if last_checked else 'N/A',
                'availability': round(availability, 2),
                'online_count': online_count,
                'offline_count': offline_count,
                'timestamps': timestamps,
                'statuses': statuses,
                'hourly_labels': hours,
                'hourly_ratios': hourly_ratios,
                'events_json': json.dumps([{
                    'timestamp': event[0].strftime('%Y-%m-%d %H:%M:%S'),
                    'status': event[1]
                } for event in events])
            })

        return render_template('dashboard.html', 
                           total_online=total_online, 
                           total_offline=total_offline,
                           total_sites=total_sites,
                           user_count=user_count,
                           last_check=last_check.strftime('%Y-%m-%d %H:%M:%S') if last_check else 'N/A',
                           sites_data=sites_data,
                           now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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
