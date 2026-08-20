# UMS — Setup & Deployment Instructions

## ⚡ Quick Start (Recommended)

```bash
# 1. Extract this zip
unzip ums-final-fixed.zip
cd ums-final-fixed

# 2. Start with Docker Compose (all-in-one)
docker compose up --build

# 3. Wait for logs to show:
# backend_1    | Uvicorn running on http://0.0.0.0:8000
# frontend_1   | Local: http://localhost:5173

# 4. Open in browser
# http://localhost:5173/login

# 5. Login with default admin:
# Email: admin@university.edu
# Password: AdminPassword123!
```

**That's it!** All migrations, seeding, and setup happen automatically. ✅

---

## 🔧 What's Fixed (vs Original)

### Issue #1: Backend URL (docker-compose.yml)
**Before:** `VITE_BACKEND_URL: http://backend:8000` (unreachable from browser)
**After:** `VITE_BACKEND_URL: http://localhost:8000` (works via Docker port mapping)

### Issue #2: CORS Middleware (backend/app/main.py)
**Before:** No CORS configuration → browser blocks requests
**After:** CORSMiddleware configured → browser allows requests

**Result:** Login page now works! ✅

---

## 📋 System Requirements

- **Docker Desktop** (version 4.0+)
- **Docker Compose** (included with Docker Desktop)
- Ports available: `5173`, `8000`, `5432`

---

## 🗂️ Project Structure

```
ums-final-fixed/
├── docker-compose.yml           ← Database, backend, frontend config
├── backend/
│   ├── app/
│   │   ├── main.py              ← ✅ FIXED: CORS middleware added
│   │   ├── api/v1/              ← Auth, academic, users, exams, etc.
│   │   ├── models/              ← SQLAlchemy models
│   │   ├── schemas/             ← Pydantic schemas
│   │   ├── services/            ← Business logic
│   │   └── core/                ← Config, errors, auth, rate limiting
│   ├── alembic/                 ← Database migrations
│   ├── scripts/                 ← Seed script (creates admin)
│   ├── tests/                   ← Unit tests
│   ├── requirements.txt          ← Python dependencies (includes bcrypt==4.0.1)
│   ├── Dockerfile               ← Docker image for backend
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── pages/               ← React pages (Login, Dashboard, etc.)
│   │   ├── contexts/            ← Auth context
│   │   ├── lib/                 ← API client, utilities
│   │   └── types/               ← TypeScript types
│   ├── package.json             ← Node dependencies
│   ├── vite.config.ts           ← Vite dev server config
│   ├── Dockerfile               ← Docker image for frontend
│   └── tailwind.config.js        ← TailwindCSS config
├── README.md                    ← Project overview
└── SETUP_INSTRUCTIONS.md        ← This file
```

---

## 🚀 Deployment Methods

### Method 1: Docker Compose (Easiest — Recommended)

```bash
# One command does everything
docker compose up --build

# Access points:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
# Database: postgresql://localhost:5432/ums_db

# Credentials
# Username: ums_user
# Password: ums_password
```

**How it works:**
1. Starts PostgreSQL container
2. Runs database migrations (`alembic upgrade head`)
3. Seeds admin account (`python -m scripts.seed`)
4. Starts FastAPI backend on port 8000
5. Starts Vite frontend dev server on port 5173

**Stop services:**
```bash
docker compose down
```

**Wipe database and restart clean:**
```bash
docker compose down -v
docker compose up --build
```

---

### Method 2: Manual Setup (Without Docker)

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env to set DATABASE_URL if needed

# Run migrations
alembic upgrade head

# Seed database (creates admin account)
python -m scripts.seed

# Start API server
uvicorn app.main:app --reload
```

**Backend now runs at:** http://localhost:8000

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set backend URL (dev server proxies to backend)
export VITE_BACKEND_URL=http://localhost:8000
# Or it defaults to localhost:8000

# Start dev server
npm run dev
```

**Frontend now runs at:** http://localhost:5173

---

## 🔐 First Login

**Default admin account created by seed script:**

```
Email: admin@university.edu
Password: AdminPassword123!
```

⚠️ **Change this password immediately after first login for security.**

---

## ✅ Verification Checklist

After starting services:

- [ ] Docker containers running: `docker ps` shows 3 containers (postgres, backend, frontend)
- [ ] Backend health: `curl http://localhost:8000/health` returns `{"status":"ok"}`
- [ ] Frontend loads: http://localhost:5173 shows login page
- [ ] Login succeeds: admin@university.edu / AdminPassword123!
- [ ] Dashboard displays: You see the admin dashboard after login
- [ ] API docs: http://localhost:8000/docs shows Swagger documentation

---

## 🧪 Testing

### Test Login Endpoint
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@university.edu",
    "password": "AdminPassword123!"
  }'

# Should return:
# {
#   "access_token": "eyJ0eXAi...",
#   "refresh_token": "eyJ0eXAi...",
#   "expires_in": 1800
# }
```

### Run Unit Tests
```bash
cd backend
python -m pytest tests/
```

### Test CORS Headers
```bash
curl -i -X OPTIONS http://localhost:8000/api/v1/auth/login \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST"

# Should include:
# access-control-allow-origin: http://localhost:5173
# access-control-allow-methods: *
```

---

## 📊 Database Access

### Via Docker (Recommended)
```bash
docker compose exec postgres psql -U ums_user -d ums_db

# Common queries:
SELECT COUNT(*) FROM users;
SELECT email, role FROM users LIMIT 5;
\dt  # List all tables
```

### Via psql (if installed locally)
```bash
psql postgresql://ums_user:ums_password@localhost:5432/ums_db

# Or set DATABASE_URL
export DATABASE_URL="postgresql://ums_user:ums_password@localhost:5432/ums_db"
psql $DATABASE_URL
```

---

## 🐛 Troubleshooting

### Problem: Containers won't start

**Solution:**
```bash
# Check logs
docker compose logs

# Clean rebuild
docker compose down -v
docker compose up --build
```

### Problem: Port already in use

**Solution:**
```bash
# Find what's using the port
lsof -i :5173  # Frontend port
lsof -i :8000  # Backend port
lsof -i :5432  # Database port

# Kill the process
kill -9 <PID>

# Or change docker-compose.yml ports
```

### Problem: Login still fails

**Solution:**
```bash
# Verify fixes are applied
grep "localhost:8000" docker-compose.yml
grep "CORSMiddleware" backend/app/main.py

# Check backend logs
docker compose logs backend | tail -30

# Verify CORS headers
curl -i -X OPTIONS http://localhost:8000/api/v1/auth/login \
  -H "Origin: http://localhost:5173"
```

### Problem: Database migration fails

**Solution:**
```bash
# Check database connection
docker compose exec postgres pg_isready

# View migration logs
docker compose logs backend | grep alembic

# Manually run migrations
docker compose exec backend alembic upgrade head

# Reseed
docker compose exec backend python -m scripts.seed
```

---

## 🔒 Production Deployment

⚠️ **Not for production use as-is. Before deploying:**

1. **Change JWT_SECRET_KEY** in docker-compose.yml (currently: "dev-only-secret-change-in-production")
2. **Restrict CORS origins** to your actual domain in `backend/app/main.py`
3. **Use environment variables** instead of hardcoding secrets
4. **Build frontend** for production: `npm run build` (currently uses dev server)
5. **Use reverse proxy** (nginx/Caddy) to serve frontend and proxy `/api`
6. **Enable HTTPS** with SSL certificates
7. **Configure secure cookies** for refresh tokens

See **backend/app/main.py** lines 29-44 for CORS configuration to update for production.

---

## 📚 Documentation

For detailed information:

- **API Documentation:** http://localhost:8000/docs (interactive Swagger UI)
- **Project README:** See README.md in this directory
- **Backend Code:** backend/app/api/v1/ (routers for each module)
- **Frontend Code:** frontend/src/pages/ (React components for each page)

---

## 🆘 Still Having Issues?

1. **Check Docker logs:** `docker compose logs -f backend`
2. **Verify files:** Check that `docker-compose.yml` has `localhost:8000` and `backend/app/main.py` has CORS middleware
3. **Browser console:** F12 → Console tab for JavaScript errors
4. **Network tab:** F12 → Network tab to see HTTP requests/responses
5. **Database:** `docker compose exec postgres psql -U ums_user -d ums_db` to verify data

---

## ✨ Next Steps After Setup Works

1. ✅ Test all four roles (Student, Teacher, Admin, Parent)
2. ✅ Verify academic structure, exam features, etc.
3. ✅ Check attendance marking works
4. ✅ Test fee invoicing and payment flow
5. ✅ Verify transcript generation (PDF)
6. ✅ Test scheduling and conflict detection

---

## 📞 Key Contacts for This Project

**Instructor:** ICT Bangladesh, Batch 26/3
**Submission Format:** Follow instructor's folder structure requirements

---

## 🎉 You're All Set!

The system is ready to run and all login issues have been fixed.

```bash
# One command to start everything:
docker compose up --build

# Then open: http://localhost:5173/login
# Login: admin@university.edu / AdminPassword123!
```

Good luck! 🚀
