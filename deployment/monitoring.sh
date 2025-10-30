#!/bin/bash

# SAP API Service Monitoring and Health Check Scripts
# Collection of monitoring utilities for production deployment

# Health Check Script
create_health_check() {
    cat > /usr/local/bin/sapapi-health-check << 'EOF'
#!/bin/bash

# SAP API Health Check Script
# Checks service status, database connectivity, and API endpoints

SERVICE_NAME="sapapi"
API_BASE_URL="http://127.0.0.1:8000"
LOG_FILE="/var/log/sapapi/health-check.log"
ALERT_EMAIL="admin@yourdomain.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging function
log() {
    echo -e "$(date +'%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check systemd service
check_service() {
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log "${GREEN}✓ Service $SERVICE_NAME is running${NC}"
        return 0
    else
        log "${RED}✗ Service $SERVICE_NAME is not running${NC}"
        return 1
    fi
}

# Check API health endpoint
check_api_health() {
    local response
    local status_code
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE_URL/api/health" --max-time 10)
    
    if [[ "$response" == "200" ]]; then
        log "${GREEN}✓ API health endpoint is responding (HTTP $response)${NC}"
        return 0
    else
        log "${RED}✗ API health endpoint failed (HTTP $response)${NC}"
        return 1
    fi
}

# Check database connectivity through API
check_database() {
    local response
    local status_code
    
    response=$(curl -s "$API_BASE_URL/api/database/check" --max-time 15)
    
    if echo "$response" | grep -q '"success":true' || echo "$response" | grep -q '"database_connection".*"success":true'; then
        log "${GREEN}✓ Database connectivity is OK${NC}"
        return 0
    else
        log "${RED}✗ Database connectivity failed${NC}"
        log "Response: $response"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    local usage
    local threshold=80
    
    usage=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ "$usage" -lt "$threshold" ]]; then
        log "${GREEN}✓ Disk usage is OK ($usage%)${NC}"
        return 0
    else
        log "${YELLOW}⚠ Disk usage is high ($usage%)${NC}"
        return 1
    fi
}

# Check memory usage
check_memory() {
    local mem_usage
    local threshold=80
    
    mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    
    if [[ "$mem_usage" -lt "$threshold" ]]; then
        log "${GREEN}✓ Memory usage is OK ($mem_usage%)${NC}"
        return 0
    else
        log "${YELLOW}⚠ Memory usage is high ($mem_usage%)${NC}"
        return 1
    fi
}

# Check log file sizes
check_log_sizes() {
    local log_dir="/var/log/sapapi"
    local max_size=$((100 * 1024 * 1024))  # 100MB
    
    for log_file in "$log_dir"/*.log; do
        if [[ -f "$log_file" ]]; then
            local size=$(stat -c%s "$log_file")
            if [[ "$size" -gt "$max_size" ]]; then
                log "${YELLOW}⚠ Log file $log_file is large ($(($size / 1024 / 1024))MB)${NC}"
            fi
        fi
    done
}

# Send alert email
send_alert() {
    local subject="SAP API Health Check Alert"
    local message="$1"
    
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
    fi
}

# Main health check
main() {
    log "Starting health check..."
    
    local errors=0
    
    check_service || ((errors++))
    check_api_health || ((errors++))
    check_database || ((errors++))
    check_disk_space || ((errors++))
    check_memory || ((errors++))
    check_log_sizes
    
    if [[ "$errors" -eq 0 ]]; then
        log "${GREEN}✓ All health checks passed${NC}"
    else
        log "${RED}✗ $errors health checks failed${NC}"
        send_alert "SAP API health check failed with $errors errors. Check $LOG_FILE for details."
    fi
    
    log "Health check completed"
    return $errors
}

# Run health check
main "$@"
EOF

    chmod +x /usr/local/bin/sapapi-health-check
    echo "Health check script created"
}

# Process Monitor Script
create_process_monitor() {
    cat > /usr/local/bin/sapapi-process-monitor << 'EOF'
#!/bin/bash

# SAP API Process Monitor
# Monitors and restarts service if needed

SERVICE_NAME="sapapi"
LOG_FILE="/var/log/sapapi/process-monitor.log"
RESTART_THRESHOLD=3
RESTART_COUNT_FILE="/tmp/sapapi-restart-count"

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

get_restart_count() {
    if [[ -f "$RESTART_COUNT_FILE" ]]; then
        cat "$RESTART_COUNT_FILE"
    else
        echo "0"
    fi
}

increment_restart_count() {
    local count=$(get_restart_count)
    echo $((count + 1)) > "$RESTART_COUNT_FILE"
}

reset_restart_count() {
    echo "0" > "$RESTART_COUNT_FILE"
}

check_and_restart() {
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        local count=$(get_restart_count)
        
        if [[ "$count" -lt "$RESTART_THRESHOLD" ]]; then
            log "Service $SERVICE_NAME is down. Attempting restart (attempt $((count + 1))/$RESTART_THRESHOLD)"
            systemctl restart "$SERVICE_NAME"
            increment_restart_count
            
            sleep 10
            
            if systemctl is-active --quiet "$SERVICE_NAME"; then
                log "Service $SERVICE_NAME restarted successfully"
                reset_restart_count
            else
                log "Service $SERVICE_NAME restart failed"
            fi
        else
            log "Service $SERVICE_NAME restart threshold exceeded. Manual intervention required."
        fi
    else
        reset_restart_count
    fi
}

check_and_restart
EOF

    chmod +x /usr/local/bin/sapapi-process-monitor
    echo "Process monitor script created"
}

# Log Rotation Configuration
create_log_rotation() {
    cat > /etc/logrotate.d/sapapi << 'EOF'
/var/log/sapapi/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 sapapi sapapi
    postrotate
        systemctl reload sapapi 2>/dev/null || true
    endscript
}
EOF

    echo "Log rotation configuration created"
}

# Performance Monitor Script
create_performance_monitor() {
    cat > /usr/local/bin/sapapi-performance-monitor << 'EOF'
#!/bin/bash

# SAP API Performance Monitor
# Collects performance metrics

LOG_FILE="/var/log/sapapi/performance.log"
API_URL="http://127.0.0.1:8000/api/health"

collect_metrics() {
    local timestamp=$(date +'%Y-%m-%d %H:%M:%S')
    
    # System metrics
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local disk_usage=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')
    
    # Process metrics
    local sapapi_cpu=$(ps -C python3 -o %cpu --no-headers | awk '{sum+=$1} END {print sum}')
    local sapapi_mem=$(ps -C python3 -o %mem --no-headers | awk '{sum+=$1} END {print sum}')
    
    # API response time
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' "$API_URL" --max-time 10)
    
    # Database connections (if PostgreSQL)
    local db_connections=""
    if command -v psql >/dev/null 2>&1; then
        db_connections=$(sudo -u postgres psql -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='sapdwh';" 2>/dev/null | tr -d ' ')
    fi
    
    # Log metrics
    echo "$timestamp,CPU:$cpu_usage,MEM:$mem_usage,DISK:$disk_usage,API_CPU:$sapapi_cpu,API_MEM:$sapapi_mem,RESPONSE_TIME:$response_time,DB_CONN:$db_connections" >> "$LOG_FILE"
}

collect_metrics
EOF

    chmod +x /usr/local/bin/sapapi-performance-monitor
    echo "Performance monitor script created"
}

# Backup Health Check
create_backup_monitor() {
    cat > /usr/local/bin/sapapi-backup-monitor << 'EOF'
#!/bin/bash

# SAP API Backup Monitor
# Monitors backup status and alerts if backups are failing

BACKUP_DIR="/opt/backups/sapapi"
LOG_FILE="/var/log/sapapi/backup-monitor.log"
ALERT_EMAIL="admin@yourdomain.com"
MAX_BACKUP_AGE=48  # hours

log() {
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_backup_freshness() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log "ERROR: Backup directory $BACKUP_DIR does not exist"
        return 1
    fi
    
    local latest_backup=$(find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -z "$latest_backup" ]]; then
        log "ERROR: No database backups found"
        return 1
    fi
    
    local backup_age=$(($(date +%s) - $(stat -c %Y "$latest_backup")))
    local backup_age_hours=$((backup_age / 3600))
    
    if [[ "$backup_age_hours" -gt "$MAX_BACKUP_AGE" ]]; then
        log "WARNING: Latest backup is $backup_age_hours hours old (threshold: $MAX_BACKUP_AGE hours)"
        return 1
    else
        log "OK: Latest backup is $backup_age_hours hours old"
        return 0
    fi
}

check_backup_size() {
    local latest_backup=$(find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
    
    if [[ -n "$latest_backup" ]]; then
        local backup_size=$(stat -c%s "$latest_backup")
        local backup_size_mb=$((backup_size / 1024 / 1024))
        
        if [[ "$backup_size_mb" -lt 1 ]]; then
            log "WARNING: Backup file seems too small ($backup_size_mb MB)"
            return 1
        else
            log "OK: Backup size is $backup_size_mb MB"
            return 0
        fi
    fi
    
    return 1
}

main() {
    log "Starting backup monitor check"
    
    local errors=0
    
    check_backup_freshness || ((errors++))
    check_backup_size || ((errors++))
    
    if [[ "$errors" -gt 0 ]]; then
        log "Backup monitor found $errors issues"
        if command -v mail >/dev/null 2>&1; then
            echo "SAP API backup monitoring detected issues. Check $LOG_FILE for details." | mail -s "SAP API Backup Alert" "$ALERT_EMAIL"
        fi
    else
        log "Backup monitor: All checks passed"
    fi
}

main
EOF

    chmod +x /usr/local/bin/sapapi-backup-monitor
    echo "Backup monitor script created"
}

# Setup Cron Jobs
setup_monitoring_cron() {
    cat > /tmp/sapapi-cron << 'EOF'
# SAP API Monitoring Cron Jobs

# Health check every 5 minutes
*/5 * * * * /usr/local/bin/sapapi-health-check >/dev/null 2>&1

# Process monitor every 2 minutes
*/2 * * * * /usr/local/bin/sapapi-process-monitor >/dev/null 2>&1

# Performance monitoring every 10 minutes
*/10 * * * * /usr/local/bin/sapapi-performance-monitor >/dev/null 2>&1

# Backup monitoring daily at 6 AM
0 6 * * * /usr/local/bin/sapapi-backup-monitor >/dev/null 2>&1

# Daily backup at 2 AM
0 2 * * * /usr/local/bin/sapapi-backup >/dev/null 2>&1
EOF

    crontab /tmp/sapapi-cron
    rm /tmp/sapapi-cron
    echo "Monitoring cron jobs installed"
}

# Alerting Configuration
create_alerting_config() {
    cat > /etc/sapapi/alerting.conf << 'EOF'
# SAP API Alerting Configuration

# Email settings
ALERT_EMAIL="admin@yourdomain.com"
SMTP_SERVER="localhost"
SMTP_PORT="25"

# Thresholds
CPU_THRESHOLD="80"
MEMORY_THRESHOLD="80"
DISK_THRESHOLD="80"
RESPONSE_TIME_THRESHOLD="5.0"

# Alert frequency (minutes)
ALERT_COOLDOWN="30"

# Enable/disable alerts
ENABLE_EMAIL_ALERTS="true"
ENABLE_SLACK_ALERTS="false"
SLACK_WEBHOOK_URL=""
EOF

    mkdir -p /etc/sapapi
    echo "Alerting configuration created"
}

# Status Dashboard Script
create_status_dashboard() {
    cat > /usr/local/bin/sapapi-status << 'EOF'
#!/bin/bash

# SAP API Status Dashboard
# Quick overview of system status

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}SAP API System Status Dashboard${NC}"
echo "=================================="

# Service Status
if systemctl is-active --quiet sapapi; then
    echo -e "Service Status: ${GREEN}Running${NC}"
else
    echo -e "Service Status: ${RED}Stopped${NC}"
fi

# API Health
if curl -s -f http://127.0.0.1:8000/api/health >/dev/null; then
    echo -e "API Health: ${GREEN}OK${NC}"
else
    echo -e "API Health: ${RED}Failed${NC}"
fi

# Database Status
if curl -s http://127.0.0.1:8000/api/database/check | grep -q '"success":true'; then
    echo -e "Database: ${GREEN}Connected${NC}"
else
    echo -e "Database: ${RED}Connection Failed${NC}"
fi

# System Resources
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
DISK_USAGE=$(df /opt | tail -1 | awk '{print $5}' | sed 's/%//')

echo "CPU Usage: ${CPU_USAGE}%"
echo "Memory Usage: ${MEM_USAGE}%"
echo "Disk Usage: ${DISK_USAGE}%"

# Recent Logs
echo ""
echo "Recent Error Logs (last 5):"
echo "----------------------------"
tail -5 /var/log/sapapi/error.log 2>/dev/null || echo "No recent errors"

echo ""
echo "Service Uptime:"
echo "---------------"
systemctl status sapapi --no-pager -l | grep "Active:" || echo "Service not running"
EOF

    chmod +x /usr/local/bin/sapapi-status
    echo "Status dashboard script created"
}

# Main function to create all monitoring scripts
main() {
    echo "Creating SAP API monitoring and health check scripts..."
    
    # Create log directory
    mkdir -p /var/log/sapapi
    
    # Create monitoring scripts
    create_health_check
    create_process_monitor
    create_log_rotation
    create_performance_monitor
    create_backup_monitor
    create_alerting_config
    create_status_dashboard
    
    # Setup cron jobs
    setup_monitoring_cron
    
    echo ""
    echo "Monitoring scripts created successfully!"
    echo ""
    echo "Available monitoring commands:"
    echo "  sapapi-health-check     - Comprehensive health check"
    echo "  sapapi-process-monitor  - Process monitoring and restart"
    echo "  sapapi-performance-monitor - Performance metrics collection"
    echo "  sapapi-backup-monitor   - Backup monitoring"
    echo "  sapapi-status          - Quick status dashboard"
    echo ""
    echo "Log files:"
    echo "  /var/log/sapapi/health-check.log"
    echo "  /var/log/sapapi/process-monitor.log"
    echo "  /var/log/sapapi/performance.log"
    echo "  /var/log/sapapi/backup-monitor.log"
    echo ""
    echo "To view real-time status: sapapi-status"
}

# Run if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi