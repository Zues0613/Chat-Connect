import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Simple logging to see if middleware is being called
  console.log(`[MIDDLEWARE] Request to: ${pathname}`)
  
  // Get token from cookies
  const token = request.cookies.get('token')?.value
  const lastActivity = request.cookies.get('lastActivity')?.value
  
  console.log(`[MIDDLEWARE] Token: ${token ? 'EXISTS' : 'NOT FOUND'}, LastActivity: ${lastActivity}`)
  
  // Check if session is valid (similar to our client-side logic)
  const isSessionValid = () => {
    if (!token || !lastActivity) {
      return false
    }
    
    const now = Date.now()
    const lastActivityTime = parseInt(lastActivity)
    const timeSinceActivity = now - lastActivityTime
    const maxInactivity = 2 * 24 * 60 * 60 * 1000 // 2 days in milliseconds
    
    return timeSinceActivity < maxInactivity
  }
  
  const sessionValid = isSessionValid()
  console.log(`[MIDDLEWARE] Session valid: ${sessionValid}`)
  
  // Handle chat URLs - preserve them during authentication
  if (pathname.startsWith('/chat/')) {
    console.log(`[MIDDLEWARE] Processing chat URL: ${pathname}`)
    
    // If user is not authenticated, redirect to login with the chat URL preserved
    if (!sessionValid) {
      console.log(`[MIDDLEWARE] User not authenticated, redirecting to login with redirect: ${pathname}`)
      const loginUrl = new URL('/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }
    
    console.log(`[MIDDLEWARE] User authenticated, allowing access to chat`)
    // If authenticated, allow access to chat - no redirect needed
    return NextResponse.next()
  }
  
  // Handle login page with redirect parameter
  if (pathname === '/login') {
    const redirect = request.nextUrl.searchParams.get('redirect')
    console.log(`[MIDDLEWARE] Login page, redirect param: ${redirect}`)
    
    // If user is already authenticated and has a redirect, go to that URL
    if (sessionValid && redirect) {
      console.log(`[MIDDLEWARE] User authenticated, redirecting to: ${redirect}`)
      return NextResponse.redirect(new URL(redirect, request.url))
    }
    
    return NextResponse.next()
  }
  
  // Handle main page - if user is not authenticated, redirect to login
  if (pathname === '/') {
    console.log(`[MIDDLEWARE] Main page`)
    if (!sessionValid) {
      console.log(`[MIDDLEWARE] User not authenticated, redirecting to login`)
      const loginUrl = new URL('/login', request.url)
      return NextResponse.redirect(loginUrl)
    }
    
    return NextResponse.next()
  }
  
  console.log(`[MIDDLEWARE] Allowing request to: ${pathname}`)
  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
