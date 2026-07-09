# AlertHub Safe City Operations

This guide turns the report recommendations into concrete operating procedures.

## PostgreSQL Persistence And Backups

PostgreSQL data is stored in the persistent Docker volume `postgres_data`.

Backups are handled by the `postgres_backup` service. It creates compressed custom-format dumps in
the `postgres_backups` Docker volume.

Configuration:

```env
POSTGRES_BACKUP_INTERVAL_SECONDS=86400
POSTGRES_BACKUP_RETENTION_DAYS=14
```

Inspect backup files:

```bash
docker compose exec postgres_backup ls -lh /backups
```

Restore a backup into an empty database:

```bash
docker compose exec postgres_backup pg_restore \
  -h postgres \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --clean \
  --if-exists \
  /backups/alerthub-YYYYMMDDTHHMMSSZ.dump
```

## Log Rotation

Docker JSON logs are rotated for all long-running services.

Configuration:

```env
DOCKER_LOG_MAX_SIZE=10m
DOCKER_LOG_MAX_FILE=5
```

Inspect logs:

```bash
docker compose logs --tail=200 backend
docker compose logs --tail=200 scheduler
docker compose logs --tail=200 nginx
```

## Scheduled Discord Synchronization

The `scheduler` service runs connector synchronization automatically, so operators do not need to
manually click sync before every report.

Configuration:

```env
SYNC_INTERVAL_SECONDS=300
```

Inspect scheduler activity:

```bash
docker compose logs --tail=100 scheduler
```

## Health Monitoring

The `health_monitor` service checks the public API health endpoint through Nginx:

```text
http://nginx/api/v1/health
```

Configuration:

```env
HEALTHCHECK_INTERVAL_SECONDS=60
```

Inspect failures:

```bash
docker compose logs --tail=100 health_monitor
```

In production, forward these logs to the organization monitoring system and alert when the monitor
prints `healthcheck failed`.

## Alembic Migrations In Deployment

Run migrations as an explicit deployment step before recreating application services:

```bash
docker compose --profile migration run --rm migrations
docker compose up -d --build
```

The `migrations` service uses the same backend image and `DATABASE_URL` as the application.

## Discord Parsing Stabilization

The parser must continue extracting these fields from Discord/Zabbix messages:

- `host`
- `severity`
- `status`
- `problem_name`
- `started_at`
- `resolved_at`
- `links`
- `operational_data`

When a new Discord message format appears, add a parser fixture and a regression test before
deploying the change.

## Open Problem Escalation

The report exposes unresolved problems with age and recommended action. The operational process is:

1. Review unresolved problems daily.
2. Prioritize `High` and `Disaster` severities first.
3. Assign an owner for each open problem.
4. Use the Zabbix link in the report to confirm status.
5. Close the follow-up only after the next sync marks the event as resolved.
