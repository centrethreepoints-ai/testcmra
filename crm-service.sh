#!/bin/bash

# CRM Maroc Service Management Script
# Usage: ./crm-service.sh {start|stop|restart|status|reload|logs|install|uninstall}

SERVICE_NAME="crm-maroc"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
APP_DIR="/opt/app"
VENV_DIR="/opt/app/venv"
USER="master"
GROUP="master"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}=== CRM Maroc Service Management ===${NC}"
}

# Check if running as root for system operations
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This operation requires root privileges. Use sudo."
        exit 1
    fi
}

# Check if service file exists
check_service_file() {
    if [[ ! -f "$SERVICE_FILE" ]]; then
        print_error "Service file not found: $SERVICE_FILE"
        print_warning "Run 'sudo ./crm-service.sh install' first"
        exit 1
    fi
}

# Check if app directory exists
check_app_dir() {
    if [[ ! -d "$APP_DIR" ]]; then
        print_error "Application directory not found: $APP_DIR"
        exit 1
    fi
}

# Check if virtual environment exists
check_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        print_error "Virtual environment not found: $VENV_DIR"
        print_warning "Please create virtual environment first"
        exit 1
    fi
}

# Install service
install_service() {
    check_root
    check_app_dir
    check_venv
    
    print_status "Installing CRM Maroc service..."
    
    # Copy service file
    cp "${SERVICE_NAME}.service" "$SERVICE_FILE"
    
    # Set proper permissions
    chmod 644 "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service
    systemctl enable "$SERVICE_NAME"
    
    print_status "Service installed and enabled successfully!"
    print_status "Use 'sudo ./crm-service.sh start' to start the service"
}

# Uninstall service
uninstall_service() {
    check_root
    
    print_status "Uninstalling CRM Maroc service..."
    
    # Stop service if running
    systemctl stop "$SERVICE_NAME" 2>/dev/null
    
    # Disable service
    systemctl disable "$SERVICE_NAME" 2>/dev/null
    
    # Remove service file
    rm -f "$SERVICE_FILE"
    
    # Reload systemd
    systemctl daemon-reload
    
    print_status "Service uninstalled successfully!"
}

# Start service
start_service() {
    check_root
    check_service_file
    
    print_status "Starting CRM Maroc service..."
    
    systemctl start "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service started successfully!"
        print_status "Access your application at: http://$(hostname -I | awk '{print $1}'):8000"
    else
        print_error "Failed to start service!"
        systemctl status "$SERVICE_NAME" --no-pager -l
        exit 1
    fi
}

# Stop service
stop_service() {
    check_root
    check_service_file
    
    print_status "Stopping CRM Maroc service..."
    
    systemctl stop "$SERVICE_NAME"
    
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service stopped successfully!"
    else
        print_error "Failed to stop service!"
        exit 1
    fi
}

# Restart service
restart_service() {
    check_root
    check_service_file
    
    print_status "Restarting CRM Maroc service..."
    
    systemctl restart "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service restarted successfully!"
    else
        print_error "Failed to restart service!"
        systemctl status "$SERVICE_NAME" --no-pager -l
        exit 1
    fi
}

# Reload service
reload_service() {
    check_root
    check_service_file
    
    print_status "Reloading CRM Maroc service..."
    
    systemctl reload "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_status "Service reloaded successfully!"
    else
        print_error "Failed to reload service!"
        exit 1
    fi
}

# Show service status
show_status() {
    check_service_file
    
    print_status "CRM Maroc Service Status:"
    echo "----------------------------------------"
    
    # Show systemd status
    systemctl status "$SERVICE_NAME" --no-pager -l
    
    echo "----------------------------------------"
    
    # Show if port is listening
    if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
        print_status "Port 8000 is listening"
        netstat -tlnp 2>/dev/null | grep ":8000 "
    else
        print_warning "Port 8000 is not listening"
    fi
    
    # Show process info
    echo "----------------------------------------"
    print_status "Process Information:"
    ps aux | grep "runserver.*8000" | grep -v grep || print_warning "No Django process found"
}

# Show service logs
show_logs() {
    check_service_file
    
    print_status "Showing CRM Maroc service logs..."
    
    if command -v journalctl >/dev/null 2>&1; then
        journalctl -u "$SERVICE_NAME" -f --no-pager
    else
        print_warning "journalctl not available, showing recent logs from systemd:"
        systemctl status "$SERVICE_NAME" --no-pager -l
    fi
}

# Show help
show_help() {
    print_header
    echo "Usage: $0 {start|stop|restart|status|reload|logs|install|uninstall|help}"
    echo ""
    echo "Commands:"
    echo "  start     - Start the CRM Maroc service"
    echo "  stop      - Stop the CRM Maroc service"
    echo "  restart   - Restart the CRM Maroc service"
    echo "  status    - Show service status and information"
    echo "  reload    - Reload the service configuration"
    echo "  logs      - Show service logs (follow mode)"
    echo "  install   - Install the service (requires root)"
    echo "  uninstall - Uninstall the service (requires root)"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  sudo ./crm-service.sh install"
    echo "  sudo ./crm-service.sh start"
    echo "  ./crm-service.sh status"
    echo "  sudo ./crm-service.sh restart"
}

# Main script logic
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    reload)
        reload_service
        ;;
    logs)
        show_logs
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Invalid command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
