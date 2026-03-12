#!/usr/bin/env bash
# synthetic_probe.sh — Lightweight synthetic monitoring for YatinVeda
# Run via cron every 2 minutes. Logs failures to stderr; exits non-zero if any check fails.
#
# Usage:
#   API_BASE=https://api.yatinveda.com FRONTEND_URL=https://yatinveda.com ./synthetic_probe.sh
#   # Or with defaults (localhost):
#   ./synthetic_probe.sh

set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
TIMEOUT=10
FAILURES=0

check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_keyword="$3"

    local http_code
    local body
    body=$(curl -sf --max-time "$TIMEOUT" -w "\n%{http_code}" "$url" 2>/dev/null) || {
        echo "[FAIL] $name — $url unreachable" >&2
        FAILURES=$((FAILURES + 1))
        return
    }

    http_code=$(echo "$body" | tail -n1)
    body=$(echo "$body" | sed '$d')

    if [ "$http_code" -ne 200 ]; then
        echo "[FAIL] $name — HTTP $http_code (expected 200)" >&2
        FAILURES=$((FAILURES + 1))
        return
    fi

    if [ -n "$expected_keyword" ] && ! echo "$body" | grep -qi "$expected_keyword"; then
        echo "[FAIL] $name — response missing keyword: $expected_keyword" >&2
        FAILURES=$((FAILURES + 1))
        return
    fi

    echo "[OK]   $name — HTTP $http_code"
}

echo "=== YatinVeda Synthetic Probe — $(date -u '+%Y-%m-%dT%H:%M:%SZ') ==="

check_endpoint "API Root"     "$API_BASE/"                   "active"
check_endpoint "Health"       "$API_BASE/api/v1/health"      "healthy"
check_endpoint "Readiness"    "$API_BASE/api/v1/readiness"   "true"
check_endpoint "Frontend"     "$FRONTEND_URL/"               "YatinVeda"

if [ "$FAILURES" -gt 0 ]; then
    echo "--- $FAILURES check(s) failed ---" >&2
    exit 1
fi

echo "--- All checks passed ---"
