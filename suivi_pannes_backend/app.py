from flask import Flask, render_template, request, redirect
import pymysql
from db import close_db_connection, get_db_connection, fetch_one, execute_query

app = Flask(__name__)

@app.route('/')
def dashboard():
    conn = get_db_connection()
    if not conn:
        return "Erreur de connexion à la base de données"

    sites = []
    events = []
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, url_or_ip, last_status, last_checked FROM monitored_sites")
            sites = cursor.fetchall()
            cursor.execute("SELECT s.name as site_name, e.timestamp, e.status, e.reason FROM monitoring_events e JOIN monitored_sites s ON e.site_id = s.id ORDER BY e.timestamp DESC LIMIT 10")
            events = cursor.fetchall()
    except pymysql.Error as e:
        print(f"Erreur lors de la récupération des données : {e}")
    finally:
        close_db_connection(conn)

    return render_template('dashboard.html', sites=sites, events=events, active_page='accueil')

@app.route('/add_site', methods=['POST'])
def add_site():
    name = request.form.get('name')
    url_or_ip = request.form.get('url_or_ip')
    if name and url_or_ip:
        execute_query("INSERT INTO monitored_sites (name, url_or_ip) VALUES (%s, %s)", (name, url_or_ip))
    return redirect('/')

@app.route('/toggle_site/<int:site_id>')
def toggle_site(site_id):
    execute_query("UPDATE monitored_sites SET enabled = NOT enabled WHERE id = %s", (site_id,))
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)