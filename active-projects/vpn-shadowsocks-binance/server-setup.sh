#!/bin/bash
# Shadowsocks Server Setup Script
# Server: 43.160.195.89 (Singapore)
# Purpose: Binance access from US

# Update system
apt update && apt upgrade -y

# Install Shadowsocks
apt install -y shadowsocks-libev

# Configure Shadowsocks
cat > /etc/shadowsocks-libev/config.json << EOF
{
  "server": "0.0.0.0",
  "server_port": 443,
  "password": "kcS95i51Wt4PPu01",
  "timeout": 300,
  "method": "aes-256-gcm",
  "fast_open": true,
  "mode": "tcp_and_udp",
  "no_delay": true,
  "reuse_port": true
}
EOF

# Enable BBR (Google TCP acceleration)
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p

# Optimize network parameters
cat >> /etc/sysctl.conf << EOF
fs.file-max = 51200
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
EOF
sysctl -p

# Configure systemd service
cat > /etc/systemd/system/shadowsocks-libev.service << EOF
[Unit]
Description=Shadowsocks-libev Server
After=network.target

[Service]
Type=simple
User=nobody
Group=nogroup
LimitNOFILE=51200
ExecStart=/usr/bin/ss-server -c /etc/shadowsocks-libev/config.json -u

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable shadowsocks-libev
systemctl start shadowsocks-libev

# Setup auto-restart
cat > /etc/systemd/system/shadowsocks-monitor.service << EOF
[Unit]
Description=Monitor and restart Shadowsocks
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c 'while true; do systemctl is-active shadowsocks-libev || systemctl restart shadowsocks-libev; sleep 300; done'
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable shadowsocks-monitor
systemctl start shadowsocks-monitor

echo "Shadowsocks server setup complete!"
echo "Server: 43.160.195.89:443"
echo "Password: kcS95i51Wt4PPu01"
echo "Method: aes-256-gcm"