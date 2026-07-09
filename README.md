# AlertHub Safe City

AlertHub Safe City is an independent monitoring analytics platform. Sprint 1 provides production-grade infrastructure only: FastAPI, React, PostgreSQL, Nginx, Docker Compose, Alembic, settings, logging, health checks, modular connectors, and documentation.

Discord remains the default source. Zabbix API and Zabbix Database integrations are optional connector modules and disabled by default. Reports, analytics, authentication, and domain business logic are intentionally not implemented in this sprint.

## Architecture

- Backend: Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic Settings, Uvicorn
- Frontend: React, Vite, TypeScript, TailwindCSS, React Router, Axios
- Database: PostgreSQL 16
- Proxy: Nginx
- Runtime: Docker and Docker Compose

See [docs/architecture.md](docs/architecture.md) for the system layout.
See [docs/operations.md](docs/operations.md) for backups, scheduled sync, log rotation, health
monitoring, migrations, and escalation procedures.

## Installation

Create an environment file:

```powershell
Copy-Item .env.example .env
```

Update secrets in `.env` before running outside local development. If you already started the
database with the default Compose values, keep `POSTGRES_PASSWORD=alerthub_password` unless you
also recreate the PostgreSQL volume.

## Docker

Start the full stack:

```bash
docker compose up --build
```

Run database migrations before deployment:

```bash
docker compose --profile migration run --rm migrations
```

Open the application:

- Frontend: http://localhost
- API health: http://localhost/api/v1/health
- Connector status: http://localhost/connectors
- Swagger: http://localhost/docs

Stop services:

```bash
docker compose down
```

Operational background services included in Compose:

- `scheduler`: synchronizes enabled connectors on `SYNC_INTERVAL_SECONDS`.
- `postgres_backup`: writes PostgreSQL dumps to the `postgres_backups` volume.
- `health_monitor`: checks `/api/v1/health` through Nginx.
- Docker log rotation is enabled through `DOCKER_LOG_MAX_SIZE` and `DOCKER_LOG_MAX_FILE`.

Remove the PostgreSQL volume when you intentionally want a clean database:

```bash
docker compose down -v
```

## Development

Backend local setup:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Frontend local setup:

```bash
cd frontend
npm install
npm run dev
```

Run backend quality checks:

```bash
cd backend
ruff check .
mypy app
```

Run frontend quality checks:

```bash
cd frontend
npm run lint
npm run build
```

## Database

Alembic is configured but no application tables are created in Sprint 1.

Create a future migration:

```bash
cd backend
alembic revision --autogenerate -m "describe change"
```

Apply migrations:

```bash
cd backend
alembic upgrade head
```

## Connectors

AlertHub Safe City uses a modular connector architecture. Discord is the default event source.
Zabbix API and Zabbix Database connectors are optional and disabled by default.

Configure connector selection with environment variables:

```env
EVENT_SOURCE=discord
CONNECTOR_IMPORTS=
ENABLE_DISCORD=true
ENABLE_ZABBIX_API=false
ENABLE_ZABBIX_DB=false
DISCORD_TOKEN=your-discord-bot-token
DISCORD_CHANNEL_ID=your-discord-channel-id
```

Supported `EVENT_SOURCE` values are `discord`, `zabbix_api`, `zabbix_database`, and `multiple`.
When `multiple` is selected, every enabled connector starts concurrently.

Future connectors can be registered with `CONNECTOR_IMPORTS` as a comma-separated list of connector
classes that subclass `BaseConnector`, for example `my_package.connectors.RestApiConnector`.

Check connector status:

```bash
curl http://localhost/connectors
```

Apply local `.env` changes on Windows:

```powershell
.\scripts\apply-env.ps1
```

The script recreates the backend and Nginx containers, then prints connector diagnostics. Discord
is ready only when `DISCORD_TOKEN` and `DISCORD_CHANNEL_ID` are configured.

## Production

For production deployments:

- Replace all default secrets.
- Set `APP_ENV=production`; the backend refuses placeholder or missing production secrets.
- Use managed secret storage.
- Restrict CORS origins to approved domains.
- Publish images through a trusted container registry.
- Terminate TLS at the load balancer or Nginx edge.
- Configure backup and retention policies for PostgreSQL.
- Ship logs and metrics to the organization observability platform.

See [SECURITY.md](SECURITY.md) for token rotation, GitHub SSH, and secret-handling guidance.

## Project Structure

```text
backend/
frontend/
database/
nginx/
docs/
docker-compose.yml
.env.example
README.md
.gitignore
```
