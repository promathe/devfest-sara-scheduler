import { NextRequest, NextResponse } from 'next/server';
import { google } from 'googleapis';

export async function GET(request: NextRequest) {
  console.log('--- Callback Route Started ---'); // LOG 1

  const searchParams = request.nextUrl.searchParams;
  const code = searchParams.get('code');

  if (!code) {
    return NextResponse.json({ error: 'No code provided' }, { status: 400 });
  }

  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = process.env.GOOGLE_REDIRECT_URI;

  const oauth2Client = new google.auth.OAuth2(
    clientId,
    clientSecret,
    redirectUri
  );

  try {
    console.log('--- Exchanging Code for Tokens ---'); // LOG 2
    // This is the line that usually times out if network is bad
    const { tokens } = await oauth2Client.getToken(code);
    console.log('--- Tokens Received ---'); // LOG 3
    
    oauth2Client.setCredentials(tokens);

    console.log('--- Fetching User Info ---'); // LOG 4
    const oauth2 = google.oauth2({ version: 'v2', auth: oauth2Client });
    const userInfo = await oauth2.userinfo.get();
    console.log('--- User Info Received ---'); // LOG 5

    const sessionData = {
      email: userInfo.data.email,
      tokens: tokens,
      calendarId: userInfo.data.email
    };

    const redirectBase = process.env.GOOGLE_REDIRECT_URI!.split('/api')[0];
  const response = NextResponse.redirect(new URL('/', redirectBase));
    
    response.cookies.set('session', JSON.stringify(sessionData), {
      httpOnly: true,
      secure: false, 
      maxAge: 60 * 60 * 24 * 7,
      path: '/'
    });

    console.log('--- Session Created, Redirecting ---'); // LOG 6
    return response;
  } catch (error) {
    console.error('--- OAuth Callback Error ---', error);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: 'Authentication failed', details: errorMessage }, { status: 500 });
  }
}
