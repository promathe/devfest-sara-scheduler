import { NextRequest, NextResponse } from 'next/server';

// 1. Define strict interfaces
interface InputMessage {
  role: string;
  text?: string;    // Frontend might send 'text'
  content?: string; // Standard format is 'content'
}

interface OutputMessage {
  role: string;
  content: string;
}

interface SessionToken {
  access_token?: string;
  id_token?: string;
}

interface SessionData {
  tokens: SessionToken;
}

interface RequestBody {
  messages: InputMessage[];
  timezone?: string;
}

export const maxDuration = 600; 

export async function POST(request: NextRequest) {
  try {
    // 2. Validate Session
    const sessionCookie = request.cookies.get('session')?.value;
    if (!sessionCookie) {
      return NextResponse.json({ success: false, message: 'Not authenticated' }, { status: 401 });
    }

    // Safe casting with the defined interface
    const session = JSON.parse(sessionCookie) as SessionData;
    const userToken = session.tokens.access_token || session.tokens.id_token || "";

    if (!userToken) {
      return NextResponse.json({ success: false, message: 'Invalid token' }, { status: 401 });
    }

    // 3. Parse and Type-Check Body
    const body = await request.json() as RequestBody;
    const { messages, timezone } = body;

    if (!Array.isArray(messages)) {
       return NextResponse.json({ success: false, message: 'Invalid format: messages must be an array.' }, { status: 400 });
    }

    // 4. Transform Payload (Strictly Typed)
    const formattedMessages: OutputMessage[] = messages.map((msg) => ({
      role: msg.role,
      // Prioritize 'content', fallback to 'text', fallback to empty string
      content: msg.content || msg.text || "" 
    }));

    const nlpPayload = {
      messages: formattedMessages,
      user_token: userToken,
      timezone: "Asia/Kolkata"
    };

    console.log('Sending Payload:', JSON.stringify(nlpPayload, null, 2));

    const nlpServerUrl = 'http://localhost:8000/chat'; 

    // --- TIMEOUT LOGIC ---
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); 

    try {
      const nlpResponse = await fetch(nlpServerUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(nlpPayload),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!nlpResponse.ok) {
        console.error('NLP Server Error:', nlpResponse.status);
        return NextResponse.json({ 
          success: false, 
          message: 'The AI server had trouble processing your request.' 
        });
      }

      const nlpResult = await nlpResponse.json();
      return NextResponse.json(nlpResult);

    } catch (fetchError: unknown) {
       clearTimeout(timeoutId);
       if (fetchError instanceof Error && fetchError.name === 'AbortError') {
         return NextResponse.json({ success: false, message: 'Request timed out.' }, { status: 504 });
       }
       throw fetchError;
    }

  } catch (error) {
    console.error('Processing error:', error);
    return NextResponse.json({ success: false, message: 'Internal server error' }, { status: 500 });
  }
}
