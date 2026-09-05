// MyApify Actor SDK — Node.js
const https = require('https');
const http  = require('http');
const url   = require('url');

const API_URL    = process.env.MYAPIFY_API_URL || 'http://localhost:4280';
const DATASET_ID = process.env.MYAPIFY_DATASET_ID || '';
const API_KEY    = process.env.MYAPIFY_API_KEY || '';

function getInput() {
    return JSON.parse(process.env.ACTOR_INPUT || '{}');
}

function pushData(items) {
    return new Promise((resolve, reject) => {
        const data    = JSON.stringify(Array.isArray(items) ? items : [items]);
        const parsed  = new url.URL(`${API_URL}/api/datasets/${DATASET_ID}/items`);
        const lib     = parsed.protocol === 'https:' ? https : http;
        const options = {
            hostname: parsed.hostname,
            port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
            path: parsed.pathname,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': API_KEY,
                'Content-Length': Buffer.byteLength(data),
            },
        };
        const req = lib.request(options, res => {
            let body = '';
            res.on('data', d => body += d);
            res.on('end', () => resolve(JSON.parse(body)));
        });
        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

module.exports = { getInput, pushData };
