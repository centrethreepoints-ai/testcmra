#!/bin/bash

# Test script for CRM Maroc service
# This script tests various aspects of the service

echo "🧪 Testing CRM Maroc Service..."
echo "=================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Test 1: Service status
echo -e "\n${YELLOW}1. Testing service status...${NC}"
if systemctl is-active --quiet crm-maroc; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service is not running${NC}"
    exit 1
fi

# Test 2: Port listening
echo -e "\n${YELLOW}2. Testing port 8000...${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo -e "${GREEN}✓ Port 8000 is listening${NC}"
    netstat -tlnp 2>/dev/null | grep ":8000 "
else
    echo -e "${RED}✗ Port 8000 is not listening${NC}"
    exit 1
fi

# Test 3: HTTP response
echo -e "\n${YELLOW}3. Testing HTTP response...${NC}"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [[ "$HTTP_RESPONSE" == "302" ]] || [[ "$HTTP_RESPONSE" == "200" ]]; then
    echo -e "${GREEN}✓ HTTP response: $HTTP_RESPONSE (OK)${NC}"
else
    echo -e "${RED}✗ HTTP response: $HTTP_RESPONSE (Unexpected)${NC}"
    exit 1
fi

# Test 4: Application accessibility
echo -e "\n${YELLOW}4. Testing application accessibility...${NC}"
if curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✓ Application is accessible${NC}"
else
    echo -e "${RED}✗ Application is not accessible${NC}"
    exit 1
fi

# Test 5: Process information
echo -e "\n${YELLOW}5. Testing process information...${NC}"
PROCESS_COUNT=$(ps aux | grep "runserver.*8000" | grep -v grep | wc -l)
if [[ $PROCESS_COUNT -gt 0 ]]; then
    echo -e "${GREEN}✓ Django process found (count: $PROCESS_COUNT)${NC}"
    ps aux | grep "runserver.*8000" | grep -v grep
else
    echo -e "${RED}✗ No Django process found${NC}"
    exit 1
fi

# Test 6: Logs accessibility
echo -e "\n${YELLOW}6. Testing logs accessibility...${NC}"
if journalctl -u crm-maroc --no-pager -n 5 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Service logs are accessible${NC}"
    echo "Recent logs:"
    journalctl -u crm-maroc --no-pager -n 3
else
    echo -e "${YELLOW}⚠ Service logs not accessible (may need sudo)${NC}"
fi

# Test 7: Service configuration
echo -e "\n${YELLOW}7. Testing service configuration...${NC}"
if [[ -f "/etc/systemd/system/crm-maroc.service" ]]; then
    echo -e "${GREEN}✓ Service file exists${NC}"
    echo "Service file permissions:"
    ls -la /etc/systemd/system/crm-maroc.service
else
    echo -e "${RED}✗ Service file not found${NC}"
    exit 1
fi

# Test 8: Auto-start configuration
echo -e "\n${YELLOW}8. Testing auto-start configuration...${NC}"
if systemctl is-enabled --quiet crm-maroc; then
    echo -e "${GREEN}✓ Service is enabled (will start on boot)${NC}"
else
    echo -e "${YELLOW}⚠ Service is not enabled (will not start on boot)${NC}"
fi

echo -e "\n${GREEN}==================================${NC}"
echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
echo -e "${GREEN}Your CRM Maroc service is working properly.${NC}"
echo -e "\n${YELLOW}Access your application at:${NC}"
echo -e "  Local:  http://localhost:8000"
echo -e "  Network: http://$(hostname -I | awk '{print $1}'):8000"
echo -e "  VM:      http://10.10.10.15:8000"
echo -e "\n${YELLOW}Useful commands:${NC}"
echo -e "  Status:  ./crmctl status"
echo -e "  Restart: ./crmctl restart"
echo -e "  Stop:    ./crmctl stop"
echo -e "  Start:   ./crmctl start"
