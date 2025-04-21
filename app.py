from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_cors import CORS
from datetime import datetime, timedelta
import pymysql
import json

app = Flask(__name__)
app.secret_key = 'ton_secret_key'
CORS(app)

# ---------- Connexion à la base de données ----------
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='suivi_pannes_',
        cursorclass=pymysql.cursors.DictCursor
    )

# ---------- Authentification ----------
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
    if user and user['password'] == password:
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------- Page d'accueil ----------
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('home.html')

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()['COUNT(*)']

                cursor.execute("SELECT COUNT(*) FROM monitored_sites WHERE last_status = 'En ligne'")
                total_online = cursor.fetchone()['COUNT(*)']

                cursor.execute("SELECT COUNT(*) FROM monitored_sites WHERE last_status = 'Hors ligne'")
                total_offline = cursor.fetchone()['COUNT(*)']

                cursor.execute("SELECT COUNT(*) FROM monitored_sites")
                total_sites = cursor.fetchone()['COUNT(*)']

                cursor.execute("SELECT MAX(last_checked) FROM monitored_sites")
                last_check = cursor.fetchone()['MAX(last_checked)']

                twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

                cursor.execute("SELECT id, name, last_status, last_checked FROM monitored_sites")
                sites = cursor.fetchall()

                sites_data = []

                for site in sites:
                    cursor.execute("""
                        SELECT timestamp, status FROM monitoring_events 
                        WHERE site_id = %s AND timestamp >= %s ORDER BY timestamp
                    """, (site['id'], twenty_four_hours_ago))
                    events = cursor.fetchall()

                    online_count = sum(1 for e in events if e['status'] == 'En ligne')
                    offline_count = len(events) - online_count
                    availability = (online_count / len(events) * 100) if events else 0

                    hourly_data = {}
                    for e in events:
                        hour = e['timestamp'].strftime('%H:00')
                        if hour not in hourly_data:
                            hourly_data[hour] = {'count': 0, 'sum': 0}
                        hourly_data[hour]['count'] += 1
                        hourly_data[hour]['sum'] += (1 if e['status'] == 'En ligne' else 0)

                    hours = sorted(hourly_data.keys())
                    hourly_ratios = [(hourly_data[h]['sum'] / hourly_data[h]['count']) * 100 for h in hours]

                    sites_data.append({
                        'id': site['id'],
                        'name': site['name'],
                        'current_status': site['last_status'],
                        'last_checked': site['last_checked'].strftime('%Y-%m-%d %H:%M:%S') if site['last_checked'] else 'N/A',
                        'availability': round(availability, 2),
                        'online_count': online_count,
                        'offline_count': offline_count,
                        'hourly_labels': hours,
                        'hourly_ratios': hourly_ratios,
                        'events_json': json.dumps([
                            {'timestamp': e['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 'status': e['status']}
                            for e in events
                        ])
                    })

        user = get_user()
        return render_template('dashboard.html',
            total_online=total_online,
            total_offline=total_offline,
            total_sites=total_sites,
            user_count=user_count,
            last_check=last_check.strftime('%Y-%m-%d %H:%M:%S') if last_check else 'N/A',
            sites_data=sites_data,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            user_role=user['role'] if user else 'unknown'
        )

    except Exception as e:
        app.logger.error(f"Erreur dans le rendu de la page : {e}")
        return "Une erreur est survenue.", 500

# ---------- Autres vues HTML ----------
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

@app.route('/profile')
def profile():
    user = get_user()
    if user:
        return render_template('profile.html', user=user)
    return redirect(url_for('index'))

# ---------- Données utilisateur ----------
def get_user():
    username = session.get('username')
    if not username:
        return None

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                return {
                    "id": user['id'],
                    "username": user['username'],
                    "prenom": user['prenom'],
                    "email": user['email'],
                    "poste": user['poste'],
                    "telephone": user['telephone'],
                    "photo_profile": user['photo_profile'],
                    "role": user['role']
                }
    return None

# ---------- API REST ----------
@app.route("/api/sites", methods=["GET"])
def api_get_sites():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM monitored_sites")
            return jsonify(cursor.fetchall())

@app.route("/api/sites", methods=["POST"])
def api_add_site():
    data = request.json
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO monitored_sites (name, url_or_ip) VALUES (%s, %s)",
                (data["name"], data["url_or_ip"])
            )
            conn.commit()
    return jsonify({"message": "Site ajouté"}), 201

@app.route("/api/sites/<int:id>", methods=["DELETE"])
def api_delete_site(id):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM monitored_sites WHERE id = %s", (id,))
            conn.commit()
    return jsonify({"message": "Site supprimé"})

# ---------- Obtenir les détails d’un site ----------
@app.route("/api/sites/<int:id>", methods=["GET"])
def get_site(id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM monitored_sites WHERE id = %s", (id,))
                site = cursor.fetchone()
                if site:
                    return jsonify(site), 200
                else:
                    return jsonify({"error": "Site non trouvé"}), 404
    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500

# ---------- Mettre à jour un site ----------
@app.route("/api/sites/<int:id>", methods=["PUT"])
def update_site(id):
    try:
        data = request.get_json()
        name = data.get("name")
        url_or_ip = data.get("url_or_ip")

        if not name or not url_or_ip:
            return jsonify({"error": "Champs manquants"}), 400

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Vérifier si le site existe
                cursor.execute("SELECT id FROM monitored_sites WHERE id = %s", (id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Site non trouvé"}), 404

                # Mettre à jour
                cursor.execute("""
                    UPDATE monitored_sites
                    SET name = %s, url_or_ip = %s
                    WHERE id = %s
                """, (name, url_or_ip, id))
                conn.commit()

        return jsonify({"message": "Site mis à jour avec succès"}), 200

    except Exception as e:
        return jsonify({"error": f"Erreur serveur : {str(e)}"}), 500

# ---------- Lancer l'application ----------
if __name__ == '__main__':
    app.run(debug=True)