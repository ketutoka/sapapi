#!/bin/bash

# SAP API Service Troubleshooting Script
# Run this script to diagnose service startup issues

echo "=== SAP API Service Troubleshooting ==="
echo "Date: $(date)"
echo ""

# Check 1: Service status
echo "1. Service Status:"
echo "=================="
systemctl status sapapi.service --no-pager -l
echo ""

# Check 2: Detailed logs
echo "2. Recent Service Logs:"
echo "======================="
journalctl -u sapapi.service -n 20 --no-pager
echo ""

# Check 3: Check if user exists
echo "3. User Check:"
echo "=============="
if id sapapi >/dev/null 2>&1; then
    echo "✓ User 'sapapi' exists"
    echo "  Home: $(getent passwd sapapi | cut -d: -f6)"
    echo "  Shell: $(getent passwd sapapi | cut -d: -f7)"
else
    echo "✗ User 'sapapi' does not exist"
fi
echo ""

# Check 4: Check working directory
echo "4. Working Directory Check:"
echo "==========================="
if [ -d "/opt/sapapi" ]; then
    echo "✓ Directory /opt/sapapi exists"
    echo "  Owner: $(stat -c '%U:%G' /opt/sapapi)"
    echo "  Permissions: $(stat -c '%a' /opt/sapapi)"
    ls -la /opt/sapapi/
else
    echo "✗ Directory /opt/sapapi does not exist"
fi
echo ""

# Check 5: Check virtual environment
echo "5. Virtual Environment Check:"
echo "============================="
if [ -f "/opt/sapapi/venv/bin/python" ]; then
    echo "✓ Virtual environment exists"
    echo "  Python version: $(/opt/sapapi/venv/bin/python --version)"
    echo "  Gunicorn installed: "
    /opt/sapapi/venv/bin/pip show gunicorn 2>/dev/null || echo "  ✗ Gunicorn not installed"
else
    echo "✗ Virtual environment not found"
fi
echo ""

# Check 6: Check app.py file
echo "6. Application File Check:"
echo "=========================="
if [ -f "/opt/sapapi/app.py" ]; then
    echo "✓ app.py exists"
    echo "  Size: $(stat -c '%s bytes' /opt/sapapi/app.py)"
    echo "  Last modified: $(stat -c '%y' /opt/sapapi/app.py)"
else
    echo "✗ app.py not found"
fi
echo ""

# Check 7: Check .env file
echo "7. Environment File Check:"
echo "=========================="
if [ -f "/opt/sapapi/.env" ]; then
    echo "✓ .env file exists"
    echo "  Owner: $(stat -c '%U:%G' /opt/sapapi/.env)"
    echo "  Permissions: $(stat -c '%a' /opt/sapapi/.env)"
    echo "  Variables (without values):"
    grep -v '^#' /opt/sapapi/.env | grep '=' | cut -d'=' -f1 | sed 's/^/    /'
else
    echo "✗ .env file not found"
fi
echo ""

# Check 8: Check database connectivity
echo "8. Database Connectivity Check:"
echo "==============================="
if command -v psql >/dev/null 2>&1; then
    echo "✓ PostgreSQL client available"
    if sudo -u postgres psql -c "SELECT 1;" >/dev/null 2>&1; then
        echo "✓ PostgreSQL server is running"
        # Check if database exists
        if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw sapdwh; then
            echo "✓ Database 'sapdwh' exists"
        else
            echo "✗ Database 'sapdwh' does not exist"
        fi
    else
        echo "✗ PostgreSQL server is not accessible"
    fi
else
    echo "✗ PostgreSQL client not installed"
fi
echo ""

# Check 9: Port availability
echo "9. Port Availability Check:"
echo "==========================="
if netstat -tlnp | grep -q ":8000 "; then
    echo "✗ Port 8000 is already in use:"
    netstat -tlnp | grep ":8000 "
else
    echo "✓ Port 8000 is available"
fi
echo ""

# Check 10: Log files
echo "10. Log Files Check:"
echo "==================="
if [ -d "/var/log/sapapi" ]; then
    echo "✓ Log directory exists"
    echo "  Owner: $(stat -c '%U:%G' /var/log/sapapi)"
    echo "  Files:"
    ls -la /var/log/sapapi/
    
    # Show recent error logs if exists
    if [ -f "/var/log/sapapi/error.log" ]; then
        echo ""
        echo "Recent error log entries:"
        tail -10 /var/log/sapapi/error.log
    fi
else
    echo "✗ Log directory /var/log/sapapi does not exist"
fi
echo ""

# Check 11: Try manual start
echo "11. Manual Start Test:"
echo "======================"
echo "Attempting to start application manually..."
cd /opt/sapapi
if sudo -u sapapi /opt/sapapi/venv/bin/python app.py --help >/dev/null 2>&1; then
    echo "✓ Application can be imported successfully"
else
    echo "✗ Application import failed. Trying to get error details:"
    sudo -u sapapi /opt/sapapi/venv/bin/python -c "import app" 2>&1 || true
fi
echo ""

echo "=== Troubleshooting Complete ==="
echo ""
echo "Recommendations:"
echo "1. Check the error logs above for specific issues"
echo "2. Verify all dependencies are installed"
echo "3. Ensure database is configured correctly"
echo "4. Check file permissions and ownership"
echo "5. Try manual start with: sudo -u sapapi /opt/sapapi/venv/bin/gunicorn app:app"