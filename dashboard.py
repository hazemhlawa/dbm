from flask import Blueprint, render_template, send_file, jsonify
import matplotlib.pyplot as plt
import seaborn as sns
import io
from utils import fetch_process_list
from db_utils import get_query_history
from mysql.connector import Error

plt.switch_backend('Agg')

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/monitor')
def monitor():
    return render_template('monitor.html')

@dashboard_bp.route('/')
def dashboard():
    try:
        query_history, query_logs, daily_query_stats = fetch_process_list()
        host_stats = {}
        for record in query_history:
            hostname = record.get('hostname', 'unknown')
            host_stats[hostname] = host_stats.get(hostname, 0) + 1

        total_queries = {}
        for day in daily_query_stats:
            if ':' not in day:
                for cmd in daily_query_stats[day]:
                    total_queries[cmd] = total_queries.get(cmd, 0) + daily_query_stats[day][cmd]
        
        print(f"Dashboard total_queries: {total_queries}")

        return render_template('dashboard.html', host_stats=host_stats, total_queries=total_queries)

    except Error as e:
        print(f"Error fetching process list: {e}")
        return render_template('dashboard.html', host_stats={}, total_queries={})

@dashboard_bp.route('/host_stats.png')
def host_stats_chart():
    try:
        query_history = get_query_history(limit=1000)  # Use SQLite for historical data
        host_stats = {}
        for record in query_history:
            hostname = record.get('hostname', 'unknown')
            host_stats[hostname] = host_stats.get(hostname, 0) + 1

        sns.set(style="whitegrid")
        fig, ax = plt.subplots()
        hosts = list(host_stats.keys())
        counts = list(host_stats.values())
        sns.barplot(x=hosts, y=counts, palette="Greens_d", ax=ax)
        ax.set_title('Host Stats')
        ax.set_xlabel('Host')
        ax.set_ylabel('Count')

        for index, value in enumerate(counts):
            ax.text(index, value, str(value), color='black', ha="center")

        output = io.BytesIO()
        plt.savefig(output, format='png')
        plt.close(fig)
        output.seek(0)
        return send_file(output, mimetype='image/png')

    except Error as e:
        print(f"Error fetching host stats: {e}")
        return send_file(io.BytesIO(), mimetype='image/png')

@dashboard_bp.route('/query_stats.png')
def query_stats_chart():
    try:
        _, _, daily_query_stats = fetch_process_list()
        total_queries = {}
        for day in daily_query_stats:
            if ':' not in day:
                for cmd in daily_query_stats[day]:
                    total_queries[cmd] = total_queries.get(cmd, 0) + daily_query_stats[day][cmd]

        print(f"Query stats chart total_queries: {total_queries}")

        sns.set(style="whitegrid")
        fig, ax = plt.subplots(figsize=(6, 6))
        labels = list(total_queries.keys())
        sizes = list(total_queries.values())
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("Paired", len(labels)))
        ax.axis('equal')
        ax.set_title('Query Statistics')

        output = io.BytesIO()
        plt.savefig(output, format='png')
        plt.close(fig)
        output.seek(0)
        return send_file(output, mimetype='image/png')

    except Error as e:
        print(f"Error fetching query stats: {e}")
        return send_file(io.BytesIO(), mimetype='image/png')

@dashboard_bp.route('/query_history')
def query_history_data():
    try:
        query_history = get_query_history(limit=100)  # Use SQLite
        return jsonify(query_history)
    except Error as e:
        print(f"Error fetching query history: {e}")
        return jsonify([])

@dashboard_bp.route('/query_stats')
def query_stats_data():
    try:
        _, _, daily_query_stats = fetch_process_list()
        total_queries = {}
        for day in daily_query_stats:
            if ':' not in day:
                for cmd in daily_query_stats[day]:
                    total_queries[cmd] = total_queries.get(cmd, 0) + daily_query_stats[day][cmd]

        print(f"Query stats data total_queries: {total_queries}")
        return jsonify(total_queries)
    except Error as e:
        print(f"Error fetching query stats: {e}")
        return jsonify({})