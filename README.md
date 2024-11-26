Для корректного запуска скрипта потребуется выполнить некоторые действия:
1) Установка python на Linux-устройство
   'apt install python'
2) Установка python-pip на Linux-устройство
   'apt install python3-pip'
3) Установить зависимости через pip (рекомендуется использовать ВПН для загрузки)
   'pip3 install ansible-runner flask prometheus_client psutil'
4) Установить Node Exporter на Linux-устройство. Установить нужно на хост и дополнительное устройство
     '# Скачать Node Exporter
     wget https://github.com/prometheus/node_exporter/releases/download/v1.6.0/node_exporter-1.6.0.linux-amd64.tar.gz
     tar xvfz node_exporter-1.6.0.linux-amd64.tar.gz
     sudo mv node_exporter-1.6.0.linux-amd64/node_exporter /usr/local/bin/
     
     # Создать systemd unit для Node Exporter
     sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<EOF
     [Unit]
     Description=Node Exporter
     Wants=network-online.target
     After=network-online.target
     
     [Service]
     User=nobody
     ExecStart=/usr/local/bin/node_exporter
     
     [Install]
     WantedBy=default.target
     EOF
     
     # Запустить Node Exporter
     sudo systemctl daemon-reload
     sudo systemctl enable node_exporter
     sudo systemctl start node_exporter'
5) Установка Prometheus на Linux-устройство (на хост)
   'wget https://github.com/prometheus/prometheus/releases/download/v2.47.0/prometheus-2.47.0.linux-amd64.tar.gz
     tar xvf prometheus-2.47.0.linux-amd64.tar.gz
     sudo mv prometheus-2.47.0.linux-amd64/prometheus /usr/local/bin/
     sudo mv prometheus-2.47.0.linux-amd64/promtool /usr/local/bin/'
7) Запуск Prometheus
   'prometheus --config.file=AstraLinux_Prometheus/prometheus.yml'
8) Запуск скрипта
   'python3 AstraLinux_Prometheus/main.py'
