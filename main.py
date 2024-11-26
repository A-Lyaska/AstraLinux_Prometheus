import os
from flask import Flask, jsonify, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)

# Данные хостов в Prometheus
hosts_data = [
    {"name": "host1", "ip": "172.16.0.10"},
    {"name": "host2", "ip": "172.16.0.20"}
]

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"  # Убедитесь, что Prometheus доступен по этому адресу

# Шаблон HTML для веб-страницы
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
    <script>
        async function fetchData() {
            const response = await fetch('/api/metrics');
            const data = await response.json();
            const tableBody = document.getElementById("host-data");
            tableBody.innerHTML = "";

            data.hosts.forEach(host => {
                const row = document.createElement("tr");
                if (host.high_memory) row.classList.add("high-load");

                row.innerHTML = `
                    <td>${host.hostname}</td>
                    <td>${host.datetime}</td>
                    <td>${host.ip}</td>
                    <td>${host.os}</td>
                    <td>${host.kernel}</td>
                    <td>${host.cpu_load}</td>
                    <td>${host.memory}</td>
                    <td>${host.disk}</td>
                    <td>${host.auth_errors}</td>
                `;
                tableBody.appendChild(row);
            });
        }

        setInterval(fetchData, 5000); // Обновление каждые 5 секунд
        window.onload = fetchData;
    </script>
</head>
<body>
    <h1>Центр мониторинга</h1>
    <table>
        <thead>
            <tr>
                <th>Имя</th>
                <th>Дата и время</th>
                <th>IP-адрес</th>
                <th>Версия ОС</th>
                <th>Версия ядра</th>
                <th>Загрузка ЦП</th>
                <th>Использование ОП</th>
                <th>Использование диска</th>
                <th>Ошибки авторизации</th>
            </tr>
        </thead>
        <tbody id="host-data">
            <!-- Данные обновляются динамически -->
        </tbody>
    </table>
</body>
</html>
"""

# Функция для получения данных из Prometheus
def fetch_metrics_from_prometheus(query):
    try:
        response = requests.get(PROMETHEUS_URL, params={"query": query})
        response.raise_for_status()
        result = response.json()
        if result["status"] == "success":
            return result["data"]["result"]
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Prometheus: {e}")
        return []

import paramiko

import paramiko

def fetch_remote_logs(host):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Параметры подключения
    username = "alyaska"  # Укажите имя пользователя
    password = "12345678"  # Укажите пароль

    try:
        ssh.connect(host['ip'], username=username, password=password)
        print(f"Authentication success for {host['name']} ({host['ip']})")
    except paramiko.AuthenticationException:
        print(f"Authentication failed for {host['name']} ({host['ip']}). Check username/password.")
        return 0
    except paramiko.SSHException as e:
        print(f"SSH error for {host['name']} ({host['ip']}): {e}")
        return 0
    except Exception as e:
        print(f"Unexpected error for {host['name']} ({host['ip']}): {e}")
        return 0

    stdin, stdout, stderr = ssh.exec_command("sudo cat /var/log/auth.log")
    logs = stdout.read().decode()
    ssh.close()

    # Подсчёт ошибок аутентификации
    auth_error_count = logs.count("Failed password")
    return auth_error_count



def fetch_metrics():
    metrics = []
    print("Hosts data:", hosts_data)  # Для отладки
    for host in hosts_data:

        hostname = host['name']  # Используем 'name' для имени хоста
        ip = host['ip']  # Используем 'ip' для IP-адреса
        print(f"Fetching metrics for {hostname} ({ip})")  # Для отладки

        # CPU Load
        cpu_query = f'avg by (instance) (rate(node_cpu_seconds_total{{mode!="idle", instance="{ip}:9100"}}[1m])) * 100'
        cpu_load = fetch_metrics_from_prometheus(cpu_query)
        print(f"CPU Load Query for {ip}: {cpu_load}")  # Для отладки
        cpu_load_value = float(cpu_load[0]["value"][1]) if cpu_load else "N/A"

        # Memory Usage
        memory_query = f'100 - (node_memory_MemAvailable_bytes{{instance="{ip}:9100"}} * 100 / node_memory_MemTotal_bytes{{instance="{ip}:9100"}})'
        memory_usage = fetch_metrics_from_prometheus(memory_query)
        print(f"Memory Usage Query for {ip}: {memory_usage}")  # Для отладки
        memory_value = float(memory_usage[0]["value"][1]) if memory_usage else "N/A"

        # Disk Usage
        disk_query = f'100 - (node_filesystem_free_bytes{{instance="{ip}:9100",fstype!=""}} * 100 / node_filesystem_size_bytes{{instance="{ip}:9100",fstype!=""}})'
        disk_usage = fetch_metrics_from_prometheus(disk_query)
        print(f"Disk Usage Query for {ip}: {disk_usage}")  # Для отладки
        disk_value = float(disk_usage[0]["value"][1]) if disk_usage else "N/A"

        # OS and Kernel Info
        os_query = f'node_uname_info{{instance="{ip}:9100"}}'
        os_info = fetch_metrics_from_prometheus(os_query)
        print(f"OS Info Query for {ip}: {os_info}")  # Для отладки
        
        if os_info:
            os_value = os_info[0]["metric"].get("version", "Linux")
            kernel_value = os_info[0]["metric"].get("release", "N/A")
            nodename_value = os_info[0]["metric"].get("nodename", "host")

        # Auth Errors (в работе)
        auth_errors = fetch_remote_logs(host)

        # Сбор данных в итоговый список
        metrics.append({
            "hostname": nodename_value,
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": ip,
            "os": os_value,
            "kernel": kernel_value,
            "cpu_load": f"{cpu_load_value:.2f}%" if isinstance(cpu_load_value, float) else "N/A",
            "memory": f"{memory_value:.2f}%" if isinstance(memory_value, float) else "N/A",
            "disk": f"{disk_value:.2f}%" if isinstance(disk_value, float) else "N/A",
            "auth_errors": auth_errors,
            "high_memory": memory_value != "N/A" and memory_value > 80
        })

    return metrics




@app.route("/")
def dashboard():
    return render_template_string(html_template)

@app.route("/api/metrics")
def api_metrics():
    hosts = fetch_metrics()
    return jsonify({"hosts": hosts})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
