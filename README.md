# fastapi-best-architecture

For a project like **Video Streaming Platform**, I would not use the typical FastAPI tutorial structure:

```text
app/
├── routers/
├── models/
├── schemas/
├── services/
```

It becomes painful once you have:

* Authentication
* Movies
* Streaming
* Payments
* Ads
* Analytics
* Notifications
* Admin

Instead, I recommend a **modular monolith** architecture.

---

# High-Level Structure

```text
backend/

├── app/
│
├── core/
├── modules/
├── shared/
├── integrations/
│
├── models/
│
├── tests/
├── scripts/
├── migrations/
│
├── docker/
├── requirements/
│
├── main.py
└── pyproject.toml
```

---

# Complete Structure

```text
backend/

├── app/
├── main.py
├── core/
│   ├── config.py
│   ├── security.py
│   ├── database.py
│   ├── dependencies.py
│   ├── cache.py
│   ├── logging.py
│   ├── exceptions.py
│   ├── middleware.py
│   ├── session.py
│   └── lifespan.py
│
├── models/
│   ├── user.py
│
├── routes/
│   ├── api.py
│   ├── v1/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── movie.py
│   │   ├── admin.py
│
├── modules/
│
│   ├── auth/
│   │   ├── api/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── schemas/
│   │
│   ├── users/
│   │
│   ├── movies/
│   │
│   ├── streaming/
│   │
│   ├── payments/
│   │
│   ├── advertisements/
│   │
│   ├── analytics/
│   │
│   ├── notifications/
│   │
│   ├── watchlists/
│   │
│   ├── reviews/
│   │
│   └── admin/
│
├── shared/
│   ├── schemas/
│   ├── enums/
│   ├── constants/
│   ├── permissions/
│   ├── responses/
│   └── events/
│
├── storage/
│   ├── uploads/
│
├── jobs/
│   ├── queue/
│
├── integrations/
│   ├── email/
│   ├── sms/
│   ├── payments/
│   └── monitoring/
│
├── tests/
│
├── scripts/
│
├── migrations/
│   ├── seeders/
│   ├── versions/
│   ├── env.py
│   ├── docker-entrypoint.sh
│   ├── alembic.ini
│
├── requirements.txt
└── pyproject.toml
```

---

# Module Structure

Example:

```text
modules/movies/

├── api/
│   ├── create_movie.py
│   ├── update_movie.py
│   ├── get_movie.py
│   └── list_movies.py
│
├── services/
│   ├── movie_service.py
│   └── pricing_service.py
│
├── repositories/
│   └── movie_repository.py
│
├── schemas/
│   ├── requests.py
│   └── responses.py
│
├── models/
│   └── movie.py
│
├── dependencies/
│   └── permissions.py
│
├── routes.py
└── constants.py
```

Everything related to movies stays together.

---

# Database Models

Keep models inside their domains:

```text
modules/

├── users/models/
├── movies/models/
├── payments/models/
├── ads/models/
```

Avoid:

```text
models/

├── user.py
├── movie.py
├── payment.py
├── ad.py
```

because eventually you'll have dozens of models.

---

# Infrastructure Layer

This is where external services live.

Example:

```text
infrastructure/storage/

├── s3.py
├── cloudflare_r2.py
└── local.py
```

Then:

```python
storage.upload(...)
```

instead of:

```python
boto3.client(...)
```

scattered across the project.

---

# Payment Providers

Very important for Video Streaming Platform.

```text
infrastructure/payments/

├── base.py
├── stripe.py
├── paystack.py
├── flutterwave.py
├── apple.py
└── google.py
```

Then:

```python
provider.charge(...)
provider.verify(...)
provider.refund(...)
```

The application never cares which provider is used.

---

# Streaming Module

This will become one of the biggest domains.

```text
modules/streaming/

├── api/
├── services/
├── repositories/
├── schemas/
├── models/
│
├── drm/
│
├── tokens/
│
├── manifests/
│
└── hls/
```

Responsibilities:

* Playback authorization
* Signed URLs
* Stream sessions
* Viewing limits
* Device restrictions
* DRM integration later

---

# Advertisement Module

```text
modules/advertisements/

├── campaigns/
├── targeting/
├── impressions/
├── clicks/
├── billing/
└── reporting/
```

Because ads often become almost a separate product.

---

# Analytics Module

```text
modules/analytics/

├── events/
├── reporting/
├── aggregation/
└── dashboards/
```

Track:

```text
Play
Pause
Seek
Watch Time
Completion
Ad Impressions
Revenue
```

from day one.

---

# Background Jobs

```text
infrastructure/queue/

├── celery_app.py
├── tasks/
│
├── video_processing.py
├── email_tasks.py
├── analytics_tasks.py
└── cleanup_tasks.py
```

Examples:

```text
Video transcoding
Thumbnail generation
Email sending
Analytics aggregation
```

---

# API Versioning

Start immediately.

```text
api/v1/
```

Example:

```python
/api/v1/auth/login
/api/v1/movies
/api/v1/payments
```

You'll thank yourself later.

---

# Config Structure

```text
core/

├── config.py
├── security.py
├── database.py
├── cache.py
└── logging.py
```

Never put everything inside:

```python
settings.py
```

once the project grows.

---

# What I Would Actually Use

For Video Streaming Platform:

```text
FastAPI
SQLAlchemy 2
Alembic

PostgreSQL

Redis

Celery

Cloudflare R2

FFmpeg

Pydantic v2

JWT

Prometheus

Grafana

Sentry
```

And the root structure would be:

```text
app/
├── core/
├── modules/
├── shared/
├── infrastructure/
└── main.py
```

This is a scalable modular-monolith architecture. It is significantly easier to maintain than a microservice architecture, while still being organized enough that domains like Movies, Streaming, Payments, and Advertisements can eventually be extracted into separate services if the platform grows very large.
