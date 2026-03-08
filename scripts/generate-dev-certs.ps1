# generate-dev-certs.ps1
# ─────────────────────────────────────────────────────────────
# Generates a self-signed SSL certificate for local development.
# Nginx expects the cert files at ./ssl/fullchain.pem and ./ssl/privkey.pem
#
# Requirements: openssl must be installed.
#   - It ships with Git for Windows (C:\Program Files\Git\usr\bin\openssl.exe)
#   - Or install via: winget install ShiningLight.OpenSSL
#
# Usage (from project root):
#   powershell -ExecutionPolicy Bypass -File scripts\generate-dev-certs.ps1
# ─────────────────────────────────────────────────────────────

$ErrorActionPreference = "Stop"

# Detect openssl
$openssl = Get-Command openssl -ErrorAction SilentlyContinue
if (-not $openssl) {
    # Try Git's bundled openssl
    $gitOpenssl = "C:\Program Files\Git\usr\bin\openssl.exe"
    if (Test-Path $gitOpenssl) {
        $openssl = $gitOpenssl
    } else {
        Write-Error "openssl not found. Install Git for Windows or OpenSSL and try again."
        exit 1
    }
} else {
    $openssl = $openssl.Path
}

# Create ssl directory if needed
$sslDir = Join-Path $PSScriptRoot "..\ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir | Out-Null
}

$certFile = Join-Path $sslDir "fullchain.pem"
$keyFile  = Join-Path $sslDir "privkey.pem"

if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
    Write-Host "SSL certificates already exist at $sslDir — skipping generation." -ForegroundColor Yellow
    Write-Host "Delete ssl\fullchain.pem and ssl\privkey.pem to regenerate." -ForegroundColor Yellow
    exit 0
}

Write-Host "Generating self-signed SSL certificate for local development..." -ForegroundColor Cyan

& $openssl req -x509 -nodes -days 365 `
    -newkey rsa:2048 `
    -keyout $keyFile `
    -out $certFile `
    -subj "/C=IN/ST=Dev/L=Local/O=YatinVeda/CN=localhost" `
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

if ($LASTEXITCODE -ne 0) {
    Write-Error "openssl failed. See output above."
    exit 1
}

Write-Host ""
Write-Host "Done! Certificates written to:" -ForegroundColor Green
Write-Host "  Certificate : $certFile" -ForegroundColor Green
Write-Host "  Private key : $keyFile" -ForegroundColor Green
Write-Host ""
Write-Host "Your browser will show a security warning — click 'Advanced > Proceed' for local dev." -ForegroundColor Yellow
Write-Host "For production, replace these with real Let's Encrypt certs." -ForegroundColor Yellow
