// src/app/api/auth/status/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const session = request.cookies.get('session')?.value;
  
  if (session) {
    try {
      const sessionData = JSON.parse(session);
      return NextResponse.json({
        authenticated: true,
        email: sessionData.email,
        calendarId: sessionData.calendarId
      });
    } catch (error) {
      return NextResponse.json({ authenticated: false });
    }
  }

  return NextResponse.json({ authenticated: false });
}
