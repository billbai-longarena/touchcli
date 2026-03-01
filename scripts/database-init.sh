#!/bin/bash
# Database initialization script
# Runs migrations and seeds demo data

set -e

echo "🗄️ Initializing database..."

# Load environment variables
if [ -f .env.development ]; then
    set -a && source .env.development && set +a
fi

# Check if database URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set. Set environment variables."
    exit 1
fi

# Navigate to backend
cd backend/python

echo "📝 Running migrations..."
python -m alembic upgrade head

echo "🌱 Seeding demo data..."
python -m agent_service.seeds

echo "✅ Database initialization complete!"
echo ""
echo "Database URL: $DATABASE_URL"
echo "Tables created and demo data seeded."
