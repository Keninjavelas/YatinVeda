# generate-dev-certs.ps1
# Generates self-signed certs for local/dev nginx TLS.

$ErrorActionPreference = "Stop"

$opensslCmd = Get-Command openssl -ErrorAction SilentlyContinue
if ($null -eq $opensslCmd) {
    $gitOpenssl = "C:\Program Files\Git\usr\bin\openssl.exe"
    if (Test-Path $gitOpenssl) {
        $opensslPath = $gitOpenssl
    }
    else {
        throw "openssl not found. Install Git for Windows or OpenSSL."
    }
}
else {
    $opensslPath = $opensslCmd.Path
}

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$sslDir = Join-Path $projectRoot "ssl"
if (-not (Test-Path $sslDir)) {
    New-Item -ItemType Directory -Path $sslDir | Out-Null
}

$certFile = Join-Path $sslDir "fullchain.pem"
$keyFile = Join-Path $sslDir "privkey.pem"

if ((Test-Path $certFile) -and (Test-Path $keyFile)) {
    Write-Host "SSL certificates already exist at $sslDir; skipping generation." -ForegroundColor Yellow
    exit 0
}

Write-Host "Generating self-signed SSL certificate for local development..." -ForegroundColor Cyan

& $opensslPath req -x509 -nodes -days 365 -newkey rsa:2048 `
    -keyout $keyFile `
    -out $certFile `
    -subj "/C=IN/ST=Dev/L=Local/O=YatinVeda/CN=localhost" `
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

if ($LASTEXITCODE -ne 0) {
    throw "openssl command failed"
}

Write-Host "Certificates created:" -ForegroundColor Green
Write-Host "  $certFile" -ForegroundColor Green
Write-Host "  $keyFile" -ForegroundColor Green
