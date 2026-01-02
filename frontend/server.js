require('dotenv').config();
const express = require('express');
const cors = require('cors');
const path = require('path');
const multer = require('multer');
const fs = require('fs').promises;

const app = express();
const PORT = process.env.PORT || 3000;

// Configure multer for file uploads
const storage = multer.diskStorage({
    destination: async (req, file, cb) => {
        const uploadDir = path.join(__dirname, 'uploads');
        try {
            await fs.mkdir(uploadDir, { recursive: true });
            cb(null, uploadDir);
        } catch (error) {
            cb(error);
        }
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, uniqueSuffix + '-' + file.originalname);
    }
});

const upload = multer({
    storage: storage,
    limits: {
        fileSize: 10 * 1024 * 1024 // 10MB limit
    },
    fileFilter: (req, file, cb) => {
        const allowedTypes = ['.pdf', '.doc', '.docx', '.txt'];
        const ext = path.extname(file.originalname).toLowerCase();
        if (allowedTypes.includes(ext)) {
            cb(null, true);
        } else {
            cb(new Error('Invalid file type. Only PDF, DOC, DOCX, and TXT are allowed.'));
        }
    }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Validate environment variables (Checking API key)
if (!process.env.OPENAI_API_KEY) {
    console.error('ERROR: OPENAI_API_KEY is not set in .env file');
    process.exit(1);
}

// Dynamic import for node-fetch (ESM module)
let fetch;
(async () => {
    fetch = (await import('node-fetch')).default;
})();

// Store session data temporarily (in production, use a database)
const sessionStore = new Map();

// API endpoint to upload resume
app.post('/api/upload-resume', upload.single('resume'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No file uploaded' });
        }

        console.log('Resume uploaded:', req.file.originalname);
        
        res.json({
            success: true,
            filename: req.file.filename,
            originalname: req.file.originalname,
            path: req.file.path,
            size: req.file.size
        });

    } catch (error) {
        console.error('Upload error:', error);
        res.status(500).json({
            error: 'File upload failed',
            message: error.message
        });
    }
});

// API endpoint to create ephemeral token
app.post('/api/session', async (req, res) => {
    try {
        const { 
            model, 
            voice, 
            candidateName, 
            jobDescription, 
            resumeFileName,
            role,
            interviewType,
            duration
        } = req.body;

        // Validate required fields
        if (!candidateName || !jobDescription || !resumeFileName) {
            return res.status(400).json({
                error: 'Missing required fields',
                message: 'Name, job description, and resume are required'
            });
        }

        console.log('Creating OpenAI Realtime session...');
        console.log('Candidate:', candidateName);
        console.log('Role:', role);
        console.log('Interview Type:', interviewType);
        console.log('Duration:', duration, 'minutes');
        console.log('Resume:', resumeFileName);
        console.log('Job Description length:', jobDescription.length, 'characters');
        
        // Use dynamic import for fetch
        const fetchModule = await import('node-fetch');
        const nodeFetch = fetchModule.default;
        
        const response = await nodeFetch('https://api.openai.com/v1/realtime/sessions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model || 'gpt-4o-mini-realtime-preview-2024-12-17',
                voice: voice || 'alloy',
                modalities: ['text', 'audio'],
                instructions: `You are conducting a professional ${interviewType} interview for ${candidateName} for the ${role} position. Duration: ${duration} minutes.`
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('OpenAI API Error:', errorData);
            return res.status(response.status).json({
                error: errorData.error?.message || 'Failed to create session'
            });
        }

        const data = await response.json();
        console.log('Session created successfully:', data.id);

        // Store session data
        sessionStore.set(data.id, {
            candidateName,
            role,
            interviewType,
            duration,
            jobDescription,
            resumeFileName,
            createdAt: new Date().toISOString()
        });

        res.json({
            client_secret: data.client_secret.value,
            session_id: data.id,
            expires_at: data.expires_at,
            candidate_name: candidateName,
            interview_config: {
                role,
                type: interviewType,
                duration
            }
        });

    } catch (error) {
        console.error('Server error:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// Get session info
app.get('/api/session/:sessionId', (req, res) => {
    const { sessionId } = req.params;
    const sessionData = sessionStore.get(sessionId);
    
    if (!sessionData) {
        return res.status(404).json({ error: 'Session not found' });
    }
    
    res.json(sessionData);
});

// Delete session data (cleanup)
app.delete('/api/session/:sessionId', async (req, res) => {
    const { sessionId } = req.params;
    const sessionData = sessionStore.get(sessionId);
    
    if (sessionData) {
        // Clean up uploaded resume file if needed
        // (Optional: implement file cleanup logic here)
        sessionStore.delete(sessionId);
    }
    
    res.json({ success: true });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        openai_configured: !!process.env.OPENAI_API_KEY,
        model: 'gpt-4o-mini-realtime-preview-2024-12-17',
        active_sessions: sessionStore.size,
        uptime: process.uptime()
    });
});

// Serve frontend
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Error:', error);
    res.status(500).json({
        error: 'Internal server error',
        message: error.message
    });
});

// Cleanup old sessions periodically (every hour)
setInterval(() => {
    const now = Date.now();
    for (const [sessionId, data] of sessionStore.entries()) {
        const createdAt = new Date(data.createdAt).getTime();
        const ageInHours = (now - createdAt) / (1000 * 60 * 60);
        
        if (ageInHours > 24) {
            console.log('Cleaning up old session:', sessionId);
            sessionStore.delete(sessionId);
        }
    }
}, 60 * 60 * 1000); // Run every hour

// Start server
app.listen(PORT, () => {
    console.log(`
╔════════════════════════════════════════════════════════╗
║     Mock Interview POC Server                          ║
╠════════════════════════════════════════════════════════╣
║  Server running on: http://localhost:${PORT}            ║
║  OpenAI API Key: ${process.env.OPENAI_API_KEY ? '✓ Configured' : '✗ Missing'}                     ║
║  Model: gpt-4o-mini-realtime-preview-2024-12-17        ║
║  Environment: ${process.env.NODE_ENV || 'development'}                              ║
║  Upload Directory: ./uploads                           ║
╚════════════════════════════════════════════════════════╝
    `);
});