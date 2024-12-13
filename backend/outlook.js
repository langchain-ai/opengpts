const fetch = require('node-fetch');

// Route to get Outlook Auth URL
app.get('/outlook-auth-url', (req, res) => {
    const outlookAuthUrl = `https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost:3000/outlook-callback&response_mode=query&scope=Calendars.Read`;
    res.send({ url: outlookAuthUrl });
});

// Route to handle Outlook callback
app.get('/outlook-callback', async (req, res) => {
    const { code } = req.query;

    // Exchange code for access token
    const tokenResponse = await fetch(`https://login.microsoftonline.com/common/oauth2/v2.0/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `client_id=YOUR_CLIENT_ID&scope=Calendars.Read&code=${code}&redirect_uri=http://localhost:3000/outlook-callback&grant_type=authorization_code&client_secret=YOUR_CLIENT_SECRET`
    });
    const tokenData = await tokenResponse.json();

    // Fetch calendar events
    const eventsResponse = await fetch('https://graph.microsoft.com/v1.0/me/events', {
        headers: { Authorization: `Bearer ${tokenData.access_token}` },
    });
    const events = await eventsResponse.json();
    res.send(events.value);
});
