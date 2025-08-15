# Tiger System - Database Infrastructure Deployment Guide

## 📋 Prerequisites

### System Requirements
- Ubuntu 20.04+ or compatible Linux distribution
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Minimum 4GB RAM
- 20GB available disk space

### Software Dependencies
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.10
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install PostgreSQL 14
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update
sudo apt install postgresql-14 postgresql-client-14 -y

# Install Redis
sudo apt install redis-server -y
```

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/tiger/TigerSystem.git
cd TigerSystem
```

### 2. Setup Python Environment
```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create user for Tiger System
CREATE USER tiger_app WITH PASSWORD 'tiger_secure_password_2024';
ALTER USER tiger_app CREATEDB;
\q

# Update PostgreSQL configuration for performance
sudo nano /etc/postgresql/14/main/postgresql.conf
# Add/modify these settings:
# shared_buffers = 256MB
# effective_cache_size = 1GB
# maintenance_work_mem = 128MB
# checkpoint_completion_target = 0.9
# wal_buffers = 16MB

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 4. Configure Redis
```bash
# Copy Redis configuration
sudo cp config/redis.conf /etc/redis/redis.conf

# Set Redis password
sudo nano /etc/redis/redis.conf
# Find and update: requirepass tiger_redis_2024

# Restart Redis
sudo systemctl restart redis-server

# Enable Redis on boot
sudo systemctl enable redis-server
```

### 5. Initialize Database
```bash
# Set environment variables
export TIGER_DB_PASSWORD="tiger_secure_password_2024"

# Run database initialization
python database/init_database.py

# Expected output:
# Database connection successful, all tables created
```

### 6. Configure API Keys
```bash
# Copy template
cp config/api_keys.yaml.example config/api_keys.yaml

# Edit with your API keys
nano config/api_keys.yaml
```

## 📁 Directory Structure

```
TigerSystem/
├── database/           # Database scripts and models
│   ├── create_database.sql
│   ├── init_database.py
│   └── models/
├── config/            # Configuration files
│   ├── database.yaml
│   ├── redis.yaml
│   ├── system.yaml
│   └── api_keys.yaml
├── core/              # Core modules
│   ├── interfaces.py
│   ├── dal.py
│   └── redis_manager.py
├── tests/             # Test suites
│   ├── test_database.py
│   └── test_performance.py
└── docs/              # Documentation
    └── DEPLOY.md
```

## 🔧 Configuration

### Database Configuration
Edit `config/database.yaml`:
```yaml
host: localhost
port: 5432
database: tiger_system
user: tiger_app
password: ${TIGER_DB_PASSWORD}
```

### Redis Configuration
Edit `config/redis.yaml`:
```yaml
host: localhost
port: 6379
password: tiger_redis_2024
```

### System Configuration
Edit `config/system.yaml` for system-wide settings.

## 🧪 Testing

### Run Unit Tests
```bash
python tests/test_database.py
```

### Run Performance Tests
```bash
python tests/test_performance.py
```

### Expected Test Results
- All database tables created: ✓
- Connection pool working: ✓
- Redis cache operational: ✓
- Write latency < 10ms: ✓
- Query latency < 100ms: ✓
- Throughput > 10,000 ops/sec: ✓

## 🔍 Verification

### Check Database Status
```bash
# Connect to database
psql -h localhost -U tiger_app -d tiger_system

# List tables
\dt

# Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Check Redis Status
```bash
# Connect to Redis
redis-cli -a tiger_redis_2024

# Check server info
INFO server

# Test set/get
SET test "Hello Tiger"
GET test
```

## 🚨 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# Test connection
psql -h localhost -U tiger_app -d tiger_system -c "SELECT 1;"
```

### Redis Connection Issues
```bash
# Check Redis status
sudo systemctl status redis-server

# Check logs
sudo tail -f /var/log/redis/redis-server.log

# Test connection
redis-cli -a tiger_redis_2024 ping
```

### Permission Issues
```bash
# Fix PostgreSQL permissions
sudo chown postgres:postgres /var/lib/postgresql/14/main

# Fix Redis permissions
sudo chown redis:redis /var/lib/redis
```

## 🔐 Security

### Production Deployment
1. **Change default passwords** in all configuration files
2. **Use environment variables** for sensitive data
3. **Enable SSL/TLS** for database connections
4. **Configure firewall** to restrict access
5. **Set up regular backups**

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 5432/tcp  # PostgreSQL (only from app servers)
sudo ufw allow 6379/tcp  # Redis (only from localhost)
sudo ufw enable
```

### Backup Strategy
```bash
# Database backup script
pg_dump -h localhost -U tiger_app tiger_system > backup_$(date +%Y%m%d).sql

# Redis backup
redis-cli -a tiger_redis_2024 BGSAVE
```

## 📊 Monitoring

### System Health Check
```python
from core.dal import get_dal

dal = get_dal()
health = dal.get_system_health()
print(health)
```

### Performance Monitoring
```python
stats = dal.get_performance_stats()
print(stats)
```

## 🔄 Maintenance

### Daily Tasks
- Check system logs
- Monitor disk usage
- Verify backup completion

### Weekly Tasks
- Review performance metrics
- Clean up old logs
- Update statistics

### Monthly Tasks
- Archive old data (> 30 days)
- Optimize database tables
- Review and update configurations

## 📝 Integration with Other Windows

After successful deployment, other windows can connect using:

```python
from core.dal import get_dal
from core.redis_manager import RedisManager

# Get DAL instance
dal = get_dal()

# Insert market data
dal.insert_market_data(market_data)

# Get Redis manager
redis = RedisManager()

# Publish message
redis.publish('market_updates', message)
```

## ✅ Deployment Checklist

- [ ] System requirements met
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and configured
- [ ] Python environment set up
- [ ] Dependencies installed
- [ ] Database initialized
- [ ] All tables created
- [ ] Redis connection working
- [ ] Unit tests passing
- [ ] Performance tests passing
- [ ] Configuration files updated
- [ ] API keys configured
- [ ] Security measures in place
- [ ] Backup system configured
- [ ] Monitoring enabled

## 📞 Support

For issues or questions:
- Check logs in `/var/log/`
- Review test output
- Ensure all services are running
- Verify configuration files

---

**Window 1 - Database Infrastructure**
*The foundation of Tiger System*