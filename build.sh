#!/bin/bash

# Build script for deployment

echo "🔨 Building application..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Build complete!"
echo ""
echo "📤 Ready for deployment!"
echo ""
echo "Deploy options:"
echo "1. Vercel: vercel deploy"
echo "2. Heroku: git push heroku main"
echo "3. Railway: railway up"
echo "4. Local: python3 app.py"
