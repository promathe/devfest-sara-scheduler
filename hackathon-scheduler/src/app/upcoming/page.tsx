'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

// --- Types ---
interface EventItem {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  date_label: string;
  status: 'confirmed' | 'tentative' | 'cancelled';
  is_urgent: boolean;
}

interface UpcomingResponse {
  upcoming: EventItem[];
}

export default function UpcomingPage() {
  const [events, setEvents] = useState<EventItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [calendarId, setCalendarId] = useState('');

  useEffect(() => {
    // 1. Get Auth Status & Calendar ID
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        if (data.authenticated) {
          setCalendarId(data.calendarId || data.email);
        } else {
            // Redirect if not logged in
            window.location.href = '/';
        }
      } catch (error) {
        console.error('Auth check failed', error);
      }
    };

    // 2. Fetch Events
    const fetchEvents = async () => {
      try {
        const res = await fetch('/api/events');
        const data: UpcomingResponse = await res.json();
        setEvents(data.upcoming || []);
      } catch (error) {
        console.error("Failed to fetch events", error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
    fetchEvents();
  }, []);

  return (
    // Main Container: Changed from #131314 to #000000
    <div className="flex h-screen overflow-hidden bg-[#000000] text-[#e3e3e3] font-sans">
      
      {/* LEFT: Events List (40%) */}
      {/* Changed bg-[#1e1f20] -> #060606 and border-[#444746] -> #27272a */}
      <div className="w-[40%] flex flex-col border-r border-[#27272a] bg-[#060606]">
        
        {/* Header */}
        {/* Changed bg-[#1e1f20] -> #060606 and border -> #27272a */}
        <div className="p-4 flex items-center justify-between bg-[#060606] border-b border-[#27272a]">
          <div className="flex items-center gap-3">
            {/* Back Arrow Hover: #1a1a1a */}
            <Link href="/" className="p-2 -ml-2 rounded-full hover:bg-[#1a1a1a] text-[#c4c7c5] transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            </Link>
            <h1 className="font-semibold text-xl text-[#e3e3e3]">Upcoming Events</h1>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 no-scrollbar">
          {isLoading ? (
            <div className="text-center text-[#8e918f] mt-10 animate-pulse">Loading schedule...</div>
          ) : events.length === 0 ? (
            <div className="text-center text-[#8e918f] mt-10">No upcoming events found.</div>
          ) : (
            <div className="space-y-6">
              {events.map((evt, index) => {
                const showDateHeader = index === 0 || events[index-1].date_label !== evt.date_label;
                return (
                  <div key={evt.id} className="animate-fade-in-up" style={{ animationDelay: `${index * 50}ms` }}>
                    {showDateHeader && (
                      <h3 className="text-xs font-bold text-[#F09819] uppercase tracking-wider mb-3 mt-2">
                        {evt.date_label}
                      </h3>
                    )}
                    
                    {/* Event Card: 
                        - Base: bg-[#1a1a1a] (Dark Grey box)
                        - Border: border-[#27272a]
                        - Hover: bg-[#222222] 
                    */}
                    <div className={`relative p-4 rounded-xl border transition-all hover:bg-[#222222] group ${
                        evt.is_urgent 
                            ? 'border-[#EA4335]/50 bg-[#EA4335]/5' 
                            : 'border-[#27272a] bg-[#1a1a1a]'
                    }`}>
                        <div className="flex justify-between items-start mb-2">
                            <h4 className={`font-medium text-lg ${evt.status === 'tentative' ? 'italic text-[#c4c7c5]' : 'text-[#e3e3e3]'}`}>
                                {evt.title}
                            </h4>
                            {evt.is_urgent && (
                                <span className="text-[10px] bg-[#EA4335] text-white px-2 py-0.5 rounded-full uppercase font-bold tracking-wide">
                                    Urgent
                                </span>
                            )}
                        </div>
                        
                        <div className="flex items-center text-sm text-[#8e918f] gap-4">
                            <div className="flex items-center gap-1.5">
                                <svg className="w-4 h-4 text-[#F09819]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                                {evt.start_time} - {evt.end_time}
                            </div>
                            {evt.status === 'tentative' && (
                                <span className="text-[#F09819] text-xs px-2 py-0.5 border border-[#F09819]/30 rounded-full">Tentative</span>
                            )}
                        </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* RIGHT: Calendar Area (60%) */}
      {/* Changed bg to #000000 to match main theme */}
      <div className="w-[60%] bg-[#000000] flex flex-col p-2">
        {/* Changed border to #27272a */}
        <div className="flex-1 rounded-2xl overflow-hidden shadow-lg border border-[#27272a] relative">
          {calendarId ? (
            <iframe
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
  );
}