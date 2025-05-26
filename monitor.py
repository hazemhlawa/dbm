from flask import Blueprint, render_template, jsonify, send_file
import psutil
import matplotlib.pyplot as plt
import seaborn as sns
import io

monitor_bp = Blueprint('monitor', __name__)

@monitor_bp.route('/')
def monitor():
    return render_template('monitor.html')

@monitor_bp.route('/performance_data')
def performance_data():
    performance_stats = {
        'cpu': psutil.cpu_percent(interval=1),
        'memory': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'network': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
    }
    return jsonify(performance_stats)

@monitor_bp.route('/performance_chart/<metric>.png')
def performance_chart(metric):
    try:
        performance_stats = {
            'cpu': psutil.cpu_percent(interval=1, percpu=True),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'network': psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        }

        sns.set(style="whitegrid")
        fig, ax = plt.subplots()
        times = list(range(len(performance_stats[metric])))
        values = performance_stats[metric]
        sns.lineplot(x=times, y=values, ax=ax)
        ax.set_title(f'{metric.capitalize()} Usage')
        ax.set_xlabel('Time')
        ax.set_ylabel('Usage (%)')

        output = io.BytesIO()
        plt.savefig(output, format='png')
        plt.close(fig)
        output.seek(0)
        return send_file(output, mimetype='image/png')
    except KeyError as e:
        return jsonify({"error": f"Metric '{metric}' not found"}), 404
