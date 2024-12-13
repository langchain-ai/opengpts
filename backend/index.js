const express = require('express');
const app = express();
const googleCalendar = require('./googleCalendar');

app.use(express.json());

app.listen(3001, () => {
    console.log("Backend running on http://localhost:3001");
});
