#!/bin/bash
# Production deployment script.
# Builds containers, boots data services, runs DB migration, starts backend, and builds frontend assets.

set -e

echo "🚀 Starting DSP Eco Tracker deployment..."

# Step 1: Build and start services
echo "📦 Building Docker containers..."
docker-compose -f docker-compose.prod.yml build

echo "🗄️ Starting database services..."
docker-compose -f docker-compose.prod.yml up -d mysql redis

echo "⏳ Waiting for database to be ready..."
sleep 30

# Step 2: Run database migration
echo "🔄 Running database migration..."
python database/migrate_csv_to_mysql.py

# Step 3: Start backend service
echo "🖥️ Starting backend service..."
docker-compose -f docker-compose.prod.yml up -d backend

# Step 4: Build frontend for Netlify
echo "🌐 Building frontend for deployment..."
cd frontend/website
npm install
npm run build

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Upload frontend/website/dist to Netlify"
echo "2. Point domain to your server IP"
echo "3. Set up SSL certificate"
echo "4. Configure environment variables on hosting platform"
echo ""
echo "🔗 Access points:"
echo "- Backend API: http://your-server:5000"
echo "- Database: MySQL on port 3306"
echo "- Redis Cache: Port 6379"