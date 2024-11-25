from flask import Flask, jsonify, render_template_string
import ansible_runner
from datetime import datetime

app = Flask(__name__)

# Данные хостов в inventory.yml
hosts_data = [
    {"name": "host1", "ip": "172.16.0.10"},
    {"name": "host2", "ip": "172.16.0.20"}
]

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

# Сбор данных с помощью Ansible
def fetch_metrics():
    result = ansible_runner.run(
        private_data_dir=".",
        inventory="./inventory.yml",
        playbook="fetch_metrics.yml"
    )

    if result.rc != 0:
        print("Ansible playbook failed.")
        return []

    # Получаем кэшированные факты от всех хостов
    host_metrics = []
    fact_cache = result.get_fact_cache()
    for host, facts in fact_cache.items():
        metrics = {
            "hostname": host,
            "datetime": facts.get("datetime"),
            "ip": facts.get("ip"),
            "os": facts.get("os"),
            "kernel": facts.get("kernel"),
            "cpu_load": facts.get("cpu_load"),
            "memory": facts.get("memory"),
            "disk": facts.get("disk"),
            "auth_errors": facts.get("auth_errors"),
        }
        metrics["high_memory"] = float(metrics["memory"]) > 80
        host_metrics.append(metrics)

    return host_metrics


@app.route("/")
def dashboard():
    return render_template_string(html_template)

@app.route("/api/metrics")
def api_metrics():
    hosts = fetch_metrics()
    if not hosts:
        print("No data fetched from Ansible.")
    return jsonify({"hosts": hosts})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
