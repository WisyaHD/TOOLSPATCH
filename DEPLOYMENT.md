# Deployment Guide

Aplikasi ini adalah Flask backend + HTML/JS frontend. Ada beberapa opsi deployment:

## Option 1: Vercel (Recommended)
Vercel support Python dengan serverless functions

```bash
npm install -g vercel
vercel
```

## Option 2: Heroku
```bash
heroku create your-app-name
git push heroku main
```

## Option 3: Railway
https://railway.app - Drop-in Heroku replacement

## Option 4: PythonAnywhere
https://www.pythonanywhere.com

## Option 5: Render
https://render.com

## Option 6: Local / Self-hosted
```bash
python3 app.py
```

### Important Notes:
- MongoDB connection required (update .env)
- File size limit untuk Netlify: 100MB max
- Large data files (uploads/) excluded from git

### Environment Variables (.env):
```
MONGODB_URI=your_mongodb_uri
DB_MEMBER=your_member_db
DB_JUAL=your_jual_db
DB_BELI=your_beli_db
```

## For Netlify (Static Only):
If you want to use Netlify for frontend only, separate the API:
1. Deploy Flask backend to Heroku/Railway/Render
2. Deploy frontend to Netlify
3. Update API_URL in app.js to point to backend
