# SvoyDom CRM Bot Backend

Initial backend for processing website leads from `svoydom-lugansk.ru` through a Telegram CRM bot.

## Stack

- FastAPI for HTTP API and website lead webhook
- aiogram 3 for Telegram bot interactions
- PostgreSQL with SQLAlchemy 2 async ORM
- Alembic migrations
- OpenPyXL Excel export

## Local Start

```powershell
cd E:\проект\svoydom-crm-bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
Copy-Item .env.example .env
docker compose up -d postgres
alembic upgrade head
uvicorn app.main:app --reload
```

## Production Deploy

See [DEPLOY.md](DEPLOY.md) for Timeweb VPS/Cloud deployment with Docker, PostgreSQL SSL connection settings, Nginx HTTPS, migrations, and Telegram webhook registration.

The website lead endpoint is `POST /api/site/leads`. Pass `X-Webhook-Secret` with the value from `.env`.

Telegram webhook path defaults to `POST /telegram/webhook`. In production, point Telegram webhook to `PUBLIC_BASE_URL + TELEGRAM_WEBHOOK_PATH`.

## Important Notes

- `.env.example` contains placeholders only. Do not commit real tokens or passwords.
- Managers are users with role `manager`; they can be disabled from receiving new leads.
- Admins see all leads; managers should only query and act on leads assigned to them.
- `quiz_answers` is a JSON field and can store arbitrary website questionnaire answers.
- Reminder and reassignment logic is provided as service/task code and should be run by a worker or app lifespan task in production.

## Next Data Needed

- Telegram bot token from BotFather
- Telegram IDs of initial admins
- Production PostgreSQL credentials
- Public HTTPS backend URL for Telegram webhook and website integration
- Exact website payload fields and desired Excel columns/filters
