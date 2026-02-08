#!/bin/bash

# Generate development SSL certificates for YatinVeda
# This creates self-signed certificates for local development with HTTPS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}▶${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Create SSL directory
SSL_DIR="./ssl"
mkdir -p "$SSL_DIR"/certs "$SSL_DIR"/private

print_status "Generating development SSL certificates..."

# Generate private key
openssl genrsa -out "$SSL_DIR/private/privkey.pem" 2048

# Generate certificate signing request
openssl req -new -key "$SSL_DIR/private/privkey.pem" -out "$SSL_DIR/cert.csr" -subj "/C=IN/ST=Maharashtra/L=Mumbai/O=YatinVeda/OU=Development/CN=localhost"

# Generate self-signed certificate
openssl x509 -req -days 365 -in "$SSL_DIR/cert.csr" -signkey "$SSL_DIR/private/privkey.pem" -out "$SSL_DIR/certs/fullchain.pem"

# Clean up CSR file
rm "$SSL_DIR/cert.csr"

# Set proper permissions
chmod 600 "$SSL_DIR/private/privkey.pem"
chmod 644 "$SSL_DIR/certs/fullchain.pem"

print_status "SSL certificates generated successfully!"
print_warning "These are self-signed certificates for development only."
print_warning "For production, use Let's Encrypt or purchase valid certificates."

# Create .env file for HTTPS configuration
cat > .env.https << EOF
# HTTPS Configuration for Development
ENVIRONMENT=development
COOKIE_SECURE=true
COOKIE_SAMESITE=strict
NEXT_PUBLIC_API_BASE_URL=https://localhost:8000
EOF

print_status "Created .env.https configuration file"
print_status "To use HTTPS, run: docker-compose --env-file .env.https up"

echo ""
print_status "Certificate Details:"
echo "  Private Key: $SSL_DIR/private/privkey.pem"
echo "  Certificate: $SSL_DIR/certs/fullchain.pem"
echo "  Valid for: localhost, 365 days"
echo ""
print_warning "Your browser will show a security warning for self-signed certificates."
print_warning "You can safely proceed or add the certificate to your trusted store."