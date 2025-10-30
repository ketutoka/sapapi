# SAP API Deployment Files

Folder ini berisi semua file yang dibutuhkan untuk deploy SAP API Flask application di Ubuntu production server.

## 📁 File Structure

```
deployment/
├── sapapi.service              # Systemd service file
├── nginx-sapapi.conf          # Nginx configuration (bare metal)
├── nginx-docker.conf          # Nginx configuration (Docker)
├── gunicorn.conf.py           # Gunicorn WSGI server config
├── .env.production            # Production environment template
├── deploy.sh                  # Complete automated deployment script
├── quick-install.sh           # Quick installation script
├── monitoring.sh              # Monitoring and health check scripts
├── Dockerfile                 # Docker container definition
├── docker-compose.yml         # Docker Compose orchestration
└── DEPLOYMENT_GUIDE.md        # Detailed deployment guide
```

## 🚀 Quick Start Options

### Option 1: Automated Deployment (Recommended)
```bash
# Clone repository
git clone https://github.com/ketutoka/sapapi.git
cd sapapi

# Run complete deployment
sudo chmod +x deployment/deploy.sh
sudo ./deployment/deploy.sh
```

### Option 2: Quick Installation
```bash
# Simple installation for testing
sudo chmod +x deployment/quick-install.sh
sudo ./deployment/quick-install.sh
```

### Option 3: Docker Deployment
```bash
# Using Docker Compose
cd deployment
cp .env.production .env
# Edit .env dengan password yang aman
sudo docker-compose up -d
```

## 📋 Before Deployment

### 1. Update Configuration Files

**Edit domain name in nginx configs:**
```bash
sed -i 's/your-domain.com/yourdomain.com/g' deployment/nginx-sapapi.conf
```

**Edit environment variables:**
```bash
cp deployment/.env.production .env
# Edit .env dengan:
# - DATABASE_URL dengan password yang aman
# - SECRET_KEY dengan key yang aman
```

### 2. System Requirements
- Ubuntu 20.04 LTS atau lebih baru
- Minimum 2GB RAM, 2 CPU cores
- 20GB disk space
- Root access atau sudo privileges

## 🔧 Configuration Files

### sapapi.service
Systemd service configuration untuk menjalankan aplikasi sebagai system service dengan:
- Auto-restart on failure
- Proper user isolation
- Environment variables
- Resource limits
- Logging configuration

### nginx-sapapi.conf
Nginx reverse proxy configuration dengan:
- SSL/HTTPS support
- Rate limiting
- Security headers
- CORS support
- Static file serving
- Health check endpoints

### gunicorn.conf.py
Gunicorn WSGI server configuration untuk:
- Multi-worker processes
- Performance optimization
- Logging configuration
- Process management
- Health checks

### .env.production
Production environment template dengan:
- Database connection strings
- Security settings
- Performance tuning
- Feature flags

## 🐳 Docker Deployment

Docker Compose setup includes:
- **PostgreSQL**: Database service
- **SAP API**: Flask application
- **Nginx**: Reverse proxy
- **Redis**: Caching (optional)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f sapapi

# Check status
docker-compose ps

# Stop services
docker-compose down
```

## 📊 Monitoring & Health Checks

The monitoring.sh script creates:
- **sapapi-health-check**: Comprehensive health monitoring
- **sapapi-process-monitor**: Process monitoring and auto-restart
- **sapapi-performance-monitor**: Performance metrics collection
- **sapapi-backup-monitor**: Backup status monitoring
- **sapapi-status**: Quick status dashboard

### Usage:
```bash
# Setup monitoring
sudo bash deployment/monitoring.sh

# Check system status
sapapi-status

# Run health check
sapapi-health-check

# View performance metrics
tail -f /var/log/sapapi/performance.log
```

## 🔐 Security Features

### Application Security
- Non-root user execution
- Environment variable isolation
- Secure secret key generation
- Database credential protection

### Network Security
- UFW firewall configuration
- Nginx rate limiting
- Fail2ban integration
- SSL/TLS encryption

### System Security
- Regular security updates
- Log monitoring
- Resource limiting
- Process isolation

## 🚀 Deployment Verification

After deployment, verify installation:

```bash
# Check service status
sudo systemctl status sapapi

# Test API endpoints
curl http://localhost/api/health
curl http://localhost/docs/

# Check logs
sudo journalctl -u sapapi -f

# Run health check
sapapi-health-check
```

## 📝 Post-Deployment Tasks

### 1. SSL Certificate (Production)
```bash
# Install Certbot SSL certificate
sudo certbot --nginx -d yourdomain.com
```

### 2. Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 3. Backup Setup
```bash
# Test backup functionality
sapapi-backup

# Verify backup files
ls -la /opt/backups/sapapi/
```

### 4. Monitoring Setup
```bash
# Verify monitoring scripts
sapapi-status
sapapi-health-check
```

## 🔧 Troubleshooting

### Common Issues

**Service won't start:**
```bash
sudo systemctl status sapapi
sudo journalctl -u sapapi -n 50
```

**Database connection issues:**
```bash
sudo systemctl status postgresql
sudo -u postgres psql -d sapdwh -c "SELECT 1;"
```

**Nginx configuration issues:**
```bash
sudo nginx -t
sudo systemctl status nginx
```

### Log Locations
- Application: `/var/log/sapapi/`
- Nginx: `/var/log/nginx/`
- PostgreSQL: `/var/log/postgresql/`
- System: `journalctl -u sapapi`

## 📞 Support

### Getting Help
1. Check `DEPLOYMENT_GUIDE.md` untuk detailed instructions
2. Review log files untuk error messages
3. Run diagnostic scripts (`sapapi-health-check`)
4. Check system resources (`htop`, `df -h`)

### Performance Tuning
- Adjust Gunicorn workers berdasarkan CPU cores
- Tune PostgreSQL configuration
- Configure Nginx caching
- Monitor system resources

## 🔄 Updates

### Application Updates
```bash
# Stop service
sudo systemctl stop sapapi

# Backup database
sapapi-backup

# Update code
sudo -u sapapi git -C /opt/sapapi pull

# Update dependencies
sudo -u sapapi /opt/sapapi/venv/bin/pip install -r /opt/sapapi/requirements.txt

# Restart service
sudo systemctl start sapapi

# Verify
sapapi-health-check
```

### System Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services if needed
sudo systemctl restart sapapi nginx postgresql
```