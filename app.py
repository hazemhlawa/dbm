from flask import Flask, render_template, send_from_directory, redirect, url_for, request, flash
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
import psutil
from dashboard import dashboard_bp
from monitor import monitor_bp
from management import management_bp
from utils import fetch_process_list
from availdb import fetch_database_availability
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
import os

app = Flask(__name__)
socketio = SocketIO(app)
db_manager = DatabaseManager()
app.secret_key = 'your_secret_key'  # Needed for session management
Bootstrap(app)

app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(monitor_bp, url_prefix='/monitor')
app.register_blueprint(management_bp, url_prefix='/management')


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return self.id

# In-memory user store, for demo purposes
users = {'admin': {'password': 'admin123'}}

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/databases', methods=['GET', 'POST'])
def manage_databases():
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
                databases=data.get('databases', [])
            )
            db_manager.add_database(config)
            return jsonify({'status': 'success'})
        
        elif action == 'remove':
            db_manager.remove_database(data['name'])
            return jsonify({'status': 'success'})
        
        elif action == 'switch':
            if db_manager.set_current_db(data['name']):
                return jsonify({'status': 'success'})
            return jsonify({'status': 'error', 'message': 'Database not found'}), 404
    
    # GET request - return all databases
    databases = db_manager.get_all_databases()
    current_db = db_manager.get_current_db()
    return jsonify({
        'databases': [{
            'name': db.name,
            'host': db.host,
            'port': db.port,
            'active': db.name == current_db.name if current_db else False
        } for db in databases],
        'current': current_db.name if current_db else None
    })

def background_monitoring():
    """Background task to monitor the current database"""
    while True:
        try:
            current_db = db_manager.get_current_db()
            if current_db:
                # Get and emit monitoring data
                process_data, query_logs, daily_stats = fetch_process_list()
                performance_data = fetch_database_performance()
                
                socketio.emit('monitoring_data', {
                    'processes': process_data,
                    'queries': query_logs,
                    'performance': performance_data,
                    'daily_stats': daily_stats,
                    'database': current_db.name
                })
        except Exception as e:
            print(f"Monitoring error: {e}")
        socketio.sleep(5)

# Start background thread
threading.Thread(target=background_monitoring, daemon=True).start()

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

# Protect the blueprint routes
@app.before_request
def before_request():
    if not current_user.is_authenticated and request.endpoint and 'static' not in request.endpoint:
        if request.endpoint.startswith('dashboard') or request.endpoint.startswith('monitor') or request.endpoint.startswith('management'):
            return redirect(url_for('login'))

def background_task():
    while True:
        try:
            query_data, query_logs, daily_stats = fetch_process_list()
            socketio.emit('realtime_data', query_data)
            socketio.emit('query_logs', query_logs)
            socketio.emit('daily_query_stats', daily_stats)
        except Exception as e:
            print("Error during fetch or emit:", e)
        socketio.sleep(1)

def database_availability_task():
    while True:
        try:
            _, availability_status, _ = fetch_database_availability()
            socketio.emit('db_availability', availability_status)
        except Exception as e:
            print("Error during fetch or emit:", e)
        socketio.sleep(1)

def performance_task():
    while True:
        try:
            performance_stats = {
                'cpu': psutil.cpu_percent(interval=1),
                'memory': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent,
                'network': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            }
            socketio.emit('realtime_performance', performance_stats)
        except Exception as e:
            print("Error during fetch or emit:", e)
        socketio.sleep(5)

socketio.start_background_task(target=background_task)
socketio.start_background_task(target=database_availability_task)
socketio.start_background_task(target=performance_task)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)