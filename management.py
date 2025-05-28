from flask import Blueprint, render_template, request, jsonify
from database_manager import DatabaseManager, DatabaseConfig
import subprocess
import platform

management_bp = Blueprint('management', __name__)
db_manager = DatabaseManager()

@management_bp.route('/')
def management():
    return render_template('management.html', databases=db_manager.get_all_databases())

@management_bp.route('/databases', methods=['GET', 'POST'])
def handle_databases():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        
        if action == 'add':
            config = DatabaseConfig(
                name=data['name'],
                host=data['host'],
                port=data.get('port', 3306),
                user=data.get('user', 'root'),
                password=data.get('password', ''),
                database=data.get('database', '')
            )
            if db_manager.add_database(config):
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Failed to add database"}), 400
        
        elif action == 'remove':
            if db_manager.remove_database(data['name']):
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Database not found"}), 404
        
        elif action == 'switch':
            if db_manager.set_current_db(data['name']):
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "Database not found"}), 404
    
    # GET request - return all databases
    current_db = db_manager.get_current_db()
    return jsonify({
        "databases": [{
            "name": db.name,
            "host": db.host,
            "port": db.port,
            "user": db.user,
            "database": db.database,
            "active": db.active
        } for db in db_manager.get_all_databases()],
        "current_db": current_db.name if current_db else None
    })

@management_bp.route('/test_connection', methods=['POST'])
def test_connection():
    data = request.json
    config = DatabaseConfig(
        name=data.get('name', 'test'),
        host=data['host'],
        port=data.get('port', 3306),
        user=data.get('user', 'root'),
        password=data.get('password', ''),
        database=data.get('database', '')
    )
    if db_manager.test_connection(config):
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Connection failed"}), 400

def manage_database_service(command, host, port):
    try:
        mysql_service_name = 'mysqld'
        
        if platform.system() == "Windows":
            subprocess.run(['net', command, mysql_service_name], check=True)
        else:
            subprocess.run(['systemctl', command, mysql_service_name], check=True)
        
        return {"status": "success", "message": f"Database {command}ed successfully on {host}:{port}"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"Failed to {command} database on {host}:{port}: {str(e)}"}

@management_bp.route('/start_database', methods=['POST'])
def start_database():
    result = manage_database_service('start', request.form['host'], request.form['port'])
    return jsonify(result), 200 if result['status'] == 'success' else 500

@management_bp.route('/stop_database', methods=['POST'])
def stop_database():
    result = manage_database_service('stop', request.form['host'], request.form['port'])
    return jsonify(result), 200 if result['status'] == 'success' else 500

@management_bp.route('/restart_database', methods=['POST'])
def restart_database():
    result = manage_database_service('restart', request.form['host'], request.form['port'])
    return jsonify(result), 200 if result['status'] == 'success' else 500