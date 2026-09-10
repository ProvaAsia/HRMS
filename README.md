# HRMS — Human Resource Management System

Django 4.2 + Tailwind CSS + Supabase (PostgreSQL)

## Modules

| Module | HR / Admin | Employee |
|--------|-----------|----------|
| Recruitment | Job positions, candidates, interviews | — |
| Training | Programs, enrollments | My enrollments |
| Appraisals | Cycles, all appraisals | Self-review, goals |
| Leave | Approve/reject, balances | Request, history |
| Overtime | Approve/reject, reports | Request, history |
| Attendance | Daily records, reports | Clock-in/out, my report |

## Roles

| Role | Access |
|------|--------|
| `super_admin` | Full access + user management |
| `hr_manager` | All modules, no user management |
| `employee` | Self-service only |

---

## Local Development

```bash
# 1. Clone and set up environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Run migrations
python manage.py migrate

# 4. Create a superuser
python manage.py createsuperuser

# 5. Start the dev server
python manage.py runserver
```

---

## Deploy to Railway + Supabase

### 1. Create a Supabase project
- Go to [supabase.com](https://supabase.com) → New project
- Copy the **Connection string** (URI format) from Settings → Database

### 2. Generate a Django secret key
```bash
python -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters+string.digits+'!@#$%^&*') for _ in range(60)))"
```

### 3. Deploy to Railway
- Go to [railway.app](https://railway.app) → New project → Deploy from GitHub repo
- Add environment variables in Railway dashboard:

```
SECRET_KEY=<generated above>
DEBUG=False
ALLOWED_HOSTS=<your-app>.railway.app
DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT-REF.supabase.co:5432/postgres
```

Railway auto-runs `python manage.py migrate --noinput` on every deploy (via `Procfile` release command), then starts Gunicorn.

### 4. Create the first super admin
After first deploy, open a Railway shell or run locally against the Supabase DB:
```bash
DATABASE_URL=<supabase-url> python manage.py createsuperuser
```

---

## Project Structure

```
hrms/
├── accounts/       # Custom User model, login, user management
├── recruitment/    # Job positions & candidates
├── training/       # Training programs & enrollments
├── appraisals/     # Performance cycles & appraisals
├── leave/          # Leave requests & balances
├── overtime/       # OT requests
├── attendance/     # Clock-in/out & attendance records
├── templates/      # Shared base template + per-app templates
├── static/         # CSS / JS assets
├── hrms/           # Django settings, URLs, WSGI
├── Procfile        # Railway/Heroku process config
├── railway.json    # Railway deployment config
├── runtime.txt     # Python version pin
└── requirements.txt
```
