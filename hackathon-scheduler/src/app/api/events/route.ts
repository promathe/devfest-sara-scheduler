import { NextRequest, NextResponse } from 'next/server';

interface SessionData {
  tokens: {
    access_token?: string;
    id_token?: string;
  };
}

export const dynamic = 'force-dynamic'; // Prevent caching

export async function GET(request: NextRequest) {
  try {
    // 1. Validate Session
    const sessionCookie = request.cookies.get('session')?.value;
    if (!sessionCookie) {
      return NextResponse.json({ success: false, message: 'Not authenticated' }, { status: 401 });
    }

    const session = JSON.parse(sessionCookie) as SessionData;
    // Use access_token or id_token depending on what Google gave you
    const userToken = session.tokens.access_token || session.tokens.id_token || "";

    if (!userToken) {
      return NextResponse.json({ success: false, message: 'Invalid token' }, { status: 401 });
    }

    // 2. Prepare request to NLP Server (UPDATED FOR QUERY PARAM)
    // We create a URL object to safely append parameters
    const nlpServerBaseUrl = 'http://localhost:8000/events/upcoming';
    const nlpUrl = new URL(nlpServerBaseUrl);
    
    // Append the token as a query parameter: ?user_token=...
    nlpUrl.searchParams.append('user_token', userToken);

    console.log(`Fetching events from: ${nlpUrl.toString()}`);

    const nlpResponse = await fetch(nlpUrl.toString(), {
      method: 'GET',
      headers: { 
        'Content-Type': 'application/json'
        // Note: 'user_token' is REMOVED from headers
      },
    });

    if (!nlpResponse.ok) {
      console.error('NLP Events Error:', nlpResponse.status);
      // Return empty array on failure so UI doesn't crash
      return NextResponse.json({ upcoming: [] }); 
    }

    const eventsData = await nlpResponse.json();
    return NextResponse.json(eventsData);

  } catch (error) {
    console.error('Events API error:', error);
    return NextResponse.json({ upcoming: [] }, { status: 500 });
  }
}