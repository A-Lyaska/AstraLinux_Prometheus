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
    <h1>Monitoring Dashboard</h1>
    <table>
        <thead>
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

def fetch_metrics():
    metrics = []
    print("Hosts data:", hosts_data)  # Для отладки
    for host in hosts_data:
        # Проверка наличия ключей 'name' и 'ip'
        if 'name' not in host or 'ip' not in host:
            print(f"Host {host} skipped, missing 'name' or 'ip'.")  # Для отладки
            continue  # Пропустить хост, если отсутствуют нужные данные

        nodename = os_query[0]['metric']['nodename']
        print(f"Using nodename as hostname: {nodename}")
        host['name'] = nodename

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
            os_value = os_info[0]["metric"].get("os", "Linux")
            kernel_value = os_info[0]["metric"].get("release", "N/A")
        else:
            os_value = "Linux"
            kernel_value = "N/A"

        # Auth Errors (пока заглушка, требует доработки)
        auth_errors = 0

        # Сбор данных в итоговый список
        metrics.append({
            "hostname": hostname,
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
