#!/bin/bash

# YatinVeda SSL Setup Script
# This script helps set up SSL certificates for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
DOMAINS=""
EMAIL=""
CERT_PROVIDER="self-signed"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Environment (development, staging, production)"
    echo "  -d, --domains DOMAINS    Comma-separated list of domains"
    echo "  -m, --email EMAIL        Email for Let's Encrypt registration"
    echo "  -p, --provider PROVIDER  Certificate provider (self-signed, letsencrypt)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --environment development"
    echo "  $0 --environment production --domains yatinveda.com,api.yatinveda.com --email admin@yatinveda.com"
    echo "  $0 --environment staging --domains staging.yatinveda.com --email admin@yatinveda.com --provider letsencrypt"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -d|--domains)
            DOMAINS="$2"
            shift 2
            ;;
        -m|--email)
            EMAIL="$2"
            shift 2
            ;;
        -p|--provider)
            CERT_PROVIDER="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_error "Must be one of: development, staging, production"
    exit 1
fi

# Validate certificate provider
if [[ ! "$CERT_PROVIDER" =~ ^(self-signed|letsencrypt)$ ]]; then
    print_error "Invalid certificate provider: $CERT_PROVIDER"
    print_error "Must be one of: self-signed, letsencrypt"
    exit 1
fi

print_status "Setting up SSL certificates for YatinVeda"
print_status "Environment: $ENVIRONMENT"
print_status "Certificate Provider: $CERT_PROVIDER"

# Create necessary directories
print_status "Creating SSL directories..."
mkdir -p ssl/certs
mkdir -p ssl/private
mkdir -p ssl/backups
chmod 700 ssl/private

# Set up environment-specific configuration
case $ENVIRONMENT in
    development)
        print_status "Setting up development environment..."
        
        if [[ -z "$DOMAINS" ]]; then
            DOMAINS="localhost,127.0.0.1"
        fi
        
        # Create .env file for development
        cat > .env.ssl << EOF
# SSL Configuration for Development
ENVIRONMENT=development
CERT_PROVIDER=self-signed
CERT_PATH=./ssl/certs
KEY_PATH=./ssl/private
CERT_RENEWAL_DAYS=30
COOKIE_SECURE=false
COOKIE_SAMESITE=lax

# Domains
PRODUCTION_DOMAINS=$DOMAINS
STAGING_DOMAINS=$DOMAINS

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0
EOF
        
        print_success "Development SSL configuration created"
        print_warning "Self-signed certificates will be generated automatically"
        print_warning "Browsers will show security warnings for self-signed certificates"
        ;;
        
    staging)
        print_status "Setting up staging environment..."
        
        if [[ -z "$DOMAINS" ]]; then
            print_error "Domains are required for staging environment"
            print_error "Use: $0 --environment staging --domains staging.yatinveda.com --email admin@yatinveda.com"
            exit 1
        fi
        
        if [[ -z "$EMAIL" && "$CERT_PROVIDER" == "letsencrypt" ]]; then
            print_error "Email is required for Let's Encrypt certificates"
            exit 1
        fi
        
        # Create .env file for staging
        cat > .env.ssl << EOF
# SSL Configuration for Staging
ENVIRONMENT=staging
CERT_PROVIDER=$CERT_PROVIDER
CERT_PATH=./ssl/certs
KEY_PATH=./ssl/private
CERT_RENEWAL_DAYS=30
COOKIE_SECURE=true
COOKIE_SAMESITE=strict

# Domains
STAGING_DOMAINS=$DOMAINS
PRODUCTION_DOMAINS=$DOMAINS

# Let's Encrypt
LETSENCRYPT_EMAIL=$EMAIL

# Redis (recommended for staging)
REDIS_URL=redis://redis:6379/0

# Security
ENABLE_SECURITY_MONITORING=true
EOF
        
        print_success "Staging SSL configuration created"
        if [[ "$CERT_PROVIDER" == "letsencrypt" ]]; then
            print_warning "Let's Encrypt certificates will use staging server"
            print_warning "Make sure DNS points to your server before starting"
        fi
        ;;
        
    production)
        print_status "Setting up production environment..."
        
        if [[ -z "$DOMAINS" ]]; then
            print_error "Domains are required for production environment"
            print_error "Use: $0 --environment production --domains yatinveda.com,api.yatinveda.com --email admin@yatinveda.com"
            exit 1
        fi
        
        if [[ -z "$EMAIL" ]]; then
            print_error "Email is required for production environment"
            exit 1
        fi
        
        # Force Let's Encrypt for production
        CERT_PROVIDER="letsencrypt"
        
        # Create .env file for production
        cat > .env.ssl << EOF
# SSL Configuration for Production
ENVIRONMENT=production
CERT_PROVIDER=letsencrypt
CERT_PATH=./ssl/certs
KEY_PATH=./ssl/private
CERT_RENEWAL_DAYS=30
COOKIE_SECURE=true
COOKIE_SAMESITE=strict

# Domains
PRODUCTION_DOMAINS=$DOMAINS

# Let's Encrypt
LETSENCRYPT_EMAIL=$EMAIL

# Redis (required for production)
REDIS_URL=redis://redis:6379/0

# Security (required for production)
ENABLE_SECURITY_MONITORING=true
SECRET_KEY=\${SECRET_KEY:-$(openssl rand -base64 32)}

# Database (use PostgreSQL in production)
# DATABASE_URL=postgresql://user:password@localhost:5432/yatinveda
EOF
        
        print_success "Production SSL configuration created"
        print_warning "IMPORTANT: Update the following before deployment:"
        print_warning "1. Set a strong SECRET_KEY"
        print_warning "2. Configure PostgreSQL DATABASE_URL"
        print_warning "3. Set up external logging and monitoring"
        print_warning "4. Ensure DNS points to your server"
        ;;
esac

# Create Docker Compose override for SSL
print_status "Creating Docker Compose configuration..."

cat > docker-compose.override.yml << EOF
version: "3.9"

services:
  backend:
    environment:
      - ENVIRONMENT=$ENVIRONMENT
      - CERT_PROVIDER=$CERT_PROVIDER
      - CERT_PATH=/etc/ssl/certs
      - KEY_PATH=/etc/ssl/private
EOF

if [[ "$ENVIRONMENT" != "development" ]]; then
    cat >> docker-compose.override.yml << EOF
      - COOKIE_SECURE=true
      - COOKIE_SAMESITE=strict
EOF
fi

if [[ -n "$DOMAINS" ]]; then
    if [[ "$ENVIRONMENT" == "production" ]]; then
        cat >> docker-compose.override.yml << EOF
      - PRODUCTION_DOMAINS=$DOMAINS
EOF
    else
        cat >> docker-compose.override.yml << EOF
      - STAGING_DOMAINS=$DOMAINS
EOF
    fi
fi

if [[ -n "$EMAIL" ]]; then
    cat >> docker-compose.override.yml << EOF
      - LETSENCRYPT_EMAIL=$EMAIL
EOF
fi

cat >> docker-compose.override.yml << EOF
    volumes:
      - ./ssl/certs:/etc/ssl/certs
      - ./ssl/private:/etc/ssl/private

  proxy:
    volumes:
      - ./ssl/certs:/etc/ssl/certs:ro
      - ./ssl/private:/etc/ssl/private:ro
EOF

# Set appropriate permissions
chmod 600 .env.ssl 2>/dev/null || true
chmod 644 docker-compose.override.yml

print_success "SSL setup completed!"
print_status "Next steps:"

case $ENVIRONMENT in
    development)
        echo "1. Start the application: docker-compose up -d"
        echo "2. Access via HTTP: http://localhost:8080"
        echo "3. Self-signed certificates will be generated automatically"
        ;;
    staging|production)
        echo "1. Review and update .env.ssl with your specific configuration"
        echo "2. Ensure DNS records point to your server"
        echo "3. Start with SSL: docker-compose -f docker-compose.yml -f docker-compose-ssl.yml up -d"
        echo "4. Monitor certificate provisioning in logs"
        ;;
esac

print_status "Configuration files created:"
print_status "- .env.ssl (environment variables)"
print_status "- docker-compose.override.yml (Docker configuration)"
print_status "- ssl/ directory (certificate storage)"

if [[ "$ENVIRONMENT" == "production" ]]; then
    print_warning ""
    print_warning "PRODUCTION SECURITY CHECKLIST:"
    print_warning "□ Set strong SECRET_KEY in .env.ssl"
    print_warning "□ Configure PostgreSQL database"
    print_warning "□ Set up external logging (ELK, Splunk, etc.)"
    print_warning "□ Configure monitoring and alerting"
    print_warning "□ Review and test backup procedures"
    print_warning "□ Verify firewall and network security"
    print_warning "□ Test certificate renewal process"
fi