import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const publicPaths = ['/login'];

export function middleware(request: NextRequest) {
  const isPublic = publicPaths.some((path) => request.nextUrl.pathname.startsWith(path));
  const token = request.cookies.get('sapisehat_agency_token')?.value;

  if (!isPublic && !token && request.nextUrl.pathname.startsWith('/agency')) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    url.searchParams.set('next', request.nextUrl.pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/agency/:path*']
};
