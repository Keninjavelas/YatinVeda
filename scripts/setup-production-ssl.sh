#!/bin/bash
# ============================================================
# Production SSL Certificate Setup Script
# Uses Let's Encrypt with Certbot for real SSL certificates
# ============================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== YatinVeda Production SSL Setup ===${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
    exit 1
fi

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}Certbot not found. Installing...${NC}"
    
    # Detect OS and install certbot
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        apt-get update
        apt-get install -y certbot
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS
        yum install -y certbot
    else
        echo -e "${RED}Unsupported OS. Please install certbot manually:${NC}"
        echo "Visit: https://certbot.eff.org/"
        exit 1
    fi
fi

# Load environment variables
if [ -f .env ]; then
    source <(grep -E '^(PRODUCTION_DOMAINS|LETSENCRYPT_EMAIL)=' .env)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Validate required variables
if [ -z "$PRODUCTION_DOMAINS" ] || [ "$PRODUCTION_DOMAINS" == "yourdomain.com,www.yourdomain.com" ]; then
    echo -e "${RED}Error: PRODUCTION_DOMAINS not configured in .env${NC}"
    echo "Please update PRODUCTION_DOMAINS with your actual domain(s)"
    exit 1
fi

if [ -z "$LETSENCRYPT_EMAIL" ] || [ "$LETSENCRYPT_EMAIL" == "admin@yourdomain.com" ]; then
    echo -e "${RED}Error: LETSENCRYPT_EMAIL not configured in .env${NC}"
    echo "Please update LETSENCRYPT_EMAIL with your actual email"
    exit 1
fi

# Convert comma-separated domains to -d flags for certbot
DOMAIN_FLAGS=""
IFS=',' read -ra DOMAINS <<< "$PRODUCTION_DOMAINS"
for domain in "${DOMAINS[@]}"; do
    domain=$(echo "$domain" | xargs) # trim whitespace
    DOMAIN_FLAGS="$DOMAIN_FLAGS -d $domain"
done

echo -e "${GREEN}Domains to certify:${NC} $PRODUCTION_DOMAINS"
echo -e "${GREEN}Contact email:${NC} $LETSENCRYPT_EMAIL"
echo ""

# Stop nginx to free port 80/443 for certbot standalone
echo -e "${YELLOW}Stopping Docker services temporarily...${NC}"
docker compose down

# Request certificate using standalone mode
echo -e "${GREEN}Requesting SSL certificate from Let's Encrypt...${NC}"
certbot certonly \
    --standalone \
    $DOMAIN_FLAGS \
    --email "$LETSENCRYPT_EMAIL" \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

# Get first domain for certificate path
PRIMARY_DOMAIN=$(echo "$PRODUCTION_DOMAINS" | cut -d',' -f1 | xargs)

# Copy certificates to ssl/ directory
echo -e "${GREEN}Copying certificates to ssl/ directory...${NC}"
mkdir -p ssl
cp "/etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem" ssl/fullchain.pem
cp "/etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem" ssl/privkey.pem
chmod 644 ssl/fullchain.pem
chmod 600 ssl/privkey.pem

# Set up auto-renewal
echo -e "${GREEN}Setting up automatic certificate renewal...${NC}"

# Create renewal hook to copy certificates
cat > /etc/letsencrypt/renewal-hooks/post/copy-yatinveda-certs.sh << 'EOF'
#!/bin/bash
# Copy renewed certificates to YatinVeda ssl directory
YATINVEDA_DIR="$(dirname "$(find /home -name docker-compose.yml -path "*/YatinVeda/*" | head -1)" 2>/dev/null)"
if [ -n "$YATINVEDA_DIR" ]; then
    PRIMARY_DOMAIN=$(grep -E '^PRODUCTION_DOMAINS=' "$YATINVEDA_DIR/.env" | cut -d'=' -f2 | cut -d',' -f1 | xargs)
    cp "/etc/letsencrypt/live/$PRIMARY_DOMAIN/fullchain.pem" "$YATINVEDA_DIR/ssl/fullchain.pem"
    cp "/etc/letsencrypt/live/$PRIMARY_DOMAIN/privkey.pem" "$YATINVEDA_DIR/ssl/privkey.pem"
    chmod 644 "$YATINVEDA_DIR/ssl/fullchain.pem"
    chmod 600 "$YATINVEDA_DIR/ssl/privkey.pem"
    # Reload nginx in Docker
    cd "$YATINVEDA_DIR"
    docker compose exec proxy nginx -s reload 2>/dev/null || true
fi
EOF

chmod +x /etc/letsencrypt/renewal-hooks/post/copy-yatinveda-certs.sh

# Test auto-renewal (dry run)
echo -e "${YELLOW}Testing auto-renewal configuration...${NC}"
certbot renew --dry-run

# Add cron job if not exists
if ! crontab -l | grep -q 'certbot renew'; then
    (crontab -l 2>/dev/null; echo "0 0,12 * * * certbot renew --quiet --post-hook 'systemctl reload nginx' || true") | crontab -
    echo -e "${GREEN}Added daily certificate renewal check to crontab${NC}"
fi

# Restart services
echo -e "${GREEN}Restarting Docker services with new SSL certificates...${NC}"
docker compose up -d

echo ""
echo -e "${GREEN}=== SSL Setup Complete! ===${NC}"
echo ""
echo -e "${GREEN}✅ SSL certificates installed and configured${NC}"
echo -e "${GREEN}✅ Auto-renewal enabled (checks twice daily)${NC}"
echo -e "${GREEN}✅ Services restarted with production certificates${NC}"
echo ""
echo -e "Certificate details:"
echo -e "  Location: /etc/letsencrypt/live/$PRIMARY_DOMAIN/"
echo -e "  Valid for: 90 days"
echo -e "  Auto-renews: 30 days before expiration"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Verify HTTPS: https://$PRIMARY_DOMAIN/api/v1/health"
echo -e "  2. Test auto-renewal: sudo certbot renew --dry-run"
echo -e "  3. Monitor renewal logs: /var/log/letsencrypt/"
echo ""
