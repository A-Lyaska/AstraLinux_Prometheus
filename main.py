import ansible_runner
from prometheus_client import start_http_server, Gauge
from flask import Flask, render_template_string
import psutil
import socket
import platform
from datetime import datetime

app = Flask(__name__)

# Prometheus метрики
gauge_memory = Gauge("host_memory_usage", "Memory usage by host", ["host"])
gauge_cpu = Gauge("host_cpu_load", "CPU load by host", ["host"])

# Данные о хостах в инвентаре
inventory_path = "./inventory"
hosts_data = [
    {"name": "host1", "ip": "172.16.0.10", "user": "alyaska", "password": "12345678"},
    {"name": "host2", "ip": "172.16.0.20", "user": "alyaska", "password": "12345678"},
]

# Шаблон страницы
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>VM Monitoring</title>
    <style>
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid black; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .high-load { background-color: red; color: white; }
    </style>
</head>
<body>
    <h1>Monitoring Dashboard</h1>
    <table>
        <tr>
            <th>Hostname</th>
            <th>Date & Time</th>
            <th>IP Address</th>
            <th>OS Version</th>
            <th>Kernel Version</th>
            <th>CPU Load</th>
            <th>Memory Usage</th>
            <th>Disk Usage</th>
            <th>Auth Errors</th>
        </tr>
        {% for host in hosts %}
        <tr class="{% if host['high_memory'] %}high-load{% endif %}">
            <td>{{ host['hostname'] }}</td>
            <td>{{ host['datetime'] }}</td>
            <td>{{ host['ip'] }}</td>
            <td>{{ host['os'] }}</td>
            <td>{{ host['kernel'] }}</td>
            <td>{{ host['cpu_load'] }}</td>
            <td>{{ host['memory'] }}</td>
            <td>{{ host['disk'] }}</td>
            <td>{{ host['auth_errors'] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

# Создание файла инвенторя для Ansible
def create_inventory():
    with open(inventory_path, "w") as file:
        file.write("[all]\n")
        for host in hosts_data:
            file.write(f"{host['name']} ansible_host={host['ip']} ansible_user={host['user']} ansible_ssh_pass={host['password']}\n")
    print("Inventory файл создан.")

# Запуск Ansible
def run_ansible_playbook(playbook_path):
    result = ansible_runner.run(private_data_dir=".", playbook=playbook_path, inventory=inventory_path)
    if result.status == "failed":
        print("Ansible playbook failed.")
    else:
        print("Ansible playbook completed successfully.")

# Сбор информации о хосте
def collect_host_metrics():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    os_version = platform.platform()
    kernel_version = platform.release()
    cpu_load = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    auth_errors = sum(1 for line in open("/var/log/auth.log") if "Failed password" in line)

    # Prometheus метрики
    gauge_memory.labels(host=hostname).set(memory.percent)
    gauge_cpu.labels(host=hostname).set(cpu_load)

    return {
        "hostname": hostname,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ip": ip_address,
        "os": os_version,
        "kernel": kernel_version,
        "cpu_load": f"{cpu_load}%",
        "memory": f"{memory.percent}%",
        "disk": f"{disk.percent}%",
        "auth_errors": auth_errors,
        "high_memory": memory.percent > 80
    }

@app.route("/")
def dashboard():
    hosts = [collect_host_metrics() for _ in hosts_data]
    return render_template_string(html_template, hosts=hosts)

if __name__ == "__main__":
    create_inventory()
    run_ansible_playbook("setup_servers.yml")
    start_http_server(8000)
    print("Prometheus server запущен на порту 8000.")
    app.run(host="0.0.0.0", port=5000)
