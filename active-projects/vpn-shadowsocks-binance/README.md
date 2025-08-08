# 🟢 Shadowsocks VPN for Binance Access

**我们的第一个成功项目** ✨

## 项目概述
- **目的**: 从美国访问Binance交易所
- **解决方案**: Shadowsocks VPN with PAC routing
- **完成时间**: 2025-08-07
- **实际配置时间**: <1小时（虽然总共花了14小时踩坑）

## 技术架构

### 服务器端
- **位置**: 新加坡（Tencent Cloud）
- **IP**: 43.160.195.89
- **端口**: 443（伪装HTTPS）
- **加密**: AES-256-GCM
- **优化**: BBR加速启用

### 客户端
- **Windows**: Shadowsocks GUI客户端
- **Android**: Shadowsocks APP with per-app VPN
- **本地代理**: SOCKS5 @ 127.0.0.1:1080

## 配置文件

### 服务器配置 (/etc/shadowsocks-libev/config.json)
```json
{
  "server": "0.0.0.0",
  "server_port": 443,
  "password": "kcS95i51Wt4PPu01",
  "timeout": 300,
  "method": "aes-256-gcm",
  "fast_open": true,
  "mode": "tcp_and_udp"
}
```

### PAC规则（智能分流）
- binance.com → 走VPN
- 其他网站 → 本地直连

## 使用指南

### 日常浏览（PAC模式）
- 只有Binance相关流量走VPN
- 其他网站保持本地速度

### Binance桌面客户端（全局模式）
1. 右键系统托盘纸飞机图标
2. 切换到"全局模式"
3. 启动Binance客户端
4. 用完切回PAC模式

## 项目经验教训

### 失败的尝试 ❌
1. **WireGuard (10+小时)**
   - UDP协议被ISP封锁
   - 尝试多个端口无效
   - 密钥配置错误20+次

### 成功的关键 ✅
1. 使用TCP协议（Shadowsocks）
2. 443端口伪装HTTPS流量
3. PAC模式智能分流
4. 正确的服务器位置（新加坡可访问Binance）

## 性能指标
- 延迟: ~197ms（美国到新加坡）
- 稳定性: 24/7运行
- 并发: 支持多设备同时连接

## 维护命令

### 检查服务状态
```bash
ssh ubuntu@43.160.195.89
sudo systemctl status shadowsocks-libev
```

### 重启服务
```bash
sudo systemctl restart shadowsocks-libev
```

## 备份文件
- 客户端配置: `client-config.json`
- 服务器脚本: `server-setup.sh`
- PAC规则: `pac-rules.txt`

---

## 总结
虽然过程曲折（14小时的教训），但最终1小时内成功搭建。这个项目教会我们：
1. 先测试网络环境
2. 选择正确的技术栈
3. 不要盲目重复失败的尝试

**这是我们第一个成功的项目，值得记录！** 🎉