'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

// --- HELPER COMPONENT: Scramble/Decode Effect ---
const ScrambleText = ({ text, className }: { text: string; className?: string }) => {
  const [displayText, setDisplayText] = useState('');
  const chars = '!<>-_\\/[]{}—=+*^?#________';

  useEffect(() => {
    let iteration = 0;
    
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split('')
          .map((letter, index) => {
            if (index < iteration) {
              return letter;
            }
            return chars[Math.floor(Math.random() * chars.length)];
          })
          .join('')
      );

      if (iteration >= text.length) {
        clearInterval(interval);
      }
      
      // [CHANGE 1] Speed up text decoding (was 1/3)
      // Higher number = Faster decoding. 1 = 1 char per tick.
      iteration += 1; 
    }, 30);

    return () => clearInterval(interval);
  }, [text]);

  return <span className={className}>{displayText}</span>;
};

export default function TaskScheduler() {
  // --- Chat & Auth State ---
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello, I’m SARA. How can I help you schedule your week?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // AUTH STATES
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [calendarId, setCalendarId] = useState('');

  // LOADING ANIMATION STATES
  const [minLoadTimePassed, setMinLoadTimePassed] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState<'active' | 'fading' | 'complete'>('active');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  // --- [CHANGE 2] Reduced Loading Time ---
  useEffect(() => {
    const timer = setTimeout(() => {
      setMinLoadTimePassed(true);
    }, 2000); // Reduced from 4000ms to 2000ms (2 seconds)
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!isCheckingAuth && minLoadTimePassed && loadingPhase === 'active') {
      setLoadingPhase('fading');
      setTimeout(() => {
        setLoadingPhase('complete');
      }, 800);
    }
  }, [isCheckingAuth, minLoadTimePassed, loadingPhase]);

  const checkAuthStatus = async () => {
    try {
      const response = await fetch('/api/auth/status');
      const data = await response.json();
      
      if (data.authenticated) {
        setIsAuthenticated(true);
        setCalendarId(data.calendarId || data.email);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setIsCheckingAuth(false);
    }
  };

  const handleGoogleLogin = async () => {
    window.location.href = '/api/auth/google';
  };

  // --- [CHANGE 3] Fixed Logout Bug ---
  const handleLogout = async () => {
    // 1. Immediately bring back the loading overlay to hide the UI transition
    setLoadingPhase('active'); 
    
    // 2. Set checking to true to unmount the main/login interface underneath
    setIsCheckingAuth(true);

    await fetch('/api/auth/logout', { method: 'POST' });
    setIsAuthenticated(false);
    
    // 3. Reload page (which will restart the animation from scratch)
    window.location.href = '/';
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = input;
    setInput('');

    const updatedMessages = [...messages, { role: 'user', text: userMessage }];
    setMessages(updatedMessages);
    setIsLoading(true);

    try {
      const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      
      const response = await fetch('/api/query/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            messages: updatedMessages, 
            timezone: userTimezone 
        })
      });

      const result = await response.json();

      if (result.response) {
        setMessages(prev => [...prev, { role: 'assistant', text: result.response }]);
        setCalendarId(prev => {
            if (!prev) return prev;
            const baseId = prev.split('&refresh=')[0];
            return `${baseId}&refresh=${Date.now()}`;
        });
      } else {
        setMessages(prev => [...prev, { role: 'assistant', text: "I didn't get a response." }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Connection error. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-screen bg-black overflow-hidden font-sans">
      
      {/* LAYER 1: MAIN CONTENT */}
      {!isCheckingAuth && (
        isAuthenticated ? (
            // --- MAIN APP INTERFACE ---
            <div className="flex h-screen overflow-hidden text-[#e3e3e3]">
              {/* LEFT: Chat Area */}
              <div className="w-[40%] flex flex-col border-r border-[#27272a] bg-[#060606]">
                {/* Header */}
                <div className="p-4 flex items-center justify-between bg-[#060606] z-20 relative border-b border-[#27272a]">
                  <div className="flex items-center gap-2">
                     <div className="flex items-center gap-2 text-[#c4c7c5]">
                       <span className="font-semibold text-xl tracking-tight bg-gradient-to-r from-[#FF512F] to-[#F09819] text-transparent bg-clip-text">SARA</span>
                       <span className="text-xs bg-[#27272a] border border-[#333] px-2 py-0.5 rounded text-[#e3e3e3]">Beta</span>
                     </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                     <Link 
                       href="/upcoming" 
                       className="text-sm text-[#8e918f] hover:text-[#e3e3e3] hover:bg-[#1a1a1a] px-3 py-1.5 rounded-full transition-colors flex items-center gap-2"
                     >
                       <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                       Upcoming
                     </Link>
                     
                     <button 
                        onClick={handleLogout}
                        className="text-sm text-[#8e918f] hover:text-[#e3e3e3] hover:bg-[#1a1a1a] px-3 py-1.5 rounded-full transition-colors"
                     >
                        Sign out
                     </button>
                  </div>
                </div>

                {/* Chat History */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6 no-scrollbar">
                  {messages.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div 
                        className={`max-w-[85%] p-4 
                          ${msg.role === 'user' 
                            ? 'bg-[#27272a]/50 backdrop-blur-md border border-[#3f3f46]/50 rounded-2xl rounded-tr-sm' 
                            : 'bg-[#1a1a1a] border border-[#27272a] rounded-2xl rounded-tl-sm' 
                          }`}
                      >
                        {msg.role === 'assistant' && (
                          <div className="flex items-center gap-2 mb-2">
                             <span className="font-medium text-sm bg-gradient-to-r from-[#FF512F] to-[#F09819] text-transparent bg-clip-text">SARA</span>
                          </div>
                        )}
                        <p className="text-[15px] leading-7 text-[#e3e3e3] whitespace-pre-wrap">
                          {msg.text}
                        </p>
                      </div>
                    </div>
                  ))}
                  
                  {isLoading && (
                     <div className="flex justify-start animate-pulse">
                        <div className="max-w-[85%] p-4 bg-[#1a1a1a] border border-[#27272a] rounded-2xl rounded-tl-sm">
                          <div className="flex items-center gap-2 mb-2">
                             <span className="font-medium text-sm text-[#F09819]">SARA</span>
                          </div>
                          <div className="h-4 bg-[#27272a] rounded w-24"></div>
                        </div>
                     </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-4 pb-6">
                  <div className="relative bg-[#060606] rounded-full border border-[#27272a] focus-within:border-[#F09819] focus-within:bg-[#060606] transition-all duration-200">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSend()}
                      placeholder="Ask SARA to schedule..."
                      className="w-full bg-transparent text-[#e3e3e3] placeholder-[#666] px-6 py-4 pr-14 rounded-full focus:outline-none"
                      disabled={isLoading}
                    />
                    <button
                      onClick={handleSend}
                      disabled={isLoading || !input.trim()}
                      className="absolute right-2 top-2 p-2 rounded-full hover:bg-[#1a1a1a] text-[#c4c7c5] disabled:opacity-50 transition-colors"
                    >
                      <svg className="w-6 h-6 transform rotate-90" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              {/* RIGHT: Calendar Area (60%) */}
              <div className="w-[60%] bg-[#000000] flex flex-col p-2">
                <div className="flex-1 rounded-2xl overflow-hidden shadow-lg border border-[#27272a] relative">
                  {calendarId ? (
                    <iframe
                      key={calendarId}
                      src={`https://calendar.google.com/calendar/embed?src=${encodeURIComponent(calendarId.split('&')[0])}&ctz=Asia%2FKolkata&mode=MONTH&showTitle=0&showNav=1&showPrint=0&showTabs=1&bgcolor=%23ececeb`}
                      style={{ 
                          border: 0, 
                          width: '100%', 
                          height: '100%',
                          filter: 'invert(1) contrast(0.95) saturate(0.8)'
                      }}
                      frameBorder="0"
                      scrolling="no"
                      className="absolute inset-0"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-[#8e918f]">
                        Loading Calendar...
                    </div>
                  )}
                </div>
              </div>
            </div>
        ) : (
            // --- LOGIN SCREEN ---
            <div className="relative flex h-screen w-screen items-center justify-center overflow-hidden font-sans text-white bg-black">
                <video
                  autoPlay
                  loop
                  muted
                  playsInline
                  className="absolute inset-0 z-0 h-full w-full object-cover"
                >
                  <source src="/assets/bg-video.mp4" type="video/mp4" />
                </video>

                <div className="absolute inset-0 z-10 bg-gradient-to-br from-[#FF512F]/30 to-[#F09819]/30 mix-blend-multiply" />

                <div className="relative z-20 mx-auto grid max-w-6xl grid-cols-1 items-center gap-16 px-8 md:grid-cols-2">
                  <div className="animate-fade-in-up flex flex-col items-start space-y-4">
                    <h1 className="bg-gradient-to-r from-[#FF512F] to-[#F09819] bg-clip-text text-9xl font-extrabold leading-none tracking-tighter text-transparent">
                      SARA
                    </h1>
                    <p className="max-w-lg border-l-4 border-[#F09819] pl-6 mt-4 text-xl font-light leading-relaxed text-[#e3e3e3] md:text-2xl">
                      AI-Powered Personal Planning & Scheduling Agent
                    </p>
                  </div>

                  <div className="animate-fade-in-up" style={{ animationDelay: '150ms' }}>
                    <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-10 backdrop-blur-x0.75 shadow-2xl">
                      <div className="absolute -left-20 -top-20 h-40 w-40 rounded-full bg-[#F09819]/20 blur-[80px]" />
                      <div className="relative z-10 space-y-4">
                        <h3 className="text-2xl font-semibold text-white">Your time, optimized.</h3>
                        <p className="max-w-md text-lg leading-relaxed text-[#c4c7c5]">
                          SARA connects with your Google account to intelligently organize your day through simple conversation.
                        </p>
                      </div>
                      <button 
                        onClick={handleGoogleLogin} 
                        className="group relative z-10 mt-10 inline-flex w-full items-center justify-center gap-4 rounded-full bg-white px-8 py-4 text-lg font-medium text-black transition-all duration-300 hover:bg-[#F09819] hover:text-white md:w-auto"
                      >
                        <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M21.35 11.1h-9.17v2.73h6.51c-.33 3.81-3.5 5.44-6.5 5.44C8.36 19.27 5 16.25 5 12c0-4.1 3.2-7.27 7.2-7.27 3.09 0 4.9 1.97 4.9 1.97L19 4.72S16.56 2 12.1 2C6.42 2 2.03 6.8 2.03 12c0 5.05 4.13 10 10.22 10 5.35 0 9.25-3.67 9.25-9.09 0-1.15-.15-1.81-.15-1.81z"/>
                        </svg>
                        Sign in with Google
                        <span className="absolute right-6 opacity-0 transition-all group-hover:translate-x-1 group-hover:opacity-100">→</span>
                      </button>
                    </div>
                  </div>
                </div>
            </div>
        )
      )}

      {/* LAYER 2: LOADING OVERLAY */}
      {loadingPhase !== 'complete' && (
        <div 
          className={`absolute inset-0 z-50 flex flex-col items-center justify-center bg-black text-white font-mono transition-opacity duration-1000 ease-in-out ${
            loadingPhase === 'fading' ? 'opacity-0 pointer-events-none' : 'opacity-100'
          }`}
        >
          {/* BRAND LOGO */}
          <div className="mb-8 h-12 w-12 rounded-full bg-gradient-to-tr from-[#FF512F] to-[#F09819] opacity-80 blur-lg animate-pulse" />

          <div className="flex flex-col items-center gap-2 z-10">
             {/* DECODING TITLE */}
             <h1 className="text-4xl font-bold tracking-widest text-white uppercase">
               <ScrambleText text="SARA" />
             </h1>
             
             {/* SUBTITLE STATUS */}
             <div className="flex items-center gap-3 text-xs text-[#555] mt-2 uppercase tracking-[0.2em]">
               <div className="h-1.5 w-1.5 rounded-full bg-[#F09819] animate-ping" />
               <ScrambleText text="SYSTEM_INITIALIZATION_SEQUENCE_STARTED..." className="text-[#888]" />
             </div>
          </div>

          {/* DECORATIVE CORNERS */}
          <div className="absolute top-10 left-10 h-4 w-4 border-l border-t border-[#333]" />
          <div className="absolute top-10 right-10 h-4 w-4 border-r border-t border-[#333]" />
          <div className="absolute bottom-10 left-10 h-4 w-4 border-l border-b border-[#333]" />
          <div className="absolute bottom-10 right-10 h-4 w-4 border-r border-b border-[#333]" />
        </div>
      )}
    </div>
  );
}