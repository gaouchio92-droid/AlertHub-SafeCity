# Database

PostgreSQL 16 is provisioned by Docker Compose with a persistent `postgres_data` volume.

Sprint 1 does not create application tables. Schema changes should be introduced through Alembic
revision files in `backend/alembic/versions`.
