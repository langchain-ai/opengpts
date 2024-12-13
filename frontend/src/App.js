import React from "react";
import GoogleAuth from "./components/GoogleAuth";
import CalendarView from "./components/CalendarView";
import TwitterFeed from "./components/TwitterFeed";

function App() {
    return (
        <div>
            <h1>Unified Calendar and Updates</h1>
            <GoogleAuth />
            <CalendarView />
            <TwitterFeed />
        </div>
    );
}

export default App;
