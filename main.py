from flask import Flask, jsonify, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)

# Хосты Prometheus
PROMETHEUS_URL = "http://<Prometheus_IP>:9090"

# Шаблон для веб-страницы
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

# Функция для получения метрик из Prometheus
def fetch_metrics():
    hosts = [
        {"name": "host1", "ip": "172.16.0.10"},
        {"name": "host2", "ip": "172.16.0.20"}
    ]

    metrics = []
    for host in hosts:
        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={
            "query": f"node_memory_MemTotal_bytes{{instance='{host['ip']}:9100'}}"
        })
        memory_total = int(response.json()["data"]["result"][0]["value"][1])

        response = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={
            "query": f"node_memory_MemAvailable_bytes{{instance='{host['ip']}:9100'}}"
        })
        memory_available = int(response.json()["data"]["result"][0]["value"][1])

        memory_usage = (1 - memory_available / memory_total) * 100

        metrics.append({
            "hostname": host["name"],
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip": host["ip"],
            "os": "Linux",
            "kernel": "N/A",
            "cpu_load": "N/A",
            "memory": f"{memory_usage:.2f}%",
            "disk": "N/A",
            "auth_errors": 0,
            "high_memory": memory_usage > 80
        })
    return metrics

@app.route("/")
def dashboard():
    return render_template_string(html_template)

@app.route("/api/metrics")
def api_metrics():
    return jsonify({"hosts": fetch_metrics()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
