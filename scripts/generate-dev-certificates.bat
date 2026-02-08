@echo off
setlocal enabledelayedexpansion

echo Generating development SSL certificates for YatinVeda...
echo.

:: Create SSL directory structure
if not exist "ssl" mkdir ssl
if not exist "ssl\certs" mkdir ssl\certs
if not exist "ssl\private" mkdir ssl\private

:: Check if OpenSSL is available
where openssl >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: OpenSSL not found in PATH
    echo Please install OpenSSL or add it to your PATH
    echo Download from: https://slproweb.com/products/Win32OpenSSL.html
    pause
    exit /b 1
)

echo Generating private key...
openssl genrsa -out ssl/private/privkey.pem 2048
if %errorlevel% neq 0 (
    echo Error generating private key
    pause
    exit /b 1
)

echo Generating certificate...
openssl req -new -x509 -key ssl/private/privkey.pem -out ssl/certs/fullchain.pem -days 365 -subj "//C=IN\ST=Maharashtra\L=Mumbai\O=YatinVeda\OU=Development\CN=localhost"
if %errorlevel% neq 0 (
    echo Error generating certificate
    pause
    exit /b 1
)

echo.
echo SSL certificates generated successfully!
echo.
echo Certificate files:
echo   Private Key: ssl/private/privkey.pem
echo   Certificate: ssl/certs/fullchain.pem
echo.
echo Note: These are self-signed certificates for development only.
echo Your browser will show security warnings - this is normal for development.
echo.
echo To use HTTPS, update your docker-compose.yml to mount the SSL volume
echo and set COOKIE_SECURE=true in your environment variables.
echo.

pause