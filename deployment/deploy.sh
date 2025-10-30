#!/bin/bash

# SAP API Deployment Script for Ubuntu Server
# Version: 1.0
# Description: Complete deployment script for SAP API Flask application

set -e  # Exit on any error

# Configuration variables
APP_NAME="sapapi"
APP_USER="sapapi"
APP_GROUP="sapapi"
APP_HOME="/opt/sapapi"
APP_REPO="https://github.com/ketutoka/sapapi.git"  # Update with your actual repo
PYTHON_VERSION="3.11"
DOMAIN_NAME="your-domain.com"  # Update with your domain

# Database configuration
DB_NAME="sapdwh"
DB_USER="sapapi_user"
DB_PASSWORD=""  # Will be generated

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Update system packages
update_system() {
    log "Updating system packages..."
    apt update
    apt upgrade -y
    apt autoremove -y
    apt autoclean
}

# Install required system packages
install_system_packages() {
    log "Installing system packages..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        postgresql \
        postgresql-contrib \
        nginx \
        supervisor \
        certbot \
        python3-certbot-nginx \
        htop \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        fail2ban \
        ufw
}

# Create application user
create_app_user() {
    log "Creating application user..."
    if ! id "$APP_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d "$APP_HOME" -m "$APP_USER"
        usermod -aG "$APP_GROUP" "$APP_USER" 2>/dev/null || groupadd "$APP_GROUP" && usermod -aG "$APP_GROUP" "$APP_USER"
        log "User $APP_USER created successfully"
    else
        warning "User $APP_USER already exists"
    fi
}

# Setup PostgreSQL
setup_postgresql() {
    log "Setting up PostgreSQL..."
    
    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # Generate database password
    if [[ -z "$DB_PASSWORD" ]]; then
        DB_PASSWORD=$(generate_password)
        log "Generated database password: $DB_PASSWORD"
    fi
    
    # Create database and user
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null || warning "User $DB_USER might already exist"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || warning "Database $DB_NAME might already exist"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    
    # Configure PostgreSQL for better performance
    PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -o '[0-9]\+\.[0-9]\+' | head -1)
    PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
    
    if [[ -f "$PG_CONFIG" ]]; then
        cp "$PG_CONFIG" "$PG_CONFIG.backup"
        
        # Update PostgreSQL configuration
        sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" "$PG_CONFIG"
        sed -i "s/#max_connections = 100/max_connections = 200/" "$PG_CONFIG"
        sed -i "s/#shared_buffers = 128MB/shared_buffers = 256MB/" "$PG_CONFIG"
        sed -i "s/#effective_cache_size = 4GB/effective_cache_size = 1GB/" "$PG_CONFIG"
        sed -i "s/#work_mem = 4MB/work_mem = 8MB/" "$PG_CONFIG"
        
        systemctl restart postgresql
        log "PostgreSQL configured and restarted"
    fi
}

# Clone and setup application
setup_application() {
    log "Setting up application..."
    
    # Create application directory
    mkdir -p "$APP_HOME"
    mkdir -p /var/log/sapapi
    chown -R "$APP_USER:$APP_GROUP" "$APP_HOME"
    chown -R "$APP_USER:$APP_GROUP" /var/log/sapapi
    
    # Clone repository as app user
    if [[ ! -d "$APP_HOME/.git" ]]; then
        sudo -u "$APP_USER" git clone "$APP_REPO" "$APP_HOME"
    else
        sudo -u "$APP_USER" git -C "$APP_HOME" pull
    fi
    
    # Create Python virtual environment
    sudo -u "$APP_USER" python3 -m venv "$APP_HOME/venv"
    
    # Install Python dependencies
    sudo -u "$APP_USER" "$APP_HOME/venv/bin/pip" install --upgrade pip
    sudo -u "$APP_USER" "$APP_HOME/venv/bin/pip" install -r "$APP_HOME/requirements.txt"
    
    # Create production environment file
    cat > "$APP_HOME/.env" << EOF
# Production Environment Configuration
FLASK_ENV=production
DEBUG=false
HOST=127.0.0.1
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME

# Security
SECRET_KEY=$(generate_password)

# Logging
LOG_LEVEL=INFO
EOF
    
    chown "$APP_USER:$APP_GROUP" "$APP_HOME/.env"
    chmod 600 "$APP_HOME/.env"
    
    log "Application setup completed"
}

# Setup systemd service
setup_systemd_service() {
    log "Setting up systemd service..."
    
    # Copy service file to systemd directory
    if [[ -f "$APP_HOME/deployment/sapapi.service" ]]; then
        # Update service file with actual database password
        sed "s/your_password/$DB_PASSWORD/g" "$APP_HOME/deployment/sapapi.service" > /etc/systemd/system/sapapi.service
        sed -i "s/your-production-secret-key-change-this/$(generate_password)/g" /etc/systemd/system/sapapi.service
    else
        error "Service file not found at $APP_HOME/deployment/sapapi.service"
        exit 1
    fi
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable sapapi
    
    log "Systemd service configured"
}

# Setup Nginx
setup_nginx() {
    log "Setting up Nginx..."
    
    # Copy nginx configuration
    if [[ -f "$APP_HOME/deployment/nginx-sapapi.conf" ]]; then
        cp "$APP_HOME/deployment/nginx-sapapi.conf" /etc/nginx/sites-available/sapapi
        
        # Update domain name in config
        sed -i "s/your-domain.com/$DOMAIN_NAME/g" /etc/nginx/sites-available/sapapi
        
        # Enable site
        ln -sf /etc/nginx/sites-available/sapapi /etc/nginx/sites-enabled/
        
        # Remove default site
        rm -f /etc/nginx/sites-enabled/default
        
        # Add rate limiting to nginx.conf if not exists
        if ! grep -q "limit_req_zone" /etc/nginx/nginx.conf; then
            sed -i '/http {/a\\tlimit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;' /etc/nginx/nginx.conf
        fi
        
        # Test nginx configuration
        nginx -t
        systemctl restart nginx
        systemctl enable nginx
        
        log "Nginx configured and started"
    else
        error "Nginx configuration file not found"
        exit 1
    fi
}

# Setup SSL with Certbot
setup_ssl() {
    log "Setting up SSL certificate..."
    
    if [[ "$DOMAIN_NAME" != "your-domain.com" ]]; then
        # Get SSL certificate
        certbot --nginx -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME" --non-interactive --agree-tos --email "admin@$DOMAIN_NAME"
        
        # Setup auto-renewal
        systemctl enable certbot.timer
        systemctl start certbot.timer
        
        log "SSL certificate installed and auto-renewal configured"
    else
        warning "Please update DOMAIN_NAME variable and re-run SSL setup"
    fi
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Reset UFW
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 'Nginx Full'
    
    # Allow PostgreSQL only from localhost
    ufw allow from 127.0.0.1 to any port 5432
    
    # Enable firewall
    ufw --force enable
    
    log "Firewall configured"
}

# Setup fail2ban
setup_fail2ban() {
    log "Setting up Fail2ban..."
    
    # Create nginx jail
    cat > /etc/fail2ban/jail.d/nginx.conf << 'EOF'
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 600
bantime = 7200

[nginx-botsearch]
enabled = true
port = http,https
logpath = /var/log/nginx/access.log
maxretry = 2
EOF
    
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log "Fail2ban configured"
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    # Run database initialization as app user
    sudo -u "$APP_USER" bash -c "
        cd '$APP_HOME'
        source venv/bin/activate
        python3 -c '
from app import app, db
with app.app_context():
    db.create_all()
    print(\"Database tables created successfully\")
'
    "
    
    log "Database initialized"
}

# Start services
start_services() {
    log "Starting services..."
    
    # Start application
    systemctl start sapapi
    
    # Check if service started successfully
    sleep 5
    if systemctl is-active --quiet sapapi; then
        log "SAP API service started successfully"
    else
        error "Failed to start SAP API service"
        systemctl status sapapi
        exit 1
    fi
    
    # Show service status
    systemctl status sapapi --no-pager
}

# Create backup script
create_backup_script() {
    log "Creating backup script..."
    
    cat > /usr/local/bin/sapapi-backup << 'EOF'
#!/bin/bash

# SAP API Backup Script
BACKUP_DIR="/opt/backups/sapapi"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="sapdwh"
DB_USER="sapapi_user"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
sudo -u postgres pg_dump "$DB_NAME" | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Application backup
tar -czf "$BACKUP_DIR/app_backup_$DATE.tar.gz" -C /opt sapapi --exclude="sapapi/venv" --exclude="sapapi/.git"

# Keep only last 7 days of backups
find "$BACKUP_DIR" -type f -mtime +7 -delete

echo "Backup completed: $DATE"
EOF
    
    chmod +x /usr/local/bin/sapapi-backup
    
    # Add to crontab
    echo "0 2 * * * /usr/local/bin/sapapi-backup" | crontab -
    
    log "Backup script created and scheduled"
}

# Create monitoring script
create_monitoring_script() {
    log "Creating monitoring script..."
    
    cat > /usr/local/bin/sapapi-monitor << 'EOF'
#!/bin/bash

# SAP API Monitoring Script
SERVICE_NAME="sapapi"
HEALTH_URL="http://127.0.0.1:8000/api/health"
LOG_FILE="/var/log/sapapi/monitor.log"

# Check service status
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "$(date): Service $SERVICE_NAME is not running. Attempting restart..." >> "$LOG_FILE"
    systemctl restart "$SERVICE_NAME"
    sleep 10
fi

# Check HTTP health endpoint
if ! curl -f -s "$HEALTH_URL" > /dev/null; then
    echo "$(date): Health check failed for $HEALTH_URL" >> "$LOG_FILE"
    systemctl restart "$SERVICE_NAME"
fi

# Check disk space
DISK_USAGE=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "$(date): Disk usage is at ${DISK_USAGE}%" >> "$LOG_FILE"
fi
EOF
    
    chmod +x /usr/local/bin/sapapi-monitor
    
    # Add to crontab (every 5 minutes)
    echo "*/5 * * * * /usr/local/bin/sapapi-monitor" | crontab -
    
    log "Monitoring script created and scheduled"
}

# Display deployment summary
display_summary() {
    log "Deployment completed successfully!"
    
    echo ""
    echo "==================================="
    echo "SAP API Deployment Summary"
    echo "==================================="
    echo "Application URL: https://$DOMAIN_NAME"
    echo "API Documentation: https://$DOMAIN_NAME/docs/"
    echo "Health Check: https://$DOMAIN_NAME/api/health"
    echo ""
    echo "Database Information:"
    echo "  Host: localhost"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo "  Password: $DB_PASSWORD"
    echo ""
    echo "Service Management:"
    echo "  Start: sudo systemctl start sapapi"
    echo "  Stop: sudo systemctl stop sapapi"
    echo "  Restart: sudo systemctl restart sapapi"
    echo "  Status: sudo systemctl status sapapi"
    echo "  Logs: sudo journalctl -u sapapi -f"
    echo ""
    echo "Application Logs:"
    echo "  Access: /var/log/sapapi/access.log"
    echo "  Error: /var/log/sapapi/error.log"
    echo "  Monitor: /var/log/sapapi/monitor.log"
    echo ""
    echo "Backup: /usr/local/bin/sapapi-backup"
    echo "Monitor: /usr/local/bin/sapapi-monitor"
    echo "==================================="
}

# Main deployment function
main() {
    log "Starting SAP API deployment..."
    
    check_root
    update_system
    install_system_packages
    create_app_user
    setup_postgresql
    setup_application
    initialize_database
    setup_systemd_service
    setup_nginx
    setup_firewall
    setup_fail2ban
    start_services
    create_backup_script
    create_monitoring_script
    
    # SSL setup (optional, comment out if not needed)
    # setup_ssl
    
    display_summary
}

# Run main function
main "$@"