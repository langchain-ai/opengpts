import React, { useState } from 'react';

function App() {
    const [authUrl, setAuthUrl] = useState('');
    const [events, setEvents] = useState([]);

    const getAuthUrl = async () => {
        const response = await fetch('http://localhost:3001/auth-url');
        const data = await response.json();
        setAuthUrl(data.url);
    };

    const fetchEvents = async () => {
        const response = await fetch('http://localhost:3001/callback');
        const data = await response.json();
        setEvents(data);
    };

    return (
        <div>
            <h1>Unified Calendar</h1>
            <button onClick={getAuthUrl}>Connect Google Calendar</button>
            {authUrl && (
                <a href={authUrl} target="_blank" rel="noopener noreferrer">
                    Authenticate Google
                </a>
            )}
            <button onClick={fetchEvents}>Fetch Calendar Events</button>
            <ul>
                {events.map((event, index) => (
                    <li key={index}>{event.summary}</li>
                ))}
            </ul>
        </div>
    );
}

export default App;
