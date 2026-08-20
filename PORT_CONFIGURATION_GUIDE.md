# Port Configuration & Conflict Resolution Guide

**Status:** ✅ RESOLVED - All ports now configurable via environment variables

---

## 🔴 **THE PROBLEM (Port Conflict)**

### Error You Were Getting:
```
Error starting userland proxy: listen tcp 0.0.0.0:5432: bind for 0.0.0.0:5432 failed: port is already allocated
```

### Why This Happened:
- Your machine already has a PostgreSQL service running on port 5432
- Docker tried to bind port 5432 but it was already in use
- Docker Compose failed before backend even started

### Result:
- ❌ Database container crashed
- ❌ Backend couldn't start
- ❌ Entire system down

---

## ✅ **THE SOLUTION (Port Flexibility)**

### What We Fixed:

1. **Made PostgreSQL port configurable:**
   ```yaml
   ports:
     - "${POSTGRES_PORT:-5433}:5432"  # Uses 5433 if 5432 is taken
   ```

2. **Made Backend port configurable:**
   ```yaml
   ports:
     - "${BACKEND_PORT:-8000}:8000"
   ```

3. **Made Frontend port configurable:**
   ```yaml
   ports:
     - "${FRONTEND_PORT:-5173}:5173"
   ```

4. **Created `.env` file with defaults:**
   - POSTGRES_PORT=5433 (safe default, alternate to 5432)
   - BACKEND_PORT=8000
   - FRONTEND_PORT=5173

---

## 🚀 **HOW TO USE (3 Scenarios)**

### Scenario 1: Standard Ports (5432 is free)
```bash
# Edit .env:
POSTGRES_PORT=5432
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Then run:
docker compose up --build
```

### Scenario 2: Port Conflict (5432 already in use)
```bash
# Edit .env:
POSTGRES_PORT=5433  # Use alternate port
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Then run:
docker compose up --build

# Connect via alternate port:
psql -h localhost -p 5433 -U ums_user
```

### Scenario 3: Multiple Instances (testing/CI)
```bash
# Edit .env:
POSTGRES_PORT=5434
BACKEND_PORT=8001
FRONTEND_PORT=5174

# Then run:
docker compose up --build

# Access frontend: http://localhost:5174
# Access backend: http://localhost:8001
```

---

## 📋 **COMPLETE SETUP INSTRUCTIONS**

### Step 1: Check Your Machine's Port Usage
```bash
# On Linux/Mac:
netstat -an | grep LISTEN | grep 5432

# On Windows (PowerShell):
netstat -ano | findstr :5432

# If nothing shows up, port 5432 is free!
# If something shows up, use alternate port (5433, 5434, etc.)
```

### Step 2: Configure Ports
```bash
# Copy .env if it doesn't exist:
cp .env.example .env

# Edit .env with your port choices:
nano .env  # or vi, code, etc.
```

### Step 3: Start Services
```bash
# Clean up any old containers:
docker compose down -v

# Build and start:
docker compose up --build
```

### Step 4: Verify Services
```bash
# Check if services started:
docker compose ps

# Should show:
# NAME                COMMAND                  STATUS         PORTS
# postgres            postgres                 Up 30s         0.0.0.0:5433->5432/tcp
# backend             /app/entrypoint.sh       Up 20s         0.0.0.0:8000->8000/tcp
# frontend            npm run dev              Up 15s         0.0.0.0:5173->5173/tcp
```

---

## 🔍 **TROUBLESHOOTING PORT CONFLICTS**

### Issue: "port is already allocated"

**Step 1: Identify which port is conflicting**
```bash
# Example from error message:
# "bind for 0.0.0.0:5432 failed"
# This means port 5432 is in use
```

**Step 2: Find what's using the port**
```bash
# Linux/Mac:
lsof -i :5432
# Output will show:
# COMMAND   PID    USER   TYPE SIZE NODE NAME
# postgres  1234   user   IPv4  50  localhost:5432

# Windows (PowerShell):
netstat -ano | findstr :5432 | findstr LISTEN
```

**Step 3: Choose alternate port**
- If 5432 is in use, try: 5433, 5434, 5435, etc.
- If 8000 is in use, try: 8001, 8002, 8003, etc.
- If 5173 is in use, try: 5174, 5175, 5176, etc.

**Step 4: Update .env and restart**
```bash
# Edit .env:
POSTGRES_PORT=5433  # Change this

# Restart:
docker compose down -v
docker compose up --build
```

### Issue: "Cannot connect to postgres"

**Solution 1: Use internal connection string**
```
# Inside containers, use:
postgresql+psycopg://ums_user:ums_password@postgres:5432/ums_db

# NOT:
postgresql+psycopg://ums_user:ums_password@localhost:5432/ums_db
# (This is already configured correctly)
```

**Solution 2: Check Docker network**
```bash
docker network ls
docker network inspect ums_network  # Should show all 3 containers
```

**Solution 3: Verify healthcheck**
```bash
docker compose logs postgres | tail -20
# Should show: "database system is ready to accept connections"
```

---

## 📊 **ENVIRONMENT VARIABLES REFERENCE**

### PostgreSQL Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `POSTGRES_USER` | ums_user | Database username |
| `POSTGRES_PASSWORD` | ums_password | Database password |
| `POSTGRES_DB` | ums_db | Database name |
| `POSTGRES_PORT` | 5433 | Host machine port (for external access) |

### Backend Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `BACKEND_PORT` | 8000 | API server port |
| `JWT_SECRET_KEY` | dev-only-secret-... | Token signing key |
| `DEFAULT_UNIVERSITY_ID` | 1 | Default university ID |

### Frontend Variables
| Variable | Default | Purpose |
|----------|---------|---------|
| `FRONTEND_PORT` | 5173 | Dev server port |
| `VITE_BACKEND_URL` | http://localhost:8000 | Backend API URL |

---

## 🔐 **SECURITY NOTES**

### Development Environment:
- ✅ Default ports are fine
- ✅ Default credentials are OK for local testing
- ✅ JWT_SECRET_KEY can be dev-only

### Production Environment:
- ❌ NEVER use default passwords
- ❌ ALWAYS change JWT_SECRET_KEY
- ❌ Use proper secrets management (Kubernetes Secrets, Vault, etc.)
- ❌ Never commit `.env` file to git
- ✅ Use strong random values:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

---

## 📚 **DOCKER COMPOSE NETWORKING**

### How Container Communication Works:
```
Host Machine:                Docker Network (ums_network):
─────────────               ──────────────────────────────

:5433 ──── postgres:5432    postgres container (internal 5432)
           (bound to host)  

:8000 ──── backend:8000     backend container
           (bound to host)  - Connects to: postgres:5432
                           
:5173 ──── frontend:5173    frontend container
           (bound to host)  - Connects to: localhost:8000
                             (which is the host's backend)
```

### Key Points:
1. Containers use internal network (ums_network)
2. Services communicate by name: `postgres`, `backend`, `frontend`
3. Host machine binds to ports you configure
4. DATABASE_URL must use service name: `postgres:5432`
5. Frontend URL can be `localhost:8000` (browser uses host machine)

---

## ✅ **VERIFICATION CHECKLIST**

After configuring ports, verify:

```bash
# 1. Services are running:
docker compose ps
# All 3 should show "Up"

# 2. Postgres is responding:
docker compose logs postgres | grep "ready to accept"

# 3. Backend is healthy:
docker compose logs backend | grep "Uvicorn running"

# 4. Frontend is ready:
docker compose logs frontend | grep "Local:"

# 5. Can reach services:
curl http://localhost:8000/health          # Backend
curl http://localhost:5173                 # Frontend (browser)
psql -h localhost -p 5433 -U ums_user     # Database

# 6. Login works:
# Open: http://localhost:5173/login
# Email: admin@university.edu
# Password: AdminPassword123!
```

---

## 🆘 **QUICK TROUBLESHOOTING**

| Error | Solution |
|-------|----------|
| "port is already allocated" | Change POSTGRES_PORT in .env |
| "Cannot connect to postgres" | Check Docker network: `docker network inspect ums_network` |
| "Backend loops trying to connect" | Wait for postgres healthcheck to pass (check logs) |
| "Frontend can't reach backend" | Verify VITE_BACKEND_URL in .env and .compose |
| "Services won't start" | Try: `docker compose down -v && docker compose up --build` |
| "Port mappings look wrong" | Check: `docker compose ps` and verify port mappings |

---

## 📖 **REFERENCE FILES**

- `.env` - Current environment configuration
- `.env.example` - Example configuration template
- `docker-compose.yml` - Service definitions
- `backend/.env.example` - Backend-specific configuration
- This file - Port configuration guide

---

## 🎉 **FINAL STATUS**

```
✅ Port Conflicts: RESOLVED
✅ Configurable Ports: IMPLEMENTED
✅ Default Alternatives: PROVIDED
✅ Documentation: COMPLETE
✅ Ready for All Scenarios: YES!
```

---

**Everything is now flexible and conflict-free!** 🚀

You can run multiple instances, use different ports, or change to standard ports whenever needed.
