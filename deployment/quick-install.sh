#!/bin/bash

# SAP API Quick Install Script for Ubuntu
# Simplified installation for quick setup

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)"
    exit 1
fi

log "Starting SAP API Quick Installation..."

# Update system
log "Updating system packages..."
apt update
apt upgrade -y

# Install essential packages
log "Installing essential packages..."
apt install -y python3 python3-pip python3-venv python3-dev \
               postgresql postgresql-contrib nginx git curl

# Create app user
log "Creating application user..."
useradd -r -s /bin/bash -d /opt/sapapi -m sapapi 2>/dev/null || warning "User already exists"

# Setup PostgreSQL
log "Setting up PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Create database
sudo -u postgres psql -c "CREATE USER sapapi_user WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || warning "Database user might already exist"
sudo -u postgres psql -c "CREATE DATABASE sapdwh OWNER sapapi_user;" 2>/dev/null || warning "Database might already exist"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE sapdwh TO sapapi_user;"

# Clone application (assuming it's in current directory or download from git)
if [[ ! -d "/opt/sapapi/app.py" ]]; then
    log "Setting up application..."
    cp -r . /opt/sapapi/
    chown -R sapapi:sapapi /opt/sapapi
fi

# Create virtual environment and install dependencies
log "Setting up Python environment..."
sudo -u sapapi python3 -m venv /opt/sapapi/venv
sudo -u sapapi /opt/sapapi/venv/bin/pip install --upgrade pip
sudo -u sapapi /opt/sapapi/venv/bin/pip install -r /opt/sapapi/requirements.txt

# Create environment file
log "Creating environment configuration..."
cat > /opt/sapapi/.env << EOF
FLASK_ENV=production
DEBUG=false
HOST=127.0.0.1
PORT=8000
DATABASE_URL=postgresql://sapapi_user:$DB_PASSWORD@localhost:5432/sapdwh
SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
LOG_LEVEL=INFO
EOF

chown sapapi:sapapi /opt/sapapi/.env
chmod 600 /opt/sapapi/.env

# Initialize database
log "Initializing database..."
sudo -u sapapi bash -c "
    cd /opt/sapapi
    source venv/bin/activate
    python3 -c 'from app import app, db; app.app_context().push(); db.create_all(); print(\"Database initialized\")'
"

# Create simple systemd service
log "Creating systemd service..."
cat > /etc/systemd/system/sapapi.service << EOF
[Unit]
Description=SAP API Flask Application
After=network.target postgresql.service

[Service]
Type=exec
User=sapapi
Group=sapapi
WorkingDirectory=/opt/sapapi
Environment=PATH=/opt/sapapi/venv/bin
ExecStart=/opt/sapapi/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 2 app:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create basic nginx config
log "Configuring Nginx..."
cat > /etc/nginx/sites-available/sapapi << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable nginx site
ln -sf /etc/nginx/sites-available/sapapi /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Start services
log "Starting services..."
systemctl daemon-reload
systemctl enable sapapi
systemctl start sapapi
systemctl restart nginx
systemctl enable nginx

# Wait and check status
sleep 5

if systemctl is-active --quiet sapapi; then
    log "✓ SAP API service is running"
else
    error "✗ SAP API service failed to start"
    systemctl status sapapi
    exit 1
fi

if systemctl is-active --quiet nginx; then
    log "✓ Nginx is running"
else
    error "✗ Nginx failed to start"
    systemctl status nginx
    exit 1
fi

# Test API
log "Testing API..."
sleep 2
if curl -s -f http://localhost/api/health > /dev/null; then
    log "✓ API is responding"
else
    warning "⚠ API might not be fully ready yet"
fi

# Display summary
log "Installation completed successfully!"
echo ""
echo "=================================="
echo "SAP API Installation Summary"
echo "=================================="
echo "API URL: http://$(hostname -I | awk '{print $1}')"
echo "Documentation: http://$(hostname -I | awk '{print $1}')/docs/"
echo "Health Check: http://$(hostname -I | awk '{print $1}')/api/health"
echo ""
echo "Database Credentials:"
echo "  Host: localhost"
echo "  Database: sapdwh"
echo "  User: sapapi_user"
echo "  Password: $DB_PASSWORD"
echo ""
echo "Service Management:"
echo "  Status: sudo systemctl status sapapi"
echo "  Restart: sudo systemctl restart sapapi"
echo "  Logs: sudo journalctl -u sapapi -f"
echo ""
echo "Next Steps:"
echo "1. Update your domain name in /etc/nginx/sites-available/sapapi"
echo "2. Setup SSL certificate with: sudo certbot --nginx"
echo "3. Configure firewall: sudo ufw allow 'Nginx Full'"
echo "=================================="