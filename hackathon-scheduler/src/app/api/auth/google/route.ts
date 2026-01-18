// src/app/api/auth/google/route.ts
import { NextResponse } from 'next/server';
import { google } from 'googleapis';

export async function GET() {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = process.env.GOOGLE_REDIRECT_URI;

  // 1. Log what we are using to be 100% sure
  console.log('--- START AUTH ---');
  console.log('Client ID:', clientId ? 'Loaded' : 'Missing');
  console.log('Redirect URI:', redirectUri); 

  if (!clientId || !clientSecret || !redirectUri) {
    return NextResponse.json({ error: 'Config missing' }, { status: 500 });
  }

  const oauth2Client = new google.auth.OAuth2(
    clientId,
    clientSecret,
    redirectUri
  );

  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: [
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/userinfo.email',
      'https://www.googleapis.com/auth/userinfo.profile'
    ],
    // 2. FORCE the redirect_uri here explicitly
    redirect_uri: redirectUri 
  });

  return NextResponse.redirect(authUrl);
}
