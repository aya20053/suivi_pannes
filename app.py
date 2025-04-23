
import os
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import pymysql
import json
import bcrypt  # For password hashing (commented out for now as per previous request)
import logging  # For better logging
import threading
from tasks import run_monitoring_loop

app = Flask(__name__)
CORS(app)

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Database Configuration ---
DB_HOST = 'localhost'  # Consider using environment variables for production
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'suivi_pannes_'

def get_db_connection():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        logging.error(f"Database connection error: {e}")
        return None

# --- Authentication ---
app.secret_key = 'your_secret_key'  # Important for session management

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user = cursor.fetchone()
        if user and user['password'] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Nom d'utilisateur ou mot de passe incorrect")
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- Home and Dashboard ---
@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    try:
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
            result = cursor.fetchone()
            last_check = result['MAX(last_checked)'] if result and result['MAX(last_checked)'] else None

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

            user = get_user(conn)
            return render_template('dashboard.html',
                                   total_online=total_online,
                                   total_offline=total_offline,
                                   total_sites=total_sites,
                                   user_count=user_count,
                                   last_check=last_check,
                                   sites_data=sites_data,
                                   now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                   user_role=user['role'] if user else 'unknown'
                                   )

    except pymysql.MySQLError as e:
        logging.error(f"Dashboard database error: {e}")
        return "An error occurred while fetching dashboard data", 500
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        return "An error occurred while fetching dashboard data", 500
    finally:
        conn.close()

# --- Other HTML Views ---
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
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    try:
        user = get_user(conn)
        if user:
            return render_template('profile.html', user=user)
        return redirect(url_for('index'))
    finally:
        conn.close()

# --- User Data Retrieval ---
def get_user(conn):
    username = session.get('username')
    if not username:
        return None

    try:
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
                    "role": user['role'],
                    "password": user['password'] # Include password
                }
            return None
    except pymysql.MySQLError as e:
        logging.error(f"Error fetching user: {e}")
        return None

# --- API Routes ---
@app.route("/api/sites", methods=["GET"])
def api_get_sites():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM monitored_sites")
            return jsonify(cursor.fetchall())
    except pymysql.MySQLError as e:
        logging.error(f"Error getting sites: {e}")
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/sites", methods=["POST"])
def api_add_site():
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO monitored_sites (name, url_or_ip) VALUES (%s, %s)",
                (data["name"], data["url_or_ip"])
            )
            conn.commit()
        return jsonify({"message": "Site added"}), 201
    except pymysql.MySQLError as e:
        logging.error(f"Error adding site: {e}")
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/sites/<int:id>", methods=["DELETE"])
def api_delete_site(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM monitored_sites WHERE id = %s", (id,))
            conn.commit()
        return jsonify({"message": "Site deleted"})
    except pymysql.MySQLError as e:
        logging.error(f"Error deleting site: {e}")
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/sites/<int:id>", methods=["GET"])
def get_site(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM monitored_sites WHERE id = %s", (id,))
            site = cursor.fetchone()
            if site:
                return jsonify(site), 200
            else:
                return jsonify({"error": "Site not found"}), 404
    except pymysql.MySQLError as e:
        logging.error(f"Error getting site details: {e}")
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/sites/<int:id>", methods=["PUT"])
def update_site(id):
    data = request.get_json()
    name = data.get("name")
    url_or_ip = data.get("url_or_ip")

    if not name or not url_or_ip:
        return jsonify({"error": "Missing fields"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM monitored_sites WHERE id = %s", (id,))
            if not cursor.fetchone():
                return jsonify({"error": "Site not found"}), 404

            cursor.execute("""
                UPDATE monitored_sites
                SET name = %s, url_or_ip = %s
                WHERE id = %s
            """, (name, url_or_ip, id))
            conn.commit()

        return jsonify({"message": "Site updated successfully"}), 200
    except pymysql.MySQLError as e:
        logging.error(f"Error updating site: {e}")
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

# --- User Management API ---
@app.route('/manage_users')
def manage_users():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('manage-users.html')

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/api/users", methods=["GET"])
def api_get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, prenom, email, poste, telephone, photo_profile, role, password FROM users") # Include password
            users = cursor.fetchall()
            return jsonify(users)
    except pymysql.MySQLError as e:
        logging.error(f"Error getting users: {e}")
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/users/<int:id>", methods=["GET"])
def api_get_user(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, prenom, email, poste, telephone, photo_profile, role, password FROM users WHERE id = %s", (id,)) # Include password
            user = cursor.fetchone()
            if user:
                return jsonify(user), 200
            else:
                return jsonify({"error": "User not found"}), 404
    except pymysql.MySQLError as e:
        logging.error(f"Error getting user: {e}")
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/users", methods=["POST"])
def api_add_user():
    data = request.get_json()
    logging.info(f"Données reçues pour l'ajout d'un utilisateur: {data}")
    username = data.get('username')
    prenom = data.get('prenom')
    email = data.get('email')
    poste = data.get('poste')
    telephone = data.get('telephone')
    password = data.get('password')
    role = data.get('role')

    if not all([username, prenom, email, password, role]):
        logging.error("Champs obligatoires manquants pour l'ajout d'un utilisateur.")
        return jsonify({'error': 'Tous les champs obligatoires doivent être remplis.'}), 400

    conn = get_db_connection()
    if not conn:
        logging.error("Erreur de connexion à la base de données lors de l'ajout d'un utilisateur.")
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    logging.warning(f"Tentative d'ajout d'un utilisateur avec un nom d'utilisateur existant: {username}")
                    return jsonify({'error': 'Nom d\'utilisateur déjà existant.'}), 409
                cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    logging.warning(f"Tentative d'ajout d'un utilisateur avec un email existant: {email}")
                    return jsonify({'error': 'Email déjà existant.'}), 409

                cursor.execute("""
                    INSERT INTO users (username, prenom, email, poste, telephone, password, role)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (username, prenom, email, poste, telephone, password, role))
                conn.commit()
                logging.info(f"Utilisateur '{username}' ajouté avec succès.")
                return jsonify({'message': 'Utilisateur ajouté avec succès.'}), 201
            except pymysql.MySQLError as e:
                logging.error(f"Erreur SQL lors de l'ajout d'un utilisateur: {e}")
                conn.rollback()
                return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/users/<int:id>", methods=["PUT"])
def api_update_user(id):
    data = request.get_json()
    username = data.get('username')
    prenom = data.get('prenom')
    email = data.get('email')
    poste = data.get('poste')
    telephone = data.get('telephone')
    password = data.get('password')
    role = data.get('role')

    if not all([username, prenom, email, role]):
        return jsonify({'error': 'Les champs nom, prénom, email et rôle sont obligatoires.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            # Check if the user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Utilisateur non trouvé.'}), 404

            # Check for duplicate username (excluding the current user)
            cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, id))
            if cursor.fetchone():
                return jsonify({'error': 'Nom d\'utilisateur déjà existant.'}), 409

            # Check for duplicate email (excluding the current user)
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, id))
            if cursor.fetchone():
                return jsonify({'error': 'Email déjà existant.'}), 409

            update_query = """
                UPDATE users
                SET username = %s, prenom = %s, email = %s, poste = %s,
                    telephone = %s, password = %s, role = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (username, prenom, email, poste, telephone, password, role, id))
            conn.commit()
        return jsonify({'message': 'Utilisateur mis à jour avec succès.'}), 200
    except pymysql.MySQLError as e:
        logging.error(f"Error updating user: {e}")
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

@app.route("/api/users/<int:id>", methods=["DELETE"])
def api_delete_user(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE id = %s", (id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Utilisateur non trouvé.'}), 404
            cursor.execute("DELETE FROM users WHERE id = %s", (id,))
            conn.commit()
        return jsonify({'message': 'Utilisateur supprimé avec succès.'}), 200
    except pymysql.MySQLError as e:
        logging.error(f"Error deleting user: {e}")
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        conn.close()

# --- File Upload Route (for profile picture) ---
@app.route('/api/profile/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return jsonify({'error': 'Non autorisé'}), 401

    if 'file' not in request.files:
        return jsonify({'error': 'Pas de fichier envoyé'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE users SET photo_profile = %s WHERE username = %s", (filename, session['username']))
                conn.commit()
            return jsonify({'message': 'Photo de profil mise à jour avec succès', 'filename': filename}), 200
        except pymysql.MySQLError as e:
            logging.error(f"Error updating profile picture: {e}")
            conn.rollback()
            return jsonify({'error': f"Database error: {e}"}), 500
        finally:
            conn.close()
    else:
        return jsonify({'error': 'Type de fichier non autorisé'}), 400


def start_monitoring():
    """Démarre la boucle de monitoring dans un thread séparé."""
    thread = threading.Thread(target=run_monitoring_loop)
    thread.daemon = True  # Permet au thread de s'arrêter lorsque l'application Flask s'arrête
    thread.start()


if __name__ == '__main__':
    start_monitoring()
    app.run(debug=True)