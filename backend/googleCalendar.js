const { google } = require('googleapis');
const OAuth2 = google.auth.OAuth2;

// Set up Google API
const oauth2Client = new OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    "http://localhost:3000/google-callback"
);

module.exports = oauth2Client;
