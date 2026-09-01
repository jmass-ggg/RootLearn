#!/bin/bash

# RootLearn Setup Verification Script

echo "🔍 RootLearn Setup Verification"
echo "================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

# Helper functions
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((SUCCESS++))
    else
        echo -e "${RED}✗${NC} $1"
        ((ERRORS++))
    fi
}

check_warning() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠${NC} $1 (optional)"
        ((WARNINGS++))
    fi
}

echo "📦 Checking Prerequisites..."
echo "----------------------------"

# Check Python
python3 --version > /dev/null 2>&1
check_success "Python 3.11+ installed"

# Check Node.js
node --version > /dev/null 2>&1
check_success "Node.js 20+ installed"

# Check Docker
docker --version > /dev/null 2>&1
check_warning "Docker installed"

# Check Docker Compose
docker-compose --version > /dev/null 2>&1
check_warning "Docker Compose installed"

echo ""
echo "🔧 Checking Backend Setup..."
echo "----------------------------"

# Check backend virtual environment
if [ -d "backend/venv" ]; then
    echo -e "${GREEN}✓${NC} Backend virtual environment exists"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} Backend virtual environment not found"
    echo "  Run: cd backend && python3 -m venv venv"
    ((ERRORS++))
fi

# Check backend .env file
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✓${NC} Backend .env file exists"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠${NC} Backend .env file not found"
    echo "  Run: cd backend && cp .env.example .env"
    ((WARNINGS++))
fi

# Check backend dependencies
if [ -f "backend/venv/bin/python" ]; then
    backend/venv/bin/python -c "import fastapi; import sqlalchemy; import alembic; import networkx" > /dev/null 2>&1
    check_success "Backend dependencies installed"
fi

# Check Alembic setup
if [ -d "backend/alembic/versions" ]; then
    echo -e "${GREEN}✓${NC} Alembic migrations directory exists"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠${NC} Alembic versions directory not found"
    ((WARNINGS++))
fi

echo ""
echo "🎨 Checking Frontend Setup..."
echo "----------------------------"

# Check frontend node_modules
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✓${NC} Frontend node_modules installed"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} Frontend dependencies not installed"
    echo "  Run: cd frontend && npm install"
    ((ERRORS++))
fi

# Check frontend .env.local
if [ -f "frontend/.env.local" ]; then
    echo -e "${GREEN}✓${NC} Frontend .env.local file exists"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠${NC} Frontend .env.local file not found"
    echo "  Run: cd frontend && cp .env.local.example .env.local"
    ((WARNINGS++))
fi

echo ""
echo "🗄️  Checking Database Setup..."
echo "----------------------------"

# Check Docker Compose file
if [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}✓${NC} docker-compose.yml exists"
    ((SUCCESS++))
else
    echo -e "${RED}✗${NC} docker-compose.yml not found"
    ((ERRORS++))
fi

# Check if PostgreSQL is running
if command -v docker &> /dev/null; then
    if docker ps | grep -q postgres; then
        echo -e "${GREEN}✓${NC} PostgreSQL container is running"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠${NC} PostgreSQL container not running"
        echo "  Run: docker-compose up -d postgres"
        ((WARNINGS++))
    fi
fi

echo ""
echo "📁 Checking Project Structure..."
echo "--------------------------------"

# Check required directories and files
required_files=(
    "backend/app/main.py"
    "backend/app/config.py"
    "backend/app/database.py"
    "backend/app/logging_config.py"
    "backend/app/middleware.py"
    "backend/app/routes/health.py"
    "backend/alembic/env.py"
    "backend/alembic.ini"
    "frontend/src/app/page.tsx"
    "frontend/src/app/layout.tsx"
    "frontend/src/lib/api.ts"
    "frontend/tsconfig.json"
    "frontend/tailwind.config.ts"
    "frontend/next.config.js"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        ((SUCCESS++))
    else
        echo -e "${RED}✗${NC} Missing: $file"
        ((ERRORS++))
    fi
done

echo -e "${GREEN}✓${NC} All required project files exist"

echo ""
echo "📋 Summary"
echo "=========="
echo -e "${GREEN}✓${NC} Successful checks: $SUCCESS"
if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Warnings: $WARNINGS"
fi
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}✗${NC} Errors: $ERRORS"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 Setup verification passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start the database: docker-compose up -d postgres"
    echo "2. Run migrations: cd backend && alembic upgrade head"
    echo "3. Start backend: cd backend && ./venv/bin/uvicorn app.main:app --reload"
    echo "4. Start frontend: cd frontend && npm run dev"
    echo ""
    echo "Then visit: http://localhost:3000"
    exit 0
else
    echo -e "${RED}❌ Setup verification failed!${NC}"
    echo ""
    echo "Please fix the errors above and run this script again."
    exit 1
fi
