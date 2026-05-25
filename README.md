# ChallengeHub WebSystem

This repository contains the first implementation iteration of the ChallengeHub web system:
- Roles: `Admin`, `Moderator`, `BusinessClient`
- Web-only scope for administration, moderation, and business analytics
- Mobile `.vpk` download button on public landing page

## Stack
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Database target: MySQL (configured in architecture, integration in next phase)

## Repository Structure
- `apps/web-dashboard` - web frontend
- `apps/backend-api` - backend API skeleton
- `packages/shared-contracts` - shared domain contracts

## Run (after installing dependencies)

### 0) Prepare MySQL
Create database and user (example):
```sql
CREATE DATABASE challengehub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'challengehub'@'localhost' IDENTIFIED BY 'challengehub';
GRANT ALL PRIVILEGES ON challengehub.* TO 'challengehub'@'localhost';
FLUSH PRIVILEGES;
```

Backend reads DSN from env var `CH_MYSQL_DSN`.
Default DSN:
`mysql+pymysql://challengehub:challengehub@localhost:3306/challengehub`

### Frontend
```bash
cd apps/web-dashboard
npm install
npm run dev
```

### Backend
```bash
cd apps/backend-api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# optional: set custom DSN
# set CH_MYSQL_DSN=mysql+pymysql://user:pass@localhost:3306/challengehub
uvicorn app.main:app --reload
```

Backend starts on `http://localhost:8000` and frontend should run on `http://localhost:5173`.

## Demo Accounts
- `admin@challengehub.local` / `admin123`
- `moderator@challengehub.local` / `moderator123`
- `business@challengehub.local` / `business123`

## Current Status
Implemented:
- RBAC routes and guards with token auth
- Admin dashboard with:
  - web user creation (`Moderator`, `BusinessClient`, `Admin`)
  - sponsored challenge creation and publish (admin-only)
  - admin overview metrics
- Moderator dashboard with:
  - AI rejected queue
  - reports queue
  - moderation decisions
- Business dashboard with read-only campaign analytics
- Admin panel entry point
- Public web landing with `.vpk` download button
- FastAPI API with auth + role-protected modules
- MySQL persistence via SQLAlchemy (tables auto-created on startup, demo seed inserted once)
- Backend schema is shared-ready for mobile/web sync (single common MySQL source of truth)

Next:
- Replace in-memory storage with MySQL persistence layer
- Add refresh tokens / password hashing
- Add system settings, notifications, and audit log
