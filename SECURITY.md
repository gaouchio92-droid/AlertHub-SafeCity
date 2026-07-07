# Security Policy

## Secret Handling

Never commit `.env`, real tokens, passwords, private keys, database dumps, or production logs.
The repository tracks only `.env.example` with placeholder values.

Generate strong local values before deployment:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Required production secrets:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `DISCORD_TOKEN`
- `JWT_SECRET`

## Discord Token Rotation

If a Discord token is pasted into chat, logs, screenshots, or Git history, consider it compromised.

Rotate it immediately:

1. Open the Discord Developer Portal.
2. Select the AlertHub application.
3. Go to Bot.
4. Click Reset Token.
5. Update `DISCORD_TOKEN` in `.env`.
6. Restart the stack with `docker compose up -d --force-recreate backend nginx`.

## GitHub Transport

Prefer SSH remotes for this repository:

```bash
git remote set-url origin git@github.com:gaouchio92-droid/AlertHub-SafeCity.git
```

Do not use `http.sslVerify=false`. If HTTPS certificates fail, fix the trusted root certificate or
use SSH with a registered GitHub key.

## Production Checklist

- Set `APP_ENV=production`.
- Replace every placeholder secret.
- Restrict CORS origins to approved domains.
- Terminate TLS at the edge.
- Protect PostgreSQL with backups and restricted network access.
- Store secrets in a managed secret store rather than plain files.
- Rotate tokens after personnel changes or suspected exposure.
