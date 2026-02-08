import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

/**
 * Enhanced middleware for YatinVeda frontend.
 * 
 * Features:
 * - Request correlation IDs for distributed tracing
 * - Comprehensive security headers
 * - Performance monitoring headers
 * - Smart caching strategies
 * - CORS handling for API routes
 */

// Track request metrics (in-memory, reset on restart)
const requestMetrics = {
  total: 0,
  byPath: new Map<string, number>(),
  byStatus: new Map<number, number>(),
}

export function middleware(request: NextRequest) {
  const startTime = Date.now()
  const response = NextResponse.next()

  // Generate unique correlation ID for distributed tracing
  const correlationId = crypto.randomUUID()
  response.headers.set('X-Correlation-ID', correlationId)
  response.headers.set('X-Request-ID', correlationId)
  
  // Track request metrics
  requestMetrics.total++
  const path = request.nextUrl.pathname
  requestMetrics.byPath.set(path, (requestMetrics.byPath.get(path) || 0) + 1)
  
  // ============================================================================
  // Security Headers
  // ============================================================================
  
  // Prevent MIME type sniffing
  response.headers.set('X-Content-Type-Options', 'nosniff')
  
  // Prevent clickjacking attacks
  response.headers.set('X-Frame-Options', 'SAMEORIGIN')
  
  // Enable XSS protection (legacy browsers)
  response.headers.set('X-XSS-Protection', '1; mode=block')
  
  // Control referrer information
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  
  // Permissions policy (restrict powerful features)
  response.headers.set(
    'Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), interest-cohort=()'
  )
  
  // Content Security Policy (CSP)
  if (!path.startsWith('/api/')) {
    response.headers.set(
      'Content-Security-Policy',
      "default-src 'self'; " +
      "script-src 'self' 'unsafe-eval' 'unsafe-inline'; " +
      "style-src 'self' 'unsafe-inline'; " +
      "img-src 'self' data: blob: https:; " +
      "font-src 'self' data:; " +
      "connect-src 'self' http://localhost:8000 https://*; " +
      "frame-ancestors 'self';"
    )
  }
  
  // Strict Transport Security (HTTPS only - enable in production)
  // response.headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
  
  // ============================================================================
  // Performance Headers
  // ============================================================================
  
  // DNS prefetch control
  response.headers.set('X-DNS-Prefetch-Control', 'on')
  
  // Add request timing information
  const processingTime = Date.now() - startTime
  response.headers.set('X-Response-Time', `${processingTime}ms`)
  
  // Server timing for performance monitoring
  response.headers.set('Server-Timing', `total;dur=${processingTime}`)
  
  // ============================================================================
  // Caching Strategy
  // ============================================================================
  
  // API routes - no caching for fresh data
  if (path.startsWith('/api/')) {
    response.headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate')
    response.headers.set('Pragma', 'no-cache')
    response.headers.set('Expires', '0')
  }
  // Static assets - aggressive caching with immutability
  else if (path.match(/\.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|eot|svg|webp)$/)) {
    response.headers.set('Cache-Control', 'public, immutable, max-age=31536000')
  }
  // Next.js static files - long-term caching
  else if (path.startsWith('/_next/static')) {
    response.headers.set('Cache-Control', 'public, immutable, max-age=31536000')
  }
  // Next.js data - short caching with revalidation
  else if (path.startsWith('/_next/data')) {
    response.headers.set('Cache-Control', 'private, max-age=60, stale-while-revalidate=300')
  }
  // HTML pages - cache with stale-while-revalidate for better UX
  else if (!path.includes('.')) {
    // Authenticated pages - no caching
    const authPages = ['/dashboard', '/profile', '/wallet', '/prescriptions', '/community-feed']
    if (authPages.some(authPath => path.startsWith(authPath))) {
      response.headers.set('Cache-Control', 'private, no-cache, no-store, must-revalidate')
    }
    // Public pages - cache with revalidation
    else {
      response.headers.set('Cache-Control', 'public, max-age=3600, stale-while-revalidate=86400')
    }
  }
  // Default - short-term caching
  else {
    response.headers.set('Cache-Control', 'public, max-age=300, stale-while-revalidate=600')
  }
  
  // ============================================================================
  // CORS Headers (for API proxy scenarios)
  // ============================================================================
  
  if (request.method === 'OPTIONS') {
    return new NextResponse(null, {
      status: 200,
      headers: {
        'Access-Control-Allow-Origin': request.headers.get('origin') || '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-CSRF-Token',
        'Access-Control-Max-Age': '86400',
      },
    })
  }

  return response
}

// ============================================================================
// Middleware Configuration
// ============================================================================

// Matcher for routes that should be processed by middleware
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     * - manifest.json, robots.txt (static files)
     */
    '/((?!_next/static|_next/image|favicon.ico|public/|manifest.json|robots.txt).*)',
  ],
}

// Metrics endpoint (for monitoring - implement in API route)
export function getMetrics() {
  return {
    total_requests: requestMetrics.total,
    requests_by_path: Object.fromEntries(requestMetrics.byPath),
    requests_by_status: Object.fromEntries(requestMetrics.byStatus),
  }
}


