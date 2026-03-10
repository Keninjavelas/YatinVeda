# International Deployment Guide

**For deploying YatinVeda to serve users globally**

Last Updated: March 10, 2026

---

## Overview

This guide covers deploying YatinVeda for international markets with support for:
- Multiple currencies and payment gateways
- Multi-language interfaces (i18n)
- GDPR and international data compliance
- Multi-region deployment
- CDN configuration
- Timezone handling

## Prerequisites

Before international deployment, ensure you have:
- [ ] Completed basic deployment (see [DEPLOYMENT.md](../DEPLOYMENT.md))
- [ ] Legal documents reviewed by attorneys in target jurisdictions
- [ ] Payment gateway accounts for target regions
- [ ] CDN account (Cloudflare, CloudFront, etc.)
- [ ] Currency exchange API account (optional but recommended)
- [ ] Multi-region cloud infrastructure access

---

## Phase 1: Database & Backend Configuration

### 1.1 Run Internationalization Migration

```bash
# Activate virtual environment
cd backend
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Run the migration
alembic upgrade head
```

This migration adds:
- Timezone, currency, country, and language fields to users
- Multi-currency support to payments
- Exchange rate tracking table
- Legal consent tracking
- Cookie preferences
- GDPR data export requests

### 1.2 Configure Environment Variables

Add to your `.env`:

```bash
# Currency Settings
DEFAULT_CURRENCY=USD
CURRENCY_PROVIDER=openexchangerates  # or currencyapi, manual
CURRENCY_API_KEY=your_api_key_here
SUPPORTED_CURRENCIES=USD,EUR,GBP,INR,AUD,CAD,SGD,AED,JPY,CNY

# Timezone
DEFAULT_TIMEZONE=UTC

# Languages
SUPPORTED_LANGUAGES=en,es,fr,de,hi,zh,ja,pt,ar

# CDN
CDN_DOMAINS=cdn.yourdomain.com
CDN_BASE_URL=https://cdn.yourdomain.com

# GDPR Compliance
DATA_EXPORT_RETENTION_DAYS=30
ANONYMIZE_ON_DELETION=true
```

### 1.3 Update Payment Gateway Configuration

#### For Stripe (International)

```bash
# Add to .env
STRIPE_API_KEY=sk_live_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_ENABLED=true

# Support for regional payment methods
STRIPE_PAYMENT_METHODS=card,alipay,wechat_pay,ideal,sepa_debit
```

#### Keep Razorpay for India

```bash
# Existing configuration
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
RAZORPAY_ENABLED=true
```

---

## Phase 2: Frontend Internationalization

### 2.1 Install i18n Dependencies

```bash
cd frontend
npm install next-intl
```

### 2.2 Create Translation Files

Create `frontend/messages/` directory structure:

```
frontend/messages/
├── en.json        # English
├── es.json        # Spanish
├── fr.json        # French
├── de.json        # German
├── hi.json        # Hindi
├── zh.json        # Chinese
├── ja.json        # Japanese
├── pt.json        # Portuguese
└── ar.json        # Arabic
```

Example `en.json`:
```json
{
  "common": {
    "welcome": "Welcome to YatinVeda",
    "login": "Login",
    "signup": "Sign Up",
    "logout": "Logout"
  },
  "auth": {
    "emailLabel": "Email Address",
    "passwordLabel": "Password",
    "forgotPassword": "Forgot Password?",
    "createAccount": "Create Account"
  },
  "currency": {
    "usd": "US Dollar",
    "eur": "Euro",
    "gbp": "British Pound",
    "inr": "Indian Rupee"
  }
}
```

### 2.3 Configure next.config.mjs

Update your Next.js config:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  i18n: {
    locales: ['en', 'es', 'fr', 'de', 'hi', 'zh', 'ja', 'pt', 'ar'],
    defaultLocale: 'en',
    localeDetection: true
  },
  // For CDN
  assetPrefix: process.env.CDN_BASE_URL || '',
  images: {
    domains: ['cdn.yourdomain.com'],
  }
};

export default nextConfig;
```

---

## Phase 3: CDN Configuration

### 3.1 Cloudflare Setup (Recommended)

1. **Add your domain to Cloudflare**
   - Point DNS to your origin server
   - Enable proxy (orange cloud)

2. **Configure caching rules:**
   ```
   Static Assets: Cache everything
   API endpoints: Bypass cache
   ```

3. **Enable performance features:**
   - Brotli compression
   - HTTP/3
   - 0-RTT Connection Resumption
   - Image optimization (Polish)

4. **Security settings:**
   - SSL/TLS mode: Full (strict)
   - Always Use HTTPS: On
   - Automatic HTTPS Rewrites: On
   - WAF rules for your region

### 3.2 AWS CloudFront Setup (Alternative)

Create CloudFront distribution:

```bash
# Example CLI command
aws cloudfront create-distribution \
  --origin-domain-name yourdomain.com \
  --default-root-object index.html \
  --enabled true
```

Configure behaviors:
- `/*`: Forward all headers/cookies
- `/static/*`: Cache with long TTL
- `/api/*`: No caching

---

## Phase 4: Multi-Region Deployment

### 4.1 Database Replication

For PostgreSQL, set up read replicas in target regions:

```bash
# Example for AWS RDS
aws rds create-db-instance-read-replica \
  --db-instance-identifier yatinveda-replica-eu \
  --source-db-instance-identifier yatinveda-primary-us \
  --availability-zone eu-west-1a
```

Configure connection routing based on user region.

### 4.2 Container Deployment

Update `docker-compose.yml` for multi-region:

```yaml
services:
  backend:
    environment:
      - REGION=${DEPLOY_REGION:-us-east-1}
      - DATABASE_URL=${DATABASE_URL_PRIMARY}
      - READ_REPLICA_URL=${DATABASE_URL_REPLICA}
```

### 4.3 Kubernetes Multi-Region

If using Kubernetes, deploy to multiple regions:

```bash
# Deploy to US
kubectl apply -f k8s/us-east-1/ --context=us-cluster

# Deploy to EU
kubectl apply -f k8s/eu-west-1/ --context=eu-cluster

# Deploy to Asia
kubectl apply -f k8s/ap-southeast-1/ --context=asia-cluster
```

Configure global load balancer (AWS Global Accelerator, GCP Global LB, etc.)

---

## Phase 5: Legal Compliance

### 5.1 GDPR Compliance (EU)

**Required implementations:**
- ✅ Cookie consent banner (implemented in backend)
- ✅ Data export endpoint (Article 15)
- ✅ Data deletion endpoint (Article 17)
- ✅ Privacy policy (created)
- ✅ Terms of service (created)
- [ ] Data Processing Agreement (DPA) - create with legal counsel
- [ ] Privacy Impact Assessment (PIA) - conduct before EU launch

**EU Representative:**
If you're processing EU data, appoint an EU representative:
- Required if not established in EU
- Contact details in Privacy Policy

### 5.2 CCPA Compliance (California)

**Required:**
- "Do Not Sell My Personal Information" link (we don't sell data)
- Data deletion upon request (implemented)
- Data disclosure upon request (implemented)

### 5.3 Regional Data Residency

Some countries require data to stay within borders:

**EU (GDPR):**
- Use EU region for database
- EU-based backups only
- Standard Contractual Clauses for any transfers

**Russia:**
- Personal data must be stored in Russia
- Requires Russian server presence

**China:**
- Requires ICP license
- Data must stay in mainland China
- Significant regulatory compliance

---

## Phase 6: Payment Gateway Integration

### 6.1 Regional Gateway Selection

| Region | Primary Gateway | Backup |
|--------|----------------|---------|
| North America | Stripe | PayPal |
| Europe | Stripe | Adyen |
| India | Razorpay | Stripe |
| Southeast Asia | Stripe | 2C2P |
| China | Alipay, WeChat Pay | - |
| Middle East | Stripe | PayTabs |
| Latin America | MercadoPago | Stripe |

### 6.2 Configure Payment Routing

Update backend to route based on user country:

```python
async def get_payment_gateway(user_country: str):
    """Route to appropriate payment gateway."""
    if user_country == 'IN':
        return 'razorpay'
    elif user_country == 'CN':
        return 'alipay'
    elif user_country in ['US', 'CA', 'GB', 'AU', 'EU']:
        return 'stripe'
    else:
        return 'stripe'  # default
```

### 6.3 Currency Display

Prices should be shown in user's preferred currency:

```python
from services.currency_service import CurrencyService

# Convert base price to user currency
currency_service = CurrencyService(db)
local_price = await currency_service.convert_amount(
    amount=base_price_in_cents,
    from_currency='USD',
    to_currency=user.preferred_currency
)
```

---

## Phase 7: Monitoring & Observability

### 7.1 Geographic Monitoring

Set up monitoring from multiple regions:

**Uptime Monitoring:**
- UptimeRobot (from multiple regions)
- Pingdom
- StatusCake

**Performance Monitoring:**
- New Relic with regional agents
- Datadog with multi-region
- Prometheus + Grafana (already configured)

### 7.2 Regional Dashboards

Create Grafana dashboards for:
- Request latency by region
- Error rates by country
- Currency conversion success rates
- Payment gateway performance by region
- GDPR request handling times

---

## Phase 8: Testing

### 8.1 Pre-Launch Checklist

**Technical:**
- [ ] Test from multiple geographic locations (VPN)
- [ ] Verify timezone handling (bookings, etc.)
- [ ] Test currency conversion accuracy
- [ ] Verify payment gateways in each region
- [ ] Load test with international traffic
- [ ] Test i18n translations completeness
- [ ] Verify CDN cache hit rates
- [ ] Test GDPR data export/deletion

**Legal:**
- [ ] Legal review in each target market
- [ ] Privacy policy translated
- [ ] Terms of service translated
- [ ] Cookie consent in local language
- [ ] Refund policies comply with local law

**Business:**
- [ ] Customer support in target languages
- [ ] Local payment methods enabled
- [ ] Pricing strategy per region
- [ ] Marketing materials localized

### 8.2 Staged Rollout

Don't launch everywhere at once:

**Week 1:** English-speaking markets
- US, UK, Canada, Australia

**Week 3:** Western Europe
- France, Germany, Spain

**Week 6:** Asia Pacific
- India, Singapore, Japan

**Week 9:** Other markets
- Latin America, Middle East

Monitor each phase before proceeding.

---

## Phase 9: Go-Live

### 9.1 DNS Configuration

Point your domain to CDN/load balancer:

```
# Example Cloudflare DNS
A    yatinveda.com        104.21.XXX.XXX
A    www.yatinveda.com    104.21.XXX.XXX
AAAA yatinveda.com        2606:4700::XXX
```

### 9.2 SSL Certificates

Ensure SSL is configured for all regions:

```bash
# Let's Encrypt for multi-domain
certbot certonly --dns-cloudflare \
  -d yatinveda.com \
  -d *.yatinveda.com \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini
```

### 9.3 Enable International Features

Update `.env` for production:

```bash
ENVIRONMENT=production
ENABLE_I18N=true
ENABLE_MULTI_CURRENCY=true
ENABLE_GDPR_FEATURES=true
```

### 9.4 Launch Monitoring

Monitor intensely for first 48 hours:
- Error rates by region
- Payment success rates
- API latency
- Database connection pool usage
- CDN cache performance

---

## Maintenance & Operations

### Regular Tasks

**Daily:**
- Monitor error rates by region
- Check payment gateway webhooks
- Review GDPR request queue

**Weekly:**
- Update exchange rates (if manual)
- Review i18n translation requests
- Analyze regional performance metrics

**Monthly:**
- Review and update legal documents
- Security audits
- Compliance reporting
- Regional pricing adjustments

---

## Troubleshooting

### Issue: Slow API response from Asia

**Solution:**
- Deploy regional backend instances
- Use read replicas closer to users
- Enable CDN caching for static endpoints

### Issue: Payment failures in specific country

**Solution:**
- Check gateway regional availability
- Verify currency support
- Review local payment regulations
- Add alternative payment method

### Issue: GDPR deletion errors

**Solution:**
- Check foreign key constraints
- Review anonymization logic
- Ensure backup data is also deleted

---

## Cost Optimization

### Regional Pricing Strategy

Consider purchasing power parity:

```python
regional_multipliers = {
    'US': 1.0,      # Base price
    'GB': 1.1,      # 10% more
    'EU': 1.05,     # 5% more
    'IN': 0.3,      # 70% less (PPP adjusted)
    'BR': 0.5,      # 50% less
}
```

### Infrastructure Costs

**Monthly estimates for 10,000 global users:**
- Multi-region database: $500-800
- CDN (Cloudflare Pro): $20
- Container hosting: $300-500
- Currency API: $29-99
- Monitoring: $50-150
- **Total: ~$900-1,600/month**

---

## Support & Resources

### External Services

**Currency APIs:**
- [OpenExchangeRates](https://openexchangerates.org/) - $29/mo
- [CurrencyAPI](https://currencyapi.com/) - $15/mo

**Translation Services:**
- [Lokalise](https://lokalise.com/)
- [Phrase](https://phrase.com/)
- [POEditor](https://poeditor.com/)

**Compliance Tools:**
- [OneTrust](https://www.onetrust.com/) - Cookie compliance
- [TrustArc](https://trustarc.com/) - Privacy management
- [Cookiebot](https://www.cookiebot.com/) - Cookie consent

### Legal Resources

- **GDPR:** https://gdpr.eu/
- **CCPA:** https://oag.ca.gov/privacy/ccpa
- **ICO (UK):** https://ico.org.uk/
- **CNIL (France):** https://www.cnil.fr/

---

## Conclusion

International deployment is complex but manageable with proper:
1. Technical infrastructure (CDN, multi-region)
2. Legal compliance (GDPR, CCPA, etc.)
3. Payment integration (multiple gateways)
4. Localization (i18n, currencies, timezones)
5. Monitoring (regional performance tracking)

Launch incrementally, monitor closely, and iterate based on regional feedback.

**Need help?** Create an issue on GitHub or contact support@yatinveda.com

---

**Last Updated:** March 10, 2026  
**Version:** 1.0.0
