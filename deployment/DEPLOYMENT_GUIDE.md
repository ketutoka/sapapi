# SAP API Production Deployment Guide

## Overview
Panduan lengkap untuk deploy SAP API Flask application di Ubuntu production server dengan PostgreSQL, Nginx, dan monitoring lengkap.

## Prerequisites
- Ubuntu Server 20.04 LTS atau lebih baru
- Root access atau sudo privileges
- Domain name (opsional untuk SSL)
- Minimum 2GB RAM, 2 CPU cores, 20GB disk space

## Quick Deployment

### 1. Download dan Persiapkan
```bash
# Clone repository
git clone https://github.com/ketutoka/sapapi.git
cd sapapi

# Buat script executable
chmod +x deployment/deploy.sh
chmod +x deployment/monitoring.sh
```

### 2. Konfigurasi Environment
Edit file `deployment/.env.production` dan sesuaikan:
```bash
# Update database password dan secret key
DATABASE_URL=postgresql://sapapi_user:YOUR_SECURE_PASSWORD@localhost:5432/sapdwh
SECRET_KEY=YOUR_SECURE_SECRET_KEY

# Update domain name di deployment/nginx-sapapi.conf
# Ganti 'your-domain.com' dengan domain Anda
```

### 3. Run Automated Deployment
```bash
sudo ./deployment/deploy.sh
```

Script ini akan:
- Update sistem Ubuntu
- Install semua dependencies (Python, PostgreSQL, Nginx, dll)
- Create dedicated user dan setup security
- Configure database
- Deploy aplikasi dengan virtual environment
- Setup systemd service
- Configure Nginx reverse proxy
- Setup firewall (UFW)
- Configure monitoring dan backup scripts

## Manual Deployment Steps

### Step 1: System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv python3-dev \
                    postgresql postgresql-contrib nginx supervisor \
                    certbot python3-certbot-nginx git curl wget \
                    build-essential fail2ban ufw
```

### Step 2: Create Application User
```bash
# Create user
sudo useradd -r -s /bin/bash -d /opt/sapapi -m sapapi
sudo usermod -aG sapapi sapapi
```

### Step 3: PostgreSQL Setup
```bash
# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database dan user
sudo -u postgres psql -c "CREATE USER sapapi_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "CREATE DATABASE sapdwh OWNER sapapi_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sapdwh TO sapapi_user;"
```

### Step 4: Application Setup
```bash
# Clone repository
sudo -u sapapi git clone https://github.com/ketutoka/sapapi.git /opt/sapapi

# Create virtual environment
sudo -u sapapi python3 -m venv /opt/sapapi/venv

# Install dependencies
sudo -u sapapi /opt/sapapi/venv/bin/pip install -r /opt/sapapi/requirements.txt

# Create production environment file
sudo -u sapapi cp /opt/sapapi/deployment/.env.production /opt/sapapi/.env
# Edit .env dengan password dan secret key yang benar
```

### Step 5: Database Initialization
```bash
# Initialize database tables
sudo -u sapapi bash -c "cd /opt/sapapi && source venv/bin/activate && python3 -c 'from app import app, db; app.app_context().push(); db.create_all()'"
```

### Step 6: Systemd Service
```bash
# Copy service file
sudo cp /opt/sapapi/deployment/sapapi.service /etc/systemd/system/
# Edit service file dengan password yang benar

# Enable dan start service
sudo systemctl daemon-reload
sudo systemctl enable sapapi
sudo systemctl start sapapi
```

### Step 7: Nginx Configuration
```bash
# Copy nginx config
sudo cp /opt/sapapi/deployment/nginx-sapapi.conf /etc/nginx/sites-available/sapapi

# Edit domain name di config file
sudo sed -i 's/your-domain.com/youractual-domain.com/g' /etc/nginx/sites-available/sapapi

# Enable site
sudo ln -s /etc/nginx/sites-available/sapapi /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Test dan restart nginx
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Step 8: Firewall Setup
```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

### Step 9: SSL Certificate (Optional)
```bash
# Get SSL certificate dengan Certbot
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Step 10: Monitoring Setup
```bash
# Setup monitoring scripts
sudo bash /opt/sapapi/deployment/monitoring.sh
```

## Service Management

### Basic Commands
```bash
# Start/Stop/Restart service
sudo systemctl start sapapi
sudo systemctl stop sapapi
sudo systemctl restart sapapi

# Check status
sudo systemctl status sapapi

# View logs
sudo journalctl -u sapapi -f
sudo tail -f /var/log/sapapi/error.log
sudo tail -f /var/log/sapapi/access.log
```

### Health Monitoring
```bash
# Quick status check
sapapi-status

# Comprehensive health check
sapapi-health-check

# View performance metrics
tail -f /var/log/sapapi/performance.log
```

## API Endpoints

### Production URLs
- **API Documentation**: `https://yourdomain.com/docs/`
- **Health Check**: `https://yourdomain.com/api/health`
- **Sales Endpoint**: `https://yourdomain.com/api/sales`
- **Database Check**: `https://yourdomain.com/api/database/check`

### Testing API
```bash
# Health check
curl https://yourdomain.com/api/health

# Post sales data
curl -X POST https://yourdomain.com/api/sales \
  -H "Content-Type: application/json" \
  -d '{
    "vkorg": "1000",
    "erdat": "2023-12-01",
    "matnr": "MATERIAL001",
    "kwmeng": 100.0,
    "netwr": 1000000.0
  }'
```

## Database Management

### Backup
```bash
# Manual backup
sapapi-backup

# Check backup status
sapapi-backup-monitor
```

### Database Access
```bash
# Connect to database
sudo -u postgres psql -d sapdwh

# View tables
\dt

# Check data
SELECT COUNT(*) FROM dwh_sales;
```

## Performance Tuning

### Gunicorn Workers
Edit `/etc/systemd/system/sapapi.service`:
```ini
# Adjust workers based on CPU cores
--workers 4  # (CPU cores * 2) + 1
```

### PostgreSQL Tuning
Edit `/etc/postgresql/*/main/postgresql.conf`:
```ini
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 8MB
```

### Nginx Tuning
Edit `/etc/nginx/sites-available/sapapi`:
```nginx
# Adjust rate limiting
limit_req zone=api burst=20 nodelay;

# Adjust timeouts
proxy_read_timeout 30s;
```

## Security Considerations

### Database Security
- Use strong passwords
- Limit database access to localhost only
- Regular security updates

### Application Security
- Keep dependencies updated
- Use strong SECRET_KEY
- Enable HTTPS
- Regular log monitoring

### Server Security
- Fail2ban configured
- UFW firewall enabled
- Regular system updates
- SSH key authentication recommended

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check service status
sudo systemctl status sapapi

# Check logs
sudo journalctl -u sapapi -n 50

# Check application logs
sudo tail -f /var/log/sapapi/error.log
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d sapdwh -c "SELECT 1;"

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

#### Nginx Issues
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Log Locations
- Application logs: `/var/log/sapapi/`
- Nginx logs: `/var/log/nginx/`
- PostgreSQL logs: `/var/log/postgresql/`
- System logs: `sudo journalctl -u sapapi`

## Maintenance

### Regular Tasks
1. **Daily**: Check service status dan logs
2. **Weekly**: Review performance metrics
3. **Monthly**: Update system packages
4. **Quarterly**: Review security settings

### Update Procedure
```bash
# Stop service
sudo systemctl stop sapapi

# Backup database
sapapi-backup

# Update code
sudo -u sapapi git -C /opt/sapapi pull

# Install new dependencies
sudo -u sapapi /opt/sapapi/venv/bin/pip install -r /opt/sapapi/requirements.txt

# Restart service
sudo systemctl start sapapi

# Verify deployment
sapapi-health-check
```

## Monitoring and Alerting

### Available Monitoring Scripts
- `sapapi-status` - Quick status overview
- `sapapi-health-check` - Comprehensive health check
- `sapapi-process-monitor` - Process monitoring
- `sapapi-performance-monitor` - Performance metrics
- `sapapi-backup-monitor` - Backup status

### Email Alerts
Configure email alerts di `/etc/sapapi/alerting.conf`:
```bash
ALERT_EMAIL="admin@yourdomain.com"
ENABLE_EMAIL_ALERTS="true"
```

## Support

### Getting Help
1. Check log files untuk error messages
2. Run health check scripts
3. Review system resources
4. Check service status

### Performance Monitoring
```bash
# View system resources
htop

# Check disk space
df -h

# Monitor API performance
curl -w "Total time: %{time_total}s\n" https://yourdomain.com/api/health
```