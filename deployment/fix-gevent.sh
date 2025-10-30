#!/bin/bash

# Quick Fix for SAP API Gevent Issue
# This script fixes the "gevent not found" error

echo "🔧 SAP API Gevent Fix"
echo "====================="

# Check if we're running as root
if [[ $EUID -ne 0 ]]; then
    echo "❌ This script must be run as root (use sudo)"
    exit 1
fi

# Stop service first
echo "⏹️  Stopping SAP API service..."
systemctl stop sapapi

# Option 1: Install gevent
echo "📦 Installing gevent..."
sudo -u sapapi /opt/sapapi/venv/bin/pip install gevent>=22.10.0

# Check if installation was successful
if sudo -u sapapi /opt/sapapi/venv/bin/python -c "import gevent; print('✅ Gevent version:', gevent.__version__)" 2>/dev/null; then
    echo "✅ Gevent installed successfully!"
    
    # Update service file to use gevent (optimal performance)
    echo "🔄 Updating service configuration for gevent..."
    
    # Create updated service file with gevent
    cat > /etc/systemd/system/sapapi.service << 'EOF'
[Unit]
Description=SAP API Flask Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=sapapi
Group=sapapi
WorkingDirectory=/opt/sapapi

# System-level critical environment variables
Environment=PATH=/opt/sapapi/venv/bin
Environment=FLASK_ENV=production
Environment=DEBUG=false

# Load additional environment variables from .env file
EnvironmentFile=/opt/sapapi/.env

# Gunicorn with gevent for high performance
ExecStart=/opt/sapapi/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile /var/log/sapapi/access.log \
    --error-logfile /var/log/sapapi/error.log \
    app:app

# Restart policy
Restart=always
RestartSec=3
StartLimitBurst=3
StartLimitInterval=60s

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/sapapi
ReadWritePaths=/opt/sapapi

# Resource limits
LimitNOFILE=65535
LimitNPROC=4096

# Health check
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ Service configured to use gevent worker"
    
else
    echo "⚠️  Gevent installation failed, using sync worker instead..."
    
    # Create service file with sync worker (fallback)
    cat > /etc/systemd/system/sapapi.service << 'EOF'
[Unit]
Description=SAP API Flask Application
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=exec
User=sapapi
Group=sapapi
WorkingDirectory=/opt/sapapi

# System-level critical environment variables
Environment=PATH=/opt/sapapi/venv/bin
Environment=FLASK_ENV=production
Environment=DEBUG=false

# Load additional environment variables from .env file
EnvironmentFile=/opt/sapapi/.env

# Gunicorn with sync worker (stable fallback)
ExecStart=/opt/sapapi/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --threads 2 \
    --worker-class sync \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile /var/log/sapapi/access.log \
    --error-logfile /var/log/sapapi/error.log \
    app:app

# Restart policy
Restart=always
RestartSec=3
StartLimitBurst=3
StartLimitInterval=60s

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/sapapi
ReadWritePaths=/opt/sapapi

# Resource limits
LimitNOFILE=65535
LimitNPROC=4096

# Health check
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "✅ Service configured to use sync worker"
fi

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Start service
echo "🚀 Starting SAP API service..."
systemctl start sapapi

# Wait a moment for service to start
sleep 3

# Check service status
echo "📊 Checking service status..."
if systemctl is-active --quiet sapapi; then
    echo "✅ SAP API service is now running!"
    echo ""
    echo "📋 Service Status:"
    systemctl status sapapi --no-pager -l
    echo ""
    echo "🌐 Testing API endpoint..."
    if curl -s -f http://127.0.0.1:8000/api/health >/dev/null; then
        echo "✅ API is responding correctly!"
        echo "🎉 Fix completed successfully!"
    else
        echo "⚠️  Service is running but API might need a moment to be ready"
        echo "💡 Try: curl http://127.0.0.1:8000/api/health"
    fi
else
    echo "❌ Service failed to start. Checking logs..."
    echo ""
    echo "📋 Recent logs:"
    journalctl -u sapapi -n 10 --no-pager
    echo ""
    echo "💡 Try running the troubleshoot script for more details"
fi

echo ""
echo "🔧 Fix Summary:"
echo "- Gevent installation: $(sudo -u sapapi /opt/sapapi/venv/bin/python -c 'import gevent; print("SUCCESS")' 2>/dev/null || echo 'FAILED - using sync worker')"
echo "- Service configuration: Updated"
echo "- Service status: $(systemctl is-active sapapi)"
echo ""
echo "📖 Useful commands:"
echo "  sudo systemctl status sapapi"
echo "  sudo systemctl restart sapapi"  
echo "  sudo journalctl -u sapapi -f"
echo "  curl http://127.0.0.1:8000/api/health"