from flask import Flask, render_template, send_from_directory, redirect, url_for, request, flash, Response
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap
import psutil
import csv
from io import StringIO
from dashboard import dashboard_bp
from monitor import monitor_bp
from management import management_bp
from utils import fetch_process_list
from availdb import fetch_database_availability
from flask_login import LoginManager, current_user, login_user, login_required, logout_user, UserMixin
import os
from dotenv import load_dotenv
from db_utils import init_db, clean_old_queries

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "AZ1GPM-MPIfpkZrq5X-cARZnlASQ3kKTfXjVB0RPIRI")
Bootstrap(app)

app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(monitor_bp, url_prefix='/monitor')
app.register_blueprint(management_bp, url_prefix='/management')

socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

    def get_id(self):
        return self.id

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

@app.route('/download_queries')
@login_required
def download_queries():
    query_data, _, _ = fetch_process_list(page=1, per_page=100)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Hostname', 'Process ID', 'User', 'Database', 'Query Time', 'Execution Time (ms)', 'Query Type', 'Executed Tool', 'Query'])
    for query in query_data:
        cw.writerow([
            query['hostname'],
            query['pid'],
            query['user'],
            query['database'],
            query['query_time'],
            query['execution_time_ms'],
            query['query_type'],
            query['executed_tool'],
            query['query']
        ])
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=query_report.csv"}
    )

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico')

@app.before_request
def before_request():
    if not current_user.is_authenticated and request.endpoint and 'static' not in request.endpoint:
        if request.endpoint.startswith('dashboard') or request.endpoint.startswith('monitor') or request.endpoint.startswith('management'):
            return redirect(url_for('login'))

def background_task():
    page = 1
    while True:
        try:
            query_data, query_logs, daily_stats = fetch_process_list(page=page, per_page=10)
            socketio.emit('realtime_data', query_data)
            socketio.emit('query_logs', query_logs)
            socketio.emit('daily_query_stats', dict(daily_stats))
            page = (page % 10) + 1
            socketio.sleep(1)
        except Exception as e:
            print(f"Error in background_task: {e}")
            socketio.sleep(5)

def database_availability_task():
    while True:
        try:
            _, availability_status, _ = fetch_database_availability()
            socketio.emit('db_availability', dict(availability_status))
            socketio.sleep(1)
        except Exception as e:
            print(f"Error in database_availability_task: {e}")
            socketio.sleep(5)

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
            socketio.sleep(5)
        except Exception as e:
            print(f"Error in performance_task: {e}")
            socketio.sleep(10)

def cleanup_task():
    while True:
        try:
            clean_old_queries(days=30)
            socketio.sleep(86400)  # Run daily
        except Exception as e:
            print(f"Error in cleanup_task: {e}")
            socketio.sleep(3600)  # Retry in 1 hour

# Initialize SQLite database
with app.app_context():
    init_db()

socketio.start_background_task(target=background_task)
socketio.start_background_task(target=database_availability_task)
socketio.start_background_task(target=performance_task)
socketio.start_background_task(target=cleanup_task)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)