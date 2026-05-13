# Deploy to Timeweb

This backend can be deployed to a Timeweb VPS/Cloud server with Ubuntu and Docker. Timeweb Cloud Apps are also suitable if they support a custom Dockerfile, persistent environment variables, inbound HTTPS, and one-off migration commands.

## 1. Required Timeweb Resources

- Ubuntu VPS or Timeweb Cloud server with public IPv4.
- Timeweb PostgreSQL database.
- Domain or subdomain for the API, for example `api.example.com`.
- SSH access to the server.
- Telegram bot token from BotFather.
- Random secrets for the website webhook and Telegram webhook secret header.
- Public website URL that will send leads to this API.

## 2. Environment

Create `.env` on the server from `.env.example` and fill real values there only. Do not commit `.env`.

Important production variables:

- `DATABASE_URL`: PostgreSQL URL for SQLAlchemy asyncpg. For Timeweb PostgreSQL do not add SSL query parameters to this URL.
- `DB_SSL`: set to `true` for Timeweb PostgreSQL so asyncpg receives SSL through SQLAlchemy `connect_args`.
- `BOT_TOKEN`: Telegram bot token.
- `ADMIN_TELEGRAM_IDS`: comma-separated Telegram user IDs for admins.
- `CRM_WEBHOOK_TOKEN`: secret expected from the website in `X-Webhook-Secret`.
- `TELEGRAM_WEBHOOK_SECRET`: secret passed to Telegram as `secret_token`.
- `PUBLIC_BASE_URL`: public HTTPS API base URL.
- `TELEGRAM_WEBHOOK_PATH`: webhook route, defaults to `/telegram/webhook`.
- `TELEGRAM_WEBHOOK_URL`: full public webhook URL, usually `PUBLIC_BASE_URL + TELEGRAM_WEBHOOK_PATH`.
- `CORS_ORIGINS`: comma-separated allowed website origins.
- `APP_PORT`: app port for VPS/Docker Compose deployments, defaults to `8000`.
- `PORT`: app port injected by platforms such as Timeweb Cloud Apps. If it exists, the Docker start command uses it before `APP_PORT`.

If the database password contains special characters, URL-encode it before putting it into `DATABASE_URL`. Example format for Timeweb PostgreSQL:

```text
DATABASE_URL=postgresql+asyncpg://USER:URL_ENCODED_PASSWORD@HOST:5432/DB_NAME
DB_SSL=true
```

Do not append `?ssl=require`, `sslmode=verify-full`, or `target_session_attrs=...` to `DATABASE_URL` for this FastAPI app. Those psql-style parameters can be interpreted differently by SQLAlchemy/asyncpg and may cause connection errors such as `TargetServerAttributeNotMatched`. The app strips legacy SSL-related query parameters and enables SSL via `DB_SSL=true` for compatibility.

## 3. Docker Deploy

Install Docker on Ubuntu:

```bash
sudo apt update
sudo apt install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"
```

Upload or clone the project:

```bash
sudo mkdir -p /opt/svoydom-crm-bot
sudo chown "$USER":"$USER" /opt/svoydom-crm-bot
cd /opt/svoydom-crm-bot
git clone <repo-url> .
cp .env.example .env
nano .env
```

Build and run migrations:

```bash
docker compose -f docker-compose.prod.example.yml build
docker compose -f docker-compose.prod.example.yml run --rm app alembic upgrade head
```

Start the app:

```bash
docker compose -f docker-compose.prod.example.yml up -d
docker compose -f docker-compose.prod.example.yml ps
docker compose -f docker-compose.prod.example.yml logs -f app
```

Check health:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/health/db
```

Timeweb Cloud Apps may send `HEAD /` as a platform health check even when
you use `/health` for manual checks. The app supports empty 200 responses for
`HEAD /` and `HEAD /health`; keep `/health` for browser or curl verification.

For Timeweb Cloud Apps, use the Dockerfile or this start command so the app binds to the platform-provided port:

```bash
sh -c 'uvicorn app.main:app --host "${APP_HOST:-0.0.0.0}" --port "${PORT:-${APP_PORT:-8000}}"'
```

Do not hard-code `--port 8000` on a platform that injects `PORT`; the container can be marked running while the public proxy checks a different port.

## 4. Python + systemd Alternative

Use this if you do not want Docker:

```bash
sudo apt update
sudo apt install -y python3.12-venv python3-pip git
sudo mkdir -p /opt/svoydom-crm-bot
sudo chown www-data:www-data /opt/svoydom-crm-bot
sudo -u www-data git clone <repo-url> /opt/svoydom-crm-bot
cd /opt/svoydom-crm-bot
sudo -u www-data python3 -m venv .venv
sudo -u www-data ./.venv/bin/pip install -e .
sudo -u www-data cp .env.example .env
sudo -u www-data nano .env
sudo -u www-data ./.venv/bin/alembic upgrade head
```

Install the example service:

```bash
sudo cp svoydom-crm-bot.service.example /etc/systemd/system/svoydom-crm-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now svoydom-crm-bot
sudo systemctl status svoydom-crm-bot
```

## 5. HTTPS Reverse Proxy

Install Nginx and Certbot:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/svoydom-crm-bot`:

```nginx
server {
    server_name api.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable HTTPS:

```bash
sudo ln -s /etc/nginx/sites-available/svoydom-crm-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d api.example.com
```

After HTTPS is active, `PUBLIC_BASE_URL` must be `https://api.example.com`.

## 6. Telegram Webhook

Register the Telegram webhook after the app is reachable over HTTPS:

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://api.example.com/telegram/webhook" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

Check webhook status:

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

## 7. Website Integration

The website should send leads to:

```text
POST https://api.example.com/api/site/leads
X-Webhook-Secret: <CRM_WEBHOOK_TOKEN>
Content-Type: application/json
```

For a Next.js frontend, store the backend URL and webhook token in server-only environment variables, for example `CRM_API_URL` and `CRM_WEBHOOK_TOKEN`. Do not expose the webhook token to browser code. Send lead forms from a Next.js route handler or server action to this backend.

## 8. Release Checklist

1. Fill `.env` on the server with production values.
2. Run `alembic upgrade head`.
3. Start the app and verify `/` and `/health` first, then `/health/db`. On Timeweb Cloud Apps, ensure root `HEAD /` returns 200 for the platform health check.
4. Configure HTTPS for the API domain.
5. Register Telegram webhook with `secret_token`.
6. Send a test lead from the website backend and confirm it appears in Telegram/CRM flow.
