# HTTPS & TLS Configuration Guide

## Overview

This guide explains how to configure HTTPS/TLS for the YatinVeda platform, including SSL certificate management, nginx configuration, and security best practices.

## Prerequisites

- Docker and Docker Compose installed
- OpenSSL for certificate generation (development)
- Domain name and DNS configuration (production)

## Development Setup (Self-Signed Certificates)

### 1. Generate Development Certificates

**On Linux/Mac:**
```bash
chmod +x scripts/generate-dev-certificates.sh
./scripts/generate-dev-certificates.sh
```

**On Windows:**
```cmd
scripts\generate-dev-certificates.bat
```

This creates:
- `ssl/private/privkey.pem` - Private key
- `ssl/certs/fullchain.pem` - Self-signed certificate

### 2. Configure Environment

Create `.env.https` file:
```env
ENVIRONMENT=development
COOKIE_SECURE=true
COOKIE_SAMESITE=strict
NEXT_PUBLIC_API_BASE_URL=https://localhost:8000
```

### 3. Start Services with HTTPS

```bash
docker-compose --env-file .env.https up --build
```

Access the application at: https://localhost

## Production Setup (Let's Encrypt)

### 1. Prerequisites

- Domain name pointing to your server
- Port 80 and 443 accessible from internet
- Docker Compose setup

### 2. Using Let's Encrypt with Certbot

Install Certbot:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot

# CentOS/RHEL
sudo yum install certbot
```

Generate certificates:
```bash
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
```

Certificates will be stored in:
- `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- `/etc/letsencrypt/live/yourdomain.com/privkey.pem`

### 3. Configure Docker for Production

Update `docker-compose.yml` to mount production certificates:

```yaml
proxy:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt/live/yourdomain.com/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
    - /etc/letsencrypt/live/yourdomain.com/privkey.pem:/etc/nginx/ssl/privkey.pem:ro
```

### 4. Automated Certificate Renewal

Create renewal script `/opt/scripts/renew-certs.sh`:
```bash
#!/bin/bash
docker-compose stop proxy
certbot renew --standalone
docker-compose start proxy
```

Add to crontab for automatic renewal:
```bash
# Twice daily certificate renewal check
0 2,14 * * * /opt/scripts/renew-certs.sh >> /var/log/cert-renewal.log 2>&1
```

## Configuration Details

### Nginx SSL Configuration

The `nginx/nginx.conf` includes:

**SSL Protocol Settings:**
- TLS 1.2 and 1.3 support
- Strong cipher suites
- Session resumption disabled for security

**Security Headers:**
- HSTS (HTTP Strict Transport Security)
- Content Security Policy
- X-Frame-Options
- X-Content-Type-Options

**OCSP Stapling:**
- Improves performance and privacy
- Reduces certificate validation overhead

### Backend Cookie Security

Environment variables for cookie security:
```env
COOKIE_SECURE=true          # Required for HTTPS
COOKIE_SAMESITE=strict      # Prevent CSRF attacks
ENVIRONMENT=production      # Enables strict security policies
```

### Certificate Management

**Development:**
- Self-signed certificates
- Valid for localhost only
- 365-day validity period

**Production:**
- Let's Encrypt certificates
- 90-day validity period
- Automatic renewal process

## Security Best Practices

### 1. Certificate Security
- Store private keys with restricted permissions (600)
- Never commit certificates to version control
- Use separate certificates for different environments

### 2. HSTS Configuration
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 3. Perfect Forward Secrecy
Ensure cipher suites support PFS:
```
ECDHE-RSA-AES256-GCM-SHA512
ECDHE-RSA-AES256-GCM-SHA384
```

### 4. OCSP Stapling
Improves performance and privacy by serving OCSP responses directly from the server.

## Troubleshooting

### Common Issues

**1. Certificate Not Trusted**
- Development: Add self-signed certificate to browser trust store
- Production: Verify Let's Encrypt certificate installation

**2. Mixed Content Warnings**
- Ensure all resources use HTTPS
- Update API URLs in frontend configuration
- Check Content Security Policy settings

**3. HSTS Issues**
- Clear browser HSTS cache during development
- Chrome: chrome://net-internals/#hsts
- Firefox: about:config → network.stricttransportsecurity.preloadlist

**4. Certificate Renewal Failures**
- Check firewall allows port 80 for ACME challenge
- Verify DNS records point to correct server
- Review Certbot logs: `/var/log/letsencrypt/`

### Testing HTTPS Configuration

Use online SSL testing tools:
- SSL Labs: https://www.ssllabs.com/ssltest/
- Mozilla Observatory: https://observatory.mozilla.org/

## Monitoring

### Certificate Expiry Monitoring

Create monitoring script:
```bash
#!/bin/bash
# Check certificate expiry
openssl x509 -enddate -noout -in /etc/nginx/ssl/fullchain.pem
```

### Log Analysis

Monitor nginx access logs for:
- SSL handshake failures
- Protocol negotiation issues
- Cipher suite compatibility

## Migration Checklist

### From HTTP to HTTPS

- [ ] Generate SSL certificates
- [ ] Update nginx configuration
- [ ] Configure HSTS headers
- [ ] Update backend cookie settings
- [ ] Update frontend API URLs
- [ ] Test all application features
- [ ] Set up certificate renewal process
- [ ] Update documentation
- [ ] Monitor for mixed content issues

### Production Deployment

- [ ] Obtain valid SSL certificates
- [ ] Configure automated renewal
- [ ] Test certificate installation
- [ ] Verify HSTS preload eligibility
- [ ] Update security headers
- [ ] Perform load testing
- [ ] Set up monitoring alerts

## Additional Resources

- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [OWASP Transport Layer Protection](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)
- [Nginx SSL/TLS Guide](https://nginx.org/en/docs/http/configuring_https_servers.html)

---
**Last Updated:** January 2026  
**Version:** 1.0