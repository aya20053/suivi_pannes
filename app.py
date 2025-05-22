import os
from flask import Flask, g, jsonify, render_template, request, redirect, url_for, session, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import pymysql
import json
import logging  # For better logging
import threading
from tasks import run_monitoring_loop
from werkzeug.exceptions import BadRequest
import mysql.connector
from flask_cors import CORS
app = Flask(__name__)

CORS(app, supports_credentials=True, origins=["http://127.0.0.1:5000", "http://localhost:5000"])

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
            cursorclass=pymysql.cursors.DictCursor  # Ici uniquement
        )
        return conn
    except pymysql.MySQLError as e:
        logging.error(f"Database connection error: {e}")
        return None

# --- Authentication ---
app.secret_key = 'your_secret_key'  # Important for session management



@app.route('/')
def index():
   
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS count FROM monitored_sites WHERE last_status = 'En ligne'")
            total_online = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) AS count FROM monitored_sites WHERE last_status = 'Hors ligne'")
            total_offline = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) AS count FROM monitored_sites")
            total_sites = cursor.fetchone()['count']

            cursor.execute("SELECT MAX(last_checked) AS last_check FROM monitored_sites")
            result = cursor.fetchone()
            last_check = result['last_check'] if result and result['last_check'] else None

            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

            cursor.execute("SELECT id, name, url_or_ip,equipment_type, last_status, last_checked FROM monitored_sites")
            sites = cursor.fetchall()

            sites_data = []

            for site in sites:
                with conn.cursor() as cursor2:
                    cursor2.execute("""
                        SELECT timestamp, status FROM monitoring_events
                        WHERE site_id = %s AND timestamp >= %s ORDER BY timestamp
                    """, (site['id'], twenty_four_hours_ago))
                    events = cursor2.fetchall()

                online_count = sum(1 for e in events if e['status'] == 'En ligne')
                offline_count = len(events) - online_count
                availability = (online_count / len(events) * 100) if events else 0

                secondly_data = {}
                for e in events:
                    second = e['timestamp'].strftime('%H:%M:%S')
                    if second not in secondly_data:
                        secondly_data[second] = {'count': 0, 'sum': 0}
                    secondly_data[second]['count'] += 1
                    secondly_data[second]['sum'] += (1 if e['status'] == 'En ligne' else 0)

                seconds = sorted(secondly_data.keys())
                secondly_ratios = [
                    (secondly_data[s]['sum'] / secondly_data[s]['count']) * 100 for s in seconds
                ]

                sites_data.append({
                    'id': site['id'],
                    'name': site['name'],
                    'url_or_ip': site['url_or_ip'],
                    'equipment_type': site['equipment_type'],

                    'current_status': site['last_status'],
                    'last_checked': site['last_checked'].strftime('%Y-%m-%d %H:%M:%S') if site['last_checked'] else 'N/A',
                    'availability': round(availability, 2),
                    'online_count': online_count,
                    'offline_count': offline_count,
                    'hourly_labels': seconds,
                    'hourly_ratios': secondly_ratios,
                    'events_json': json.dumps([
                        {'timestamp': e['timestamp'].strftime('%Y-%m-%d %H:%M:%S'), 'status': e['status']}
                        for e in events
                    ])
                })

            user_role = session.get('role')
            return render_template('graphes.html',
                                total_online=total_online,
                                total_offline=total_offline,
                                total_sites=total_sites,
                                last_check=last_check,
                                sites_data=sites_data,
                                now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                user_role=user_role,
                                role=user_role)

    except Exception as e:
        logging.error(f"Erreur dashboard: {e}")
        return "Erreur serveur", 500
    finally:
        if conn:
            conn.close()

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
            session['role'] = user['role']  # Corrected: Access role directly from the 'user' dictionary
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Nom d utilisateur ou mot de passe incorrect")
    finally:
        if conn:
            conn.close()


@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')





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
            # Nombre d'utilisateurs
            cursor.execute("SELECT COUNT(*) AS count FROM users")
            user_count = cursor.fetchone()['count']

            # Sites en ligne
            cursor.execute("SELECT COUNT(*) AS count FROM monitored_sites WHERE last_status = 'En ligne'")
            total_online = cursor.fetchone()['count']

            # Sites hors ligne
            cursor.execute("SELECT COUNT(*) AS count FROM monitored_sites WHERE last_status = 'Hors ligne'")
            total_offline = cursor.fetchone()['count']

            # Nombre total de sites
            cursor.execute("SELECT COUNT(*) AS count FROM monitored_sites")
            total_sites = cursor.fetchone()['count']

            # Dernier contrôle effectué
            cursor.execute("SELECT MAX(last_checked) AS last_check FROM monitored_sites")
            result = cursor.fetchone()
            last_check = result['last_check'] if result and result['last_check'] else None

            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

            # Récupérer tous les sites
            cursor.execute("SELECT id, name, url_or_ip,equipment_type, last_status, last_checked FROM monitored_sites")
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

                # Calcul des ratios horaires
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
                    'url_or_ip': site['url_or_ip'],
                    'equipment_type': site['equipment_type'],
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

            user_role = session.get('role')
            return render_template('dashboard.html',
                                   total_online=total_online,
                                   total_offline=total_offline,
                                   total_sites=total_sites,
                                   user_count=user_count,
                                   last_check=last_check,
                                   sites_data=sites_data,
                                   now=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                   user_role=user_role,
                                   role=user_role)

    except pymysql.MySQLError as e:
        logging.error(f"Dashboard database error: {e}")
        return "An error occurred while fetching dashboard data", 500
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        return "An error occurred while fetching dashboard data", 500
    finally:
        if conn:
            conn.close()


@app.route('/api/user-role')
def get_user_role_api():
    role = session.get('role', 'visiteur')  # valeur par défaut
    return jsonify({'role': role})

@app.before_request
def before_request():
    # Vérifier si un utilisateur est connecté (session)
    g.user_role = session.get('role') # Store the role directly from the session
    # The database query to fetch the role is no longer needed here
    pass

# --- Other HTML Views ---
@app.route('/network-stats')
def network_stats():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('network_stats.html')

@app.route('/manage-networks')
def manage_networks():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('manage_networks.html', active_page='reseau')

@app.route('/profile')
def profile():
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    try:
        user_data = get_logged_in_user_data(conn)
        if user_data:
            return render_template('profile.html', user=user_data, active_page='profil')
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()

# --- User Data Retrieval ---
def get_logged_in_user_data(conn):
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
                    "password": user['password'] 
                }
            return None
    except pymysql.MySQLError as e:
        logging.error(f"Error fetching user data: {e}")
        return None

# --- API Routes ---
@app.route("/api/sites", methods=["GET"])
def api_get_sites():
    """Get all monitored sites"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM monitored_sites")
            sites = cursor.fetchall()
            # Convert datetime objects to strings
            for site in sites:
                if site.get('last_checked'):
                    site['last_checked'] = site['last_checked'].isoformat()
            return jsonify(sites), 200
    except pymysql.MySQLError as e:
        logging.error(f"Error getting sites: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/sites", methods=["POST"])
def api_add_site():
    """Add a new monitored site"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ['name', 'url_or_ip', 'equipment_type']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return jsonify({"error": f"Missing required fields: {', '.join(missing_fields)}"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cursor:
            # Check for duplicates
            cursor.execute(
                "SELECT id FROM monitored_sites WHERE name = %s OR url_or_ip = %s",
                (data["name"], data["url_or_ip"])
            )
            if cursor.fetchone():
                return jsonify({"error": "Site with this name or URL already exists"}), 409

            cursor.execute(
                "INSERT INTO monitored_sites (name, url_or_ip, equipment_type) VALUES (%s, %s, %s)",
                (data["name"], data["url_or_ip"], data["equipment_type"])
            )
            site_id = cursor.lastrowid
            conn.commit()
            
            # Return the newly created site
            cursor.execute("SELECT * FROM monitored_sites WHERE id = %s", (site_id,))
            new_site = cursor.fetchone()
            if new_site.get('last_checked'):
                new_site['last_checked'] = new_site['last_checked'].isoformat()
            
            return jsonify({
                "message": "Site added successfully",
                "site": new_site
            }), 201
    except pymysql.MySQLError as e:
        logging.error(f"Error adding site: {str(e)}")
        conn.rollback()
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/sites/<int:id>", methods=["DELETE"])
def api_delete_site(id):
    """Delete a monitored site"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cursor:
            # Check if site exists
            cursor.execute("SELECT id FROM monitored_sites WHERE id = %s", (id,))
            if not cursor.fetchone():
                return jsonify({"error": "Site not found"}), 404
            
            cursor.execute("DELETE FROM monitored_sites WHERE id = %s", (id,))
            conn.commit()
            return jsonify({"message": "Site deleted successfully"}), 200
    except pymysql.MySQLError as e:
        logging.error(f"Error deleting site {id}: {str(e)}")
        conn.rollback()
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/sites/<int:id>", methods=["GET"])
def get_site(id):
    """Get details of a specific site"""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM monitored_sites WHERE id = %s", (id,))
            site = cursor.fetchone()
            if not site:
                return jsonify({"error": "Site not found"}), 404
            
            # Convert datetime to string
            if site.get('last_checked'):
                site['last_checked'] = site['last_checked'].isoformat()
            
            return jsonify(site), 200
    except pymysql.MySQLError as e:
        logging.error(f"Error getting site {id}: {str(e)}")
        return jsonify({"error": "Database operation failed"}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/sites/<int:id>", methods=["PUT"])
def update_site(id):
    """Update a monitored site"""
    try:
        # Debug: Log the incoming request
        logging.debug(f"Update request for site {id}. Headers: {request.headers}, Data: {request.data}")
        
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Validate required fields
        required_fields = ['name', 'url_or_ip', 'equipment_type']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing": missing_fields
            }), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500

        try:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
                # Check if site exists
                cursor.execute("SELECT id FROM monitored_sites WHERE id = %s", (id,))
                if not cursor.fetchone():
                    return jsonify({"error": "Site not found"}), 404

                # Check for duplicates
                cursor.execute("""
                    SELECT id FROM monitored_sites 
                    WHERE (name = %s OR url_or_ip = %s) 
                    AND id != %s
                    LIMIT 1
                """, (data['name'], data['url_or_ip'], id))
                
                if duplicate := cursor.fetchone():
                    return jsonify({
                        "error": "Site with this name or URL already exists",
                        "duplicate_id": duplicate['id']
                    }), 409

                # Update site
                cursor.execute("""
                    UPDATE monitored_sites
                    SET name = %s, url_or_ip = %s, equipment_type = %s
                    WHERE id = %s
                """, (data['name'], data['url_or_ip'], data['equipment_type'], id))

                # Get updated site
                cursor.execute("""
                    SELECT id, name, url_or_ip, equipment_type, 
                           last_status, last_checked, failed_pings_count
                    FROM monitored_sites
                    WHERE id = %s
                """, (id,))
                
                site = cursor.fetchone()
                conn.commit()

                # Safely format dates
                if site['last_checked']:
                    try:
                        site['last_checked'] = site['last_checked'].isoformat()
                    except AttributeError:
                        site['last_checked'] = None

                return jsonify({
                    "message": "Site updated successfully",
                    "site": site
                }), 200

        except pymysql.MySQLError as e:
            logging.error(f"Database error in update_site: {str(e)}", exc_info=True)
            conn.rollback()
            return jsonify({
                "error": "Database operation failed",
                "details": str(e)
            }), 500
        finally:
            if conn:
                conn.close()

    except Exception as e:
        logging.error(f"Unexpected error in update_site: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500





       # Route pour créer une architecture

@app.route('/api/architectures', methods=['POST', 'OPTIONS'])
def create_architecture():
    if request.method == 'OPTIONS':
        return _build_cors_preflight_response()
    
    conn = None
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"status": "error", "message": "Nom manquant"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()  # simple, sans argument

        # 1. Insertion de l'architecture
        cursor.execute("""
            INSERT INTO network_architectures (name, description)
            VALUES (%s, %s)
        """, (data['name'], data.get('description', '')))
        arch_id = cursor.lastrowid

        # 2. Insertion des connexions
        if 'connections' in data:
            for conn_data in data['connections']:
                cursor.execute("""
                    INSERT INTO site_connections 
                    (architecture_id, source_site_id, target_site_id, connection_type, bandwidth)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    arch_id,
                    conn_data['source_id'],
                    conn_data['target_id'],
                    conn_data.get('type', 'standard'),
                    conn_data.get('bandwidth', 0)
                ))

        conn.commit()
        return _corsify(jsonify({
            "status": "success",
            "id": arch_id,
            "message": "Architecture créée"
        })), 201

    except Exception as e:
        if conn: conn.rollback()
        return _corsify(jsonify({
            "status": "error",
            "message": str(e)
        })), 500
    finally:
        if conn: conn.close()

# Utilitaires CORS
def _build_cors_preflight_response():
    response = jsonify({"status": "ok"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response

def _corsify(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response
@app.route('/api/architectures', methods=['POST'])
def save_architecture():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    connections = data.get('connections', [])

    conn = get_db_connection()
    if not conn:
        return jsonify({"message": "Database connection error"}), 500

    try:
        cursor = conn.cursor()  # Sans argument ici
        sql = "INSERT INTO architectures (name, description) VALUES (%s, %s)"
        cursor.execute(sql, (name, description))
        architecture_id = cursor.lastrowid

        for c in connections:
            sql_conn = """INSERT INTO connections (architecture_id, source_id, target_id, type, bandwidth)
                          VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql_conn, (
                architecture_id,
                c.get('source_id'),
                c.get('target_id'),
                c.get('type', 'standard'),
                c.get('bandwidth', 0)
            ))

        conn.commit()
        return jsonify({"message": "Architecture saved", "id": architecture_id}), 201
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde : {e}")
        return jsonify({"message": "Server error"}), 500
    finally:
        cursor.close()
        conn.close()

            
@app.route('/api/architectures', methods=['GET'])
def debug_architectures():
    try:
        conn = get_db_connection()
        cur = conn.cursor()    
        cur.execute("""
            SELECT a.*, 
                   COUNT(c.id) as connections_count
            FROM network_architectures a
            LEFT JOIN site_connections c ON a.id = c.architecture_id
            GROUP BY a.id
        """)
        results = cur.fetchall()
        return jsonify({
            "status": "success",
            "count": len(results),
            "data": results
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Route pour récupérer une architecture avec ses connexions
@app.route('/api/architectures/<int:arch_id>', methods=['GET'])
def get_architecture(arch_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Récupérer l'architecture de base
        cursor.execute("""
            SELECT * FROM network_architectures WHERE id = %s
        """, (arch_id,))
        arch = cursor.fetchone()
        
        if not arch:
            return jsonify({'error': 'Architecture non trouvée'}), 404
        
        # 2. Récupérer les connexions avec les détails des sites
        cursor.execute("""
            SELECT 
                sc.*,
                src.name as source_name, src.equipment_type as source_type,
                tgt.name as target_name, tgt.equipment_type as target_type
            FROM site_connections sc
            JOIN monitored_sites src ON sc.source_site_id = src.id
            JOIN monitored_sites tgt ON sc.target_site_id = tgt.id
            WHERE sc.architecture_id = %s
        """, (arch_id,))
        
        connections = cursor.fetchall()
        
        return jsonify({
            **arch,
            'connections': connections
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()


@app.route('/api/architectures-with-details', methods=['GET'])
def get_architectures_with_details():
    try:
        conn = get_db_connection()  # Utilisez votre méthode de connexion
        cur = conn.cursor()
        
        # Requête débogage
        print("Tentative d'exécution de la requête SQL...")
        
        cur.execute("""
            SELECT 
                a.id as arch_id,
                a.name as arch_name,
                a.description,
                c.id as connection_id,
                c.connection_type,
                c.bandwidth,
                src.id as source_id,
                src.name as source_name,
                src.equipment_type as source_type,
                tgt.id as target_id,
                tgt.name as target_name,
                tgt.equipment_type as target_type
            FROM network_architectures a
            LEFT JOIN site_connections c ON a.id = c.architecture_id
            LEFT JOIN monitored_sites src ON c.source_site_id = src.id
            LEFT JOIN monitored_sites tgt ON c.target_site_id = tgt.id
            ORDER BY a.id, c.id
        """)
        
        rows = cur.fetchall()
        print(f"Nombre de lignes récupérées : {len(rows)}")  # Debug
        
        # Structuration des données
        architectures = {}
        for row in rows:
            arch_id = row['arch_id']
            
            if arch_id not in architectures:
                architectures[arch_id] = {
                    'id': arch_id,
                    'name': row['arch_name'],
                    'description': row['description'],
                    'connections': []
                }
            
            if row['connection_id']:
                architectures[arch_id]['connections'].append({
                    'id': row['connection_id'],
                    'type': row['connection_type'],
                    'bandwidth': row['bandwidth'],
                    'source': {
                        'id': row['source_id'],
                        'name': row['source_name'],
                        'type': row['source_type']
                    },
                    'target': {
                        'id': row['target_id'],
                        'name': row['target_name'],
                        'type': row['target_type']
                    }
                })
        
        return jsonify({
            "status": "success",
            "data": list(architectures.values())
        })
        
    except Exception as e:
        print(f"ERREUR SERVEUR: {str(e)}")  # Log détaillé
        return jsonify({
            "status": "error",
            "message": f"Erreur serveur: {str(e)}",
            "details": str(e)  # Retourne l'erreur au frontend pour débogage
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

# --- User Management API ---
@app.route('/manage_users')
def manage_users():
    if 'username' not in session:
        return redirect(url_for('index'))

    if session.get('role') != 'chef admin':
        return render_template('erreur.html')  # Utilise render_template pour afficher une page HTML

    return render_template('manage-users.html', active_page='gestion-utilisateurs')

@app.route("/api/users", methods=["GET"])
def api_get_users():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, prenom, email, poste, telephone, photo_profile, role, password FROM users")
            users = cursor.fetchall()
            return jsonify(users)
    except pymysql.MySQLError as e:
        logging.error(f"Error getting users: {e}")
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        if conn:
            conn.close()

@app.route("/api/users/<int:id>", methods=["GET"])
def api_get_user(id):
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, username, prenom, email, poste, telephone, photo_profile, role, password FROM users WHERE id = %s", (id,))
            user = cursor.fetchone()
            if user:
                return jsonify(user), 200
            else:
                return jsonify({"error": "User not found"}), 404
    except pymysql.MySQLError as e:
        logging.error(f"Error getting user: {e}")
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        if conn:
            conn.close()
# Configuration
@app.route("/api/users", methods=["POST"])
def api_add_user():
    data = request.get_json()
    username = data.get('username')
    prenom = data.get('prenom')
    email = data.get('email')
    poste = data.get('poste')
    telephone = data.get('telephone')
    password = data.get('password')
    role = data.get('role')

    logging.info(f"Données reçues pour l'ajout d'un utilisateur: {username}, {email}, {role}")

    # Vérification des champs obligatoires
    if not all([username, prenom, email, password, role]):
        logging.error("Champs obligatoires manquants pour l'ajout d'un utilisateur.")
        return jsonify({'error': 'Tous les champs obligatoires doivent être remplis.'}), 400

    conn = get_db_connection()
    if not conn:
        logging.error("Erreur de connexion à la base de données.")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            # Vérifier unicité du username
            cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                logging.warning(f"Nom d'utilisateur existant: {username}")
                return jsonify({'error': 'Nom d\'utilisateur déjà existant.'}), 409

            # Vérifier unicité de l'email
            cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                logging.warning(f"Email existant: {email}")
                return jsonify({'error': 'Email déjà existant.'}), 409

            # Insertion dans la BDD (sans photo_profile)
            cursor.execute("""
                INSERT INTO users (username, prenom, email, poste, telephone, password, role)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (username, prenom, email, poste, telephone, password, role))

            conn.commit()
            logging.info(f"Utilisateur '{username}' ajouté avec succès.")
            return jsonify({'message': 'Utilisateur ajouté avec succès.'}), 201

    except pymysql.MySQLError as e:
        logging.error(f"Erreur SQL : {e}")
        conn.rollback()
        return jsonify({"error": f"Erreur SQL : {e}"}), 500
    finally:
        if conn:
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
        if conn:
            conn.close()
@app.route("/api/users/<int:id>", methods=["PUT"])
def api_update_user(id):
    data = request.get_json()
    username = data.get('username')
    prenom = data.get('prenom')
    email = data.get('email')
    poste = data.get('poste')
    telephone = data.get('telephone')
    password = data.get('password')  # Peut être vide
    role = data.get('role')

    if not all([username, prenom, email, role]):
        return jsonify({'error': 'Les champs username, prenom, email et role sont obligatoires.'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            # Vérifier si l'utilisateur existe
            cursor.execute("SELECT id FROM users WHERE id = %s", (id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Utilisateur non trouvé.'}), 404

            # Vérifier unicité du username
            cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (username, id))
            if cursor.fetchone():
                return jsonify({'error': 'Nom d\'utilisateur déjà existant.'}), 409

            # Vérifier unicité de l'email
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, id))
            if cursor.fetchone():
                return jsonify({'error': 'Email déjà existant.'}), 409

            # Construire la requête UPDATE dynamiquement
            if password:
                update_query = """
                    UPDATE users
                    SET username = %s, prenom = %s, email = %s, poste = %s,
                        telephone = %s, password = %s, role = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (username, prenom, email, poste, telephone, password, role, id))
            else:
                update_query = """
                    UPDATE users
                    SET username = %s, prenom = %s, email = %s, poste = %s,
                        telephone = %s, role = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (username, prenom, email, poste, telephone, role, id))

            conn.commit()
        return jsonify({'message': 'Utilisateur mis à jour avec succès.'}), 200

    except pymysql.MySQLError as e:
        logging.error(f"Erreur SQL lors de la mise à jour: {e}")
        conn.rollback()
        return jsonify({"error": f"Erreur SQL : {e}"}), 500
    finally:
        if conn:
            conn.close()


def get_user_role(conn):
    username = session.get('username')  # Récupérer le nom d'utilisateur depuis la session
    if not username:
        return None

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT role FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user:
                return user['role']  # Retourner seulement le rôle
            return None
    except pymysql.MySQLError as e:
        print(f"Erreur lors de la récupération de l'utilisateur : {e}")
        return None


def start_monitoring():
    """Démarre la boucle de monitoring dans un thread séparé."""
    thread = threading.Thread(target=run_monitoring_loop)
    thread.daemon = True  # Permet au thread de s'arrêter lorsque l'application Flask s'arrête
    thread.start()

@app.route('/alerts')
def alerts():
    """Route pour afficher la page des alertes."""
    if 'username' not in session:
        return redirect(url_for('index'))  # Redirige vers la page d'accueil si non connecté
    return render_template('alerts.html', active_page='Alertes')

@app.route("/api/alerts", methods=["GET"])
def api_get_alerts():
    """API endpoint pour récupérer les alertes au format JSON."""
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, timestamp, site_name, url_or_ip, reason FROM alerts ORDER BY timestamp DESC")
            alerts = cursor.fetchall()
            # Formatter la date pour l'affichage (optionnel)
            formatted_alerts = [{**alert, 'timestamp': alert['timestamp'].isoformat() + 'Z'} for alert in alerts]
            return jsonify(formatted_alerts)
    except pymysql.MySQLError as e:
        logging.error(f"Error getting alerts: {e}")
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        if conn:  # Vérifiez si la connexion existe avant de la fermer
            conn.close()


@app.route('/api/alerts', methods=['DELETE'])
def delete_all_alerts():
    try:
        connection= get_db_connection()
        cursor = connection.cursor()
        cursor.execute("TRUNCATE TABLE alerts")
        connection.commit()
        return jsonify({'message': 'Toutes les alertes ont été supprimées'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    try:
        connection= get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM alerts WHERE id = %s", (alert_id,))
        connection.commit()
        return jsonify({'message': 'Alerte supprimée'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


@app.route('/generer')
def generer():
    if 'username' not in session:
        return redirect(url_for('index'))

   
    return render_template('generer_arch.html', active_page='generer')


# Gestion des équipements
@app.route('/api/network/devices', methods=['GET', 'POST'])
def handle_devices():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        if request.method == 'GET':
            # Récupérer tous les équipements
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM network_devices")
                devices = cursor.fetchall()
                return jsonify(devices)
        
        elif request.method == 'POST':
            # Ajouter un nouvel équipement
            data = request.json
            required_fields = ['name', 'device_type']
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing required fields"}), 400
            
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO network_devices (name, ip_address, device_type, position_x, position_y) VALUES (%s, %s, %s, %s, %s)",
                    (data['name'], 
                     data.get('ip_address'), 
                     data['device_type'], 
                     data.get('position_x', 0), 
                     data.get('position_y', 0))
                )
                conn.commit()
                return jsonify({"message": "Device added", "id": cursor.lastrowid}), 201
    
    except pymysql.MySQLError as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        if conn:
            conn.close()
@app.route('/api/network/device-types', methods=['GET'])
def get_device_types():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT device_type FROM network_devices")
            types = [item['device_type'] for item in cursor.fetchall()]
            return jsonify(types)
    except pymysql.MySQLError as e:
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        if conn:
            conn.close()

            
# Gestion des connexions
@app.route('/api/network/connections', methods=['GET', 'POST'])
def handle_connections():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    
    try:
        if request.method == 'GET':
            # Récupérer toutes les connexions
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT c.*, 
                           s.name as source_name, 
                           t.name as target_name 
                    FROM network_connections c
                    JOIN network_devices s ON c.source_device_id = s.id
                    JOIN network_devices t ON c.target_device_id = t.id
                """)
                connections = cursor.fetchall()
                return jsonify(connections)
        
        elif request.method == 'POST':
            # Ajouter une nouvelle connexion
            data = request.json
            required_fields = ['source_device_id', 'target_device_id']
            if not all(field in data for field in required_fields):
                return jsonify({"error": "Missing required fields"}), 400
            
            # Vérifier que les devices existent
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM network_devices WHERE id IN (%s, %s)", 
                             (data['source_device_id'], data['target_device_id']))
                devices = cursor.fetchall()
                if len(devices) != 2:
                    return jsonify({"error": "One or both devices not found"}), 404
                
                # Vérifier que la connexion n'existe pas déjà
                cursor.execute("""
                    SELECT id FROM network_connections 
                    WHERE (source_device_id = %s AND target_device_id = %s)
                    OR (source_device_id = %s AND target_device_id = %s)
                """, (data['source_device_id'], data['target_device_id'],
                     data['target_device_id'], data['source_device_id']))
                if cursor.fetchone():
                    return jsonify({"error": "Connection already exists"}), 400
                
                # Créer la connexion
                cursor.execute(
                    "INSERT INTO network_connections (source_device_id, target_device_id, connection_type) VALUES (%s, %s, %s)",
                    (data['source_device_id'], 
                     data['target_device_id'], 
                     data.get('connection_type', 'ethernet'))
                )
                conn.commit()
                return jsonify({"message": "Connection added", "id": cursor.lastrowid}), 201
    
    except pymysql.MySQLError as e:
        conn.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500
    finally:
        if conn:
            conn.close()
@app.route('/settings')
def settings():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupère tous les utilisateurs
        cursor.execute("SELECT id, email FROM users")
        users = cursor.fetchall()
        
        # Récupère les emails de destination
        cursor.execute("SELECT id, email FROM destination_email")
        destinataires = cursor.fetchall()
        
        return render_template('settings.html', 
                           users=users, 
                           destinataires=destinataires)
        
    except Exception as e:
        flash(f"Erreur de base de données: {str(e)}", 'error')
        return render_template('settings.html', users=[], destinataires=[])
    finally:
        if cursor:
            cursor.close()
            conn.close()
@app.route('/employe/<email>')
def gestion_employe(email):
    # Exemple : récupérer l'employé par email depuis la base MySQL
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            employe = cursor.fetchone()
            if not employe:
                return "Employé non trouvé", 404
            return render_template("manage-users.html", email=email, employe=employe)
    finally:
        if conn:
            conn.close()

@app.route('/save_emails', methods=['POST'])
def save_emails():
    conn = None
    cursor = None
    try:
        selected_email = request.form.get('email_select')
        
        if not selected_email:
            flash("Aucun email sélectionné", 'warning')
            return redirect(url_for('settings'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Vérifier si l'email existe dans users
        cursor.execute("SELECT id FROM users WHERE email = %s", (selected_email,))
        if not cursor.fetchone():
            flash("Email non trouvé dans la base des utilisateurs", 'error')
            return redirect(url_for('settings'))
        
        # Insérer dans destination_email
        cursor.execute("""
            INSERT INTO destination_email (email) 
            VALUES (%s)
            ON DUPLICATE KEY UPDATE email = VALUES(email)
        """, (selected_email,))
        
        conn.commit()
        flash("Email ajouté aux destinataires avec succès!", 'success')
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Erreur lors de l'enregistrement: {str(e)}", 'error')
    finally:
        if cursor:
            cursor.close()
      
            conn.close()
    
    return redirect(url_for('settings'))

@app.route('/supprimer', methods=['POST'])
def supprimer():
    conn = None
    cursor = None
    try:
        email_id = request.form.get('email_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM destination_email WHERE id = %s", (email_id,))
        conn.commit()
        flash("Email supprimé des destinataires avec succès!", 'success')
        
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Erreur lors de la suppression: {str(e)}", 'error')
    finally:
        if cursor:
            cursor.close()
       
            conn.close()
    
    return redirect(url_for('settings'))


if __name__ == '__main__':
    from tasks import run_monitoring_loop
    import threading

    def start_monitoring():
       
        thread = threading.Thread(target=run_monitoring_loop)
        thread.daemon = True
        thread.start()

    #start_monitoring()
    app.run(debug=True)