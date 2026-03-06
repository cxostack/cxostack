# CTO Review & Task List
# Platform: Interview Prep / Job Landing Platform
# Goal: Ready for 1k users, burst-capable, scalable to 10k without major rework

---

## CURRENT STATE AUDIT

### What's Built (Confirmed)
- Flask monolith + PostgreSQL + Docker Compose
- Auth (JWT), Users, Roles/Levels
- Topics, Categories, Subcategories, Articles
- Interviews, Interview Rounds, Q&A logging
- Resumes (file storage on local disk /app/uploads)
- Progress tracking, Notes, Reviews (spaced repetition)
- Google Calendar OAuth integration
- AI Gateway (Groq + Anthropic providers)
- AI routes: topic explain, interview analysis, resume scoring (basic)
- Rate limiter, cost tracker, safety filter, queue manager
- Cache layer (memory_cache.py + redis_cache.py - but Redis not wired in docker-compose)
- Admin routes
- Subscription model (free/basic/premium tiers)
- pgAdmin for DB management

### What's Partially Built
- Redis cache (code exists, not running as service)
- Resume analysis (working but schema issue - content_hash on wrong table)
- AI services split into providers/ but ai_services_combined.py still referenced
- config/ directory conflict with config.py (discussed, not resolved)

### What's Missing / Broken
- Redis not in docker-compose as service
- S3 not implemented (resumes on local disk = will break at scale)
- config.py vs config/ directory conflict (import issues)
- No connection pooling for PostgreSQL
- No health checks on services
- No graceful shutdown
- Resumes table missing: content_hash, last_analyzed_at, latest_ats_score
- No metadata column on topics/articles/users (future-proofing)
- No feature flags system
- Gunicorn workers not optimized for async AI calls
- No DB migration tool (manual SQL = risky at scale)

### Architecture Risk Assessment
| Risk | Severity | Current State |
|------|----------|---------------|
| Resumes on local disk | 🔴 CRITICAL | Breaks with multiple containers/replicas |
| No Redis (cache in memory) | 🔴 CRITICAL | Cache lost on restart, not shared across workers |
| Single PostgreSQL connection pool | 🟡 HIGH | Will bottleneck at 100+ concurrent users |
| No health checks | 🟡 HIGH | Docker won't know if app is actually healthy |
| Manual SQL migrations | 🟡 HIGH | Easy to miss, hard to rollback |
| config.py vs config/ conflict | 🟡 HIGH | Import errors already happening |
| No feature flags | 🟠 MEDIUM | Can't safely deploy partial features |
| Gunicorn sync workers | 🟠 MEDIUM | AI calls block workers |

---

## ARCHITECTURE DECISION: POLYGLOT PERSISTENCE

### What Goes Where (Final Decision)

```
PostgreSQL (Primary - Core Business Data)
├── users, auth, subscriptions
├── topics, categories, articles (metadata only)
├── interviews, resumes (metadata only)
├── progress, notes, study_plans
└── ai_usage_logs → move to TimescaleDB later (Phase 2)

Redis (Cache + Sessions + Rate Limiting)
├── JWT session cache
├── AI response cache (topic explanations, resume scores)
├── Rate limit counters (per user, per feature)
├── Hot data (user profile, current path)
└── Real-time: active users, queue state

S3-Compatible (File Storage)
├── Resumes (PDF, DOCX)
├── Interview attachments
├── AI-generated content snapshots
└── Profile photos (future)

[Phase 2 - when 1k+ users]
Elasticsearch  → Content search, article discovery
TimescaleDB    → AI usage analytics, cost tracking
Neo4j          → Skill prerequisite graph, learning paths
```

### Docker Services (Target)
```yaml
services:
  backend:      Flask app (4 gunicorn workers, async)
  db:           PostgreSQL 15 (primary data)
  redis:        Redis 7 (cache, sessions, rate limiting)
  nginx:        Reverse proxy + static files
  pgadmin:      Already done ✅

[Phase 2 additions - separate compose profile]
  elasticsearch:  Content search
  timescaledb:    Analytics
```

---

## TASK LIST (PRIORITY ORDER)

---

### 🔴 P0 - CRITICAL FIXES (Do First - Nothing Else Works Without These)

---

#### TASK-001: Fix config.py vs config/ Directory Conflict
**Why P0:** Causing import errors right now. Blocks everything else.
**What:**
- Rename `backend/config.py` → `backend/config/app_config.py`
- Update `backend/config/__init__.py` to export both `Config` and `AI_CONFIG`
- Update all imports in `app.py` and any route files
- Delete old `config.py`

**Files to change:**
```
backend/config.py           → DELETE
backend/config/__init__.py  → UPDATE (export Config + AI_CONFIG)
backend/config/app_config.py → CREATE (move content from config.py)
backend/app.py              → UPDATE import
```

**Acceptance:** `docker compose up` starts without ImportError

---

#### TASK-002: Redis as Proper Docker Service
**Why P0:** Cache currently in-memory = lost on restart, not shared between Gunicorn workers. Rate limiting broken with multiple workers.
**What:**
- Add Redis service to docker-compose.yml with proper config
- Add Redis health check
- Add Redis data persistence volume
- Wire REDIS_URL env var to backend
- Switch AI gateway cache from memory → Redis
- Move rate limiter from in-memory dict → Redis

**docker-compose.yml additions:**
```yaml
redis:
  image: redis:7-alpine
  container_name: interview-prep-redis
  restart: unless-stopped
  command: >
    redis-server
    --maxmemory 256mb
    --maxmemory-policy allkeys-lru
    --appendonly yes
    --appendfsync everysec
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  networks:
    - app-network
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 3
```

**backend service env additions:**
```yaml
environment:
  REDIS_URL: redis://redis:6379/0
  CACHE_PROVIDER: redis
  SESSION_REDIS_URL: redis://redis:6379/1   # Separate DB for sessions
  RATE_LIMIT_REDIS_URL: redis://redis:6379/2 # Separate DB for rate limits
```

**Acceptance:** Redis running, AI cache persists across backend restarts, rate limits work across all Gunicorn workers

---

#### TASK-003: Fix Resume Storage - Move to S3-Compatible Storage
**Why P0:** Files on `/app/uploads` = lost when container restarts, breaks with multiple replicas, expensive on disk.
**What:**
- Add MinIO service to docker-compose (S3-compatible, self-hosted)
- Create `backend/services/storage/` with S3 client abstraction
- Migrate existing resume upload route to use S3
- Keep same API surface (no frontend changes needed)
- Migration script for existing files

**docker-compose.yml additions:**
```yaml
minio:
  image: minio/minio:latest
  container_name: interview-prep-minio
  restart: unless-stopped
  command: server /data --console-address ":9001"
  ports:
    - "9000:9000"   # S3 API
    - "9001:9001"   # MinIO Console UI
  environment:
    MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
    MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin123}
  volumes:
    - minio_data:/data
  networks:
    - app-network
  healthcheck:
    test: ["CMD", "mc", "ready", "local"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Why MinIO not real S3:**
- Development: MinIO (free, local, S3-compatible)
- Production: Swap `S3_ENDPOINT_URL` env var to real AWS S3
- Zero code changes needed when switching to production

**New service: `backend/services/storage/s3_client.py`**
```python
class StorageClient:
    def upload_file(self, file_data, bucket, key) -> str
    def download_file(self, bucket, key) -> bytes
    def delete_file(self, bucket, key) -> bool
    def get_presigned_url(self, bucket, key, expiry=3600) -> str
```

**Resume model changes:**
```sql
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS s3_bucket VARCHAR(100);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS s3_key VARCHAR(500);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS last_analyzed_at TIMESTAMP;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS latest_ats_score INTEGER;
-- file_path kept for backward compat during migration
```

**Acceptance:** Upload resume → stored in MinIO → download works → restart container → file still there

---

#### TASK-004: Fix Broken Resume Analysis Schema
**Why P0:** Currently throwing 500 errors (content_hash on wrong table).
**What:**
- Run migration to add missing columns to `resumes` table
- Remove wrong columns from `resume_analyses` model if they were added
- Verify endpoint works end-to-end

**Migration:**
```sql
-- 003_fix_resume_analysis.sql
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS last_analyzed_at TIMESTAMP;
ALTER TABLE resumes ADD COLUMN IF NOT EXISTS latest_ats_score INTEGER;

-- Resume analyses should NOT have these columns
-- They live on resumes table
```

**Acceptance:** `POST /api/v2/ai/resume/<id>/analyze` returns 200 with analysis data

---

### 🟡 P1 - HIGH PRIORITY (Do After P0 - Core Platform Stability)

---

#### TASK-005: PostgreSQL Connection Pooling + Optimization
**Why P1:** Default SQLAlchemy config will bottleneck at 50+ concurrent users.
**What:**
- Configure connection pool in `app_config.py`
- Add PgBouncer as connection pooler (optional but recommended for 1k users)
- Add proper indexes for common query patterns
- Enable query logging for slow query detection

**Config changes:**
```python
# backend/config/app_config.py
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,          # Base connections
    'max_overflow': 20,       # Extra connections under load
    'pool_pre_ping': True,    # Verify connection before use
    'pool_recycle': 3600,     # Recycle connections every hour
    'connect_args': {
        'connect_timeout': 10,
        'application_name': 'interview_prep_backend'
    }
}
```

**Missing indexes to add:**
```sql
-- 004_add_missing_indexes.sql
CREATE INDEX IF NOT EXISTS idx_topics_category ON topics(category_id);
CREATE INDEX IF NOT EXISTS idx_progress_user_topic ON progress(user_id, topic_id);
CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic_id);
CREATE INDEX IF NOT EXISTS idx_interviews_user ON interviews(user_id);
CREATE INDEX IF NOT EXISTS idx_notes_user_topic ON notes(user_id, topic_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_user ON study_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_user_date ON ai_usage_logs(user_id, created_at DESC);
```

**Acceptance:** No connection timeout errors under 50 concurrent users

---

#### TASK-006: Proper Health Checks + Graceful Shutdown
**Why P1:** Docker doesn't know if app is truly healthy. Critical for any load balancer or scaling.
**What:**
- Improve `/health` endpoint to check all dependencies
- Add graceful shutdown handling
- Update all service health checks in docker-compose

**Health endpoint:**
```python
@app.route('/health')
def health():
    checks = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'database': check_db(),      # Can we query?
            'redis': check_redis(),       # Can we ping?
            'storage': check_storage(),   # Can we list bucket?
        }
    }
    status_code = 200 if all(
        v == 'ok' for v in checks['services'].values()
    ) else 503
    return jsonify(checks), status_code
```

**docker-compose health checks:**
```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
    interval: 30s
    timeout: 10s
    start_period: 40s
    retries: 3

db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Acceptance:** `docker compose ps` shows all services healthy. Restart one service, others wait and recover.

---

#### TASK-007: Metadata Column - Future-Proof Schema
**Why P1:** Prevents the "every feature needs ALTER TABLE" problem. One-time change now saves 20 migrations later.
**What:**
- Add `metadata JSONB` to topics, articles, users tables
- Add GIN indexes for fast JSONB queries
- Update models to use metadata pattern
- Populate initial skill_type data for existing topics

**Migration:**
```sql
-- 005_add_metadata_columns.sql
ALTER TABLE topics ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE articles ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_metadata JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_topics_metadata ON topics USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_articles_metadata ON articles USING GIN (metadata);
CREATE INDEX IF NOT EXISTS idx_users_profile_metadata ON users USING GIN (profile_metadata);

-- Populate initial skill_type for existing topics
UPDATE topics SET metadata = jsonb_set(
    COALESCE(metadata, '{}'),
    '{skill_type}',
    CASE
        WHEN id ILIKE '%two-pointer%' OR id ILIKE '%sliding-window%'
          OR id ILIKE '%prefix-sum%' OR id ILIKE '%dynamic-programming%'
          OR id ILIKE '%binary-search%'
        THEN '"coding_pattern"'
        WHEN name ILIKE '%system design%' OR name ILIKE '%distributed%'
          OR name ILIKE '%cap theorem%' OR name ILIKE '%consistency%'
        THEN '"system_design"'
        WHEN name ILIKE '%leadership%' OR name ILIKE '%communication%'
          OR name ILIKE '%teamwork%'
        THEN '"behavioral"'
        ELSE '"technical_skill"'
    END
);
```

**Acceptance:** `SELECT metadata FROM topics LIMIT 1` returns `{"skill_type": "technical_skill"}`. No more ALTER TABLE for feature additions.

---

#### TASK-008: Feature Flags System
**Why P1:** Ability to deploy new features without them being active. Critical for safe releases.
**What:**
- Create `backend/config/features.py`
- Add feature check decorator
- Wire to environment variables

```python
# backend/config/features.py
FEATURES = {
    # Core (always on)
    'auth': True,
    'topics': True,
    'interviews': True,
    'resumes': True,
    'ai_basic': True,

    # Togglable via env
    'redis_cache': os.getenv('FEATURE_REDIS_CACHE', 'true') == 'true',
    's3_storage': os.getenv('FEATURE_S3_STORAGE', 'true') == 'true',
    'resume_analysis': os.getenv('FEATURE_RESUME_ANALYSIS', 'true') == 'true',
    'mock_interviews': os.getenv('FEATURE_MOCK_INTERVIEWS', 'false') == 'true',
    'jd_analyzer': os.getenv('FEATURE_JD_ANALYZER', 'false') == 'true',
    'learning_paths': os.getenv('FEATURE_LEARNING_PATHS', 'false') == 'true',
    'skill_assessment': os.getenv('FEATURE_SKILL_ASSESSMENT', 'false') == 'true',
}

def feature_required(feature_name):
    """Decorator: returns 404 if feature disabled"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not FEATURES.get(feature_name, False):
                return jsonify({'error': f'Feature not available: {feature_name}'}), 404
            return f(*args, **kwargs)
        return decorated
    return decorator
```

**Acceptance:** Set `FEATURE_MOCK_INTERVIEWS=false`, endpoint returns 404. Set to `true`, works normally.

---

#### TASK-009: Gunicorn Optimization for AI Workloads
**Why P1:** AI calls are slow (2-30 seconds). Sync workers block during AI calls = no capacity for other users.
**What:**
- Switch to `gevent` or `gthread` workers
- Tune worker count and timeout
- Add proper logging

**Dockerfile CMD change:**
```dockerfile
# Current (blocks on AI calls)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]

# Better (async, handles AI calls without blocking)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--worker-class", "gevent", \
     "--worker-connections", "100", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload-app", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:app"]
```

**requirements.txt additions:**
```
gevent==24.2.1
gunicorn[gevent]==21.2.0
```

**Acceptance:** 10 concurrent AI requests don't time out. Normal requests still fast during AI processing.

---

### 🟠 P2 - IMPORTANT (Do After P1 - Core Feature Completion)

---

#### TASK-010: Nginx as Reverse Proxy
**Why P2:** Currently exposing Gunicorn directly. Need Nginx for static files, SSL, rate limiting, connection handling.
**What:**
- Add Nginx service to docker-compose
- Configure proxy to Flask backend
- Serve frontend static files from Nginx (not Flask)
- Configure basic rate limiting at Nginx level

**docker-compose addition:**
```yaml
nginx:
  image: nginx:alpine
  container_name: interview-prep-nginx
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./frontend:/usr/share/nginx/html:ro
    - nginx_logs:/var/log/nginx
  depends_on:
    - backend
  networks:
    - app-network
```

**nginx.conf key settings:**
```nginx
upstream backend {
    server backend:5000;
    keepalive 32;
}

server {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=ai_api:10m rate=1r/s;

    # AI endpoints - stricter rate limit
    location /api/v2/ai/ {
        limit_req zone=ai_api burst=5 nodelay;
        proxy_pass http://backend;
        proxy_read_timeout 120s;  # AI calls can be slow
    }

    # Regular API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend;
    }

    # Static files - serve directly (fast)
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
        expires 1h;
    }
}
```

**Acceptance:** Frontend served by Nginx. API proxied to Flask. `/api/v2/ai/` rate limited at Nginx level.

---

#### TASK-011: Database Migration Tool (Alembic)
**Why P2:** Manual SQL migrations are risky. Need version tracking, rollback support.
**What:**
- Add Alembic to project
- Convert existing manual migrations to Alembic
- Add migration commands to docker-compose

```bash
# Add to requirements.txt
alembic==1.13.0

# Initialize
alembic init backend/alembic

# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "add metadata columns"

# Rollback
docker compose exec backend alembic downgrade -1
```

**Acceptance:** `alembic history` shows all migrations. `alembic upgrade head` idempotent. `alembic downgrade -1` works.

---

#### TASK-012: Fix AI Provider Proxies Error (Groq)
**Why P2:** `Client.__init__() got unexpected keyword argument 'proxies'` - AI calls failing.
**What:**
- Update Groq SDK version or fix initialization
- Review all provider __init__ methods
- Remove any proxy-related kwargs

```python
# backend/services/providers/groq_provider.py
from groq import Groq

class GroqProvider:
    def __init__(self, api_key: str):
        # Simple init - no extra kwargs
        self.client = Groq(api_key=api_key)
```

**Acceptance:** `POST /api/v2/ai/topic/<id>/explain` returns AI response without proxy error.

---

#### TASK-013: Session Management via Redis
**Why P2:** Move JWT session caching to Redis for shared state across workers.
**What:**
- Store user session data in Redis on login
- Cache user profile in Redis (5 min TTL)
- Invalidate cache on profile update
- Reduces DB hits by ~60%

```python
# backend/services/session_manager.py
class SessionManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.prefix = "session:"
        self.ttl = 86400  # 24 hours

    def cache_user(self, user_id: int, user_data: dict):
        key = f"{self.prefix}{user_id}"
        self.redis.setex(key, self.ttl, json.dumps(user_data))

    def get_cached_user(self, user_id: int) -> dict | None:
        key = f"{self.prefix}{user_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def invalidate_user(self, user_id: int):
        self.redis.delete(f"{self.prefix}{user_id}")
```

**Acceptance:** After login, subsequent requests don't hit DB for user lookup. Profile update invalidates cache.

---

### 🟢 P3 - NICE TO HAVE (Post-Stability - New Features)

---

#### TASK-014: Rate Limiter Migration to Redis
**Why P3:** Current rate limiter is in-memory = doesn't work across Gunicorn workers.
**What:**
- Rewrite `backend/services/rate_limiter.py` to use Redis
- Use Redis atomic operations (INCR + EXPIRE) for accurate counting
- Support per-user, per-feature limits

```python
class RedisRateLimiter:
    def check_rate_limit(self, user_id, feature, limits):
        # Atomic increment in Redis
        hourly_key = f"rate:{user_id}:{feature}:hourly:{current_hour}"
        daily_key = f"rate:{user_id}:{feature}:daily:{today}"

        pipe = self.redis.pipeline()
        pipe.incr(hourly_key)
        pipe.expire(hourly_key, 3600)
        pipe.incr(daily_key)
        pipe.expire(daily_key, 86400)
        hourly_count, _, daily_count, _ = pipe.execute()

        if hourly_count > limits['per_hour']:
            return False, f"Hourly limit reached ({limits['per_hour']}/hour)"
        if daily_count > limits['per_day']:
            return False, f"Daily limit reached ({limits['per_day']}/day)"
        return True, None
```

**Acceptance:** Rate limits accurate across all Gunicorn workers. Limits reset correctly on hour/day boundary.

---

#### TASK-015: AI Cost Tracking Dashboard (Admin)
**Why P3:** You need to monitor costs before they surprise you.
**What:**
- Add admin endpoint for cost analytics
- Group by: user, feature, model, date
- Alert threshold (daily cost > $X)

```python
@admin_bp.route('/ai/costs', methods=['GET'])
def ai_cost_dashboard():
    return {
        'today': get_daily_cost(today),
        'this_week': get_weekly_cost(),
        'by_feature': get_cost_by_feature(),
        'by_user': get_top_users_by_cost(limit=10),
        'by_model': get_cost_by_model(),
        'cache_hit_rate': get_cache_hit_rate()
    }
```

**Acceptance:** Admin can see real-time AI spend. Alert fires when daily cost > threshold.

---

#### TASK-016: Topic Metadata Population (AI-Powered)
**Why P3:** Enables smarter recommendations, fixes "prefix sum for Platform Engineers" problem.
**What:**
- Admin script: Run AI on all topics to populate metadata
- Categorize: skill_type, depth_level, role_relevance scores
- One-time cost: ~$10-15 for 200 topics

```python
# backend/migrations/populate_topic_metadata.py

async def populate_all_topics():
    topics = Topic.query.filter(
        Topic.metadata == '{}'
    ).all()

    for topic in topics:
        prompt = f"""Categorize this technical topic:
        Name: {topic.name}
        Brief: {topic.brief}

        Return JSON:
        {{
            "skill_type": "technical_skill|coding_pattern|system_design|behavioral",
            "depth_levels": {{
                "awareness": "estimated hours to reach",
                "application": "estimated hours",
                "mastery": "estimated hours"
            }},
            "role_relevance": {{
                "platform-engineer": {{"junior": 0-10, "mid": 0-10, "senior": 0-10}},
                "backend-engineer": {{"junior": 0-10, "mid": 0-10, "senior": 0-10}},
                "devops-engineer": {{"junior": 0-10, "mid": 0-10, "senior": 0-10}}
            }}
        }}
        """

        result = await ai.generate(prompt, model='groq/llama-3.1-70b-versatile')
        topic.metadata = {**topic.metadata, **result}
        db.session.commit()
```

**Acceptance:** All topics have `skill_type` populated. Resume analysis no longer suggests "prefix sum" for Platform Engineers.

---

#### TASK-017: Article Enhancement Pipeline
**Why P3:** Makes article recommendations intelligent.
**What:**
- Admin can trigger "Enhance Article" on any article
- AI generates: summary, key_takeaways, best_for_levels, estimated_read_time
- Stored in `articles.metadata`

**Acceptance:** Articles have AI-generated summaries. Recommendations include "Why this is recommended for you."

---

#### TASK-018: User Onboarding Flow (Skill Assessment)
**Why P3:** Tool currently knows nothing about the user. Enables personalized paths.
**What:**
- On first login after signup, redirect to onboarding
- Wizard: Target role → Current skills (checkbox) → Learning style → Timeline
- Store in `users.profile_metadata`
- Generate initial study plan based on gaps

**Acceptance:** New user completes onboarding in <5 min. Study plan generated automatically based on responses.

---

## DOCKER-COMPOSE TARGET STATE

```yaml
version: '3.8'

services:
  # ==========================================
  # CORE APPLICATION
  # ==========================================
  backend:
    build:
      context: ./backend
      target: production
    container_name: interview-prep-backend
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      # App
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      FLASK_ENV: ${FLASK_ENV:-production}
      # Database
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      # Redis
      REDIS_URL: redis://redis:6379/0
      CACHE_PROVIDER: redis
      # Storage (MinIO/S3)
      S3_ENDPOINT_URL: http://minio:9000
      S3_ACCESS_KEY: ${MINIO_ROOT_USER}
      S3_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      S3_BUCKET_RESUMES: resumes
      S3_BUCKET_CONTENT: content
      # AI Keys
      GROQ_API_KEY: ${GROQ_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      # Feature Flags
      FEATURE_REDIS_CACHE: "true"
      FEATURE_S3_STORAGE: "true"
      FEATURE_RESUME_ANALYSIS: "true"
      FEATURE_MOCK_INTERVIEWS: "false"
      FEATURE_JD_ANALYZER: "false"
    volumes:
      - app_logs:/app/logs
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      start_period: 40s
      retries: 3

  # ==========================================
  # NGINX (Reverse Proxy + Static Files)
  # ==========================================
  nginx:
    image: nginx:alpine
    container_name: interview-prep-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontend:/usr/share/nginx/html:ro
    depends_on:
      - backend
    networks:
      - app-network

  # ==========================================
  # PRIMARY DATABASE
  # ==========================================
  db:
    image: postgres:15-alpine
    container_name: interview-prep-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-interview_prep}
      POSTGRES_USER: ${POSTGRES_USER:-interview_prep}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d:ro
    networks:
      - app-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==========================================
  # REDIS (Cache + Sessions + Rate Limiting)
  # ==========================================
  redis:
    image: redis:7-alpine
    container_name: interview-prep-redis
    restart: unless-stopped
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --appendfsync everysec
    volumes:
      - redis_data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ==========================================
  # MINIO (S3-Compatible File Storage)
  # ==========================================
  minio:
    image: minio/minio:latest
    container_name: interview-prep-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    ports:
      - "9001:9001"   # MinIO Console (internal)
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:-minioadmin123}
    volumes:
      - minio_data:/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==========================================
  # ADMIN TOOLS
  # ==========================================
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: interview-prep-pgadmin
    restart: unless-stopped
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@admin.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD:-admin}
    ports:
      - "5050:80"
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    networks:
      - app-network
    profiles:
      - admin-tools   # Only when needed

  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: interview-prep-redis-ui
    restart: unless-stopped
    environment:
      REDIS_HOSTS: local:redis:6379
    ports:
      - "8081:8081"
    networks:
      - app-network
    profiles:
      - admin-tools   # Only when needed

# ==========================================
# VOLUMES
# ==========================================
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  minio_data:
    driver: local
  pgadmin_data:
    driver: local
  app_logs:
    driver: local

# ==========================================
# NETWORKS
# ==========================================
networks:
  app-network:
    driver: bridge
```

**Running commands:**
```bash
# Normal startup (backend + db + redis + minio + nginx)
docker compose up -d

# With admin tools (pgadmin + redis-commander)
docker compose --profile admin-tools up -d

# Run migrations
docker compose exec backend alembic upgrade head

# View logs
docker compose logs -f backend

# Scale backend (Phase 2)
docker compose up -d --scale backend=3
```

---

## EXECUTION ORDER (Sprint Plan)

### Sprint 1 (Week 1): Critical Fixes
```
Day 1-2: TASK-001 (config fix) + TASK-002 (Redis service)
Day 3-4: TASK-003 (MinIO/S3 storage) + TASK-004 (resume schema fix)
Day 5:   Testing + verification of all P0 tasks
```

### Sprint 2 (Week 2): Stability
```
Day 1-2: TASK-005 (connection pooling) + TASK-006 (health checks)
Day 3:   TASK-007 (metadata columns) + TASK-008 (feature flags)
Day 4-5: TASK-009 (Gunicorn optimization) + TASK-012 (Groq proxy fix)
```

### Sprint 3 (Week 3): Platform Hardening
```
Day 1-2: TASK-010 (Nginx) + TASK-011 (Alembic migrations)
Day 3-4: TASK-013 (Redis sessions) + TASK-014 (Redis rate limiting)
Day 5:   TASK-015 (cost dashboard)
```

### Sprint 4 (Week 4): Intelligence Features
```
Day 1-2: TASK-016 (topic metadata population)
Day 3-4: TASK-017 (article enhancement)
Day 5:   TASK-018 (user onboarding)
```

---

## SCALE READINESS CHECKLIST

### At 100 Users (Now)
- [ ] TASK-001: Config fixed
- [ ] TASK-002: Redis running
- [ ] TASK-003: Files in MinIO
- [ ] TASK-004: Resume analysis working
- [ ] TASK-006: Health checks

### At 500 Users
- [ ] TASK-005: Connection pooling
- [ ] TASK-009: Async Gunicorn workers
- [ ] TASK-010: Nginx in place
- [ ] TASK-013: Redis sessions
- [ ] TASK-014: Redis rate limiting

### At 1000 Users (Phase 1 Complete)
- [ ] All above +
- [ ] TASK-011: Alembic migrations
- [ ] TASK-015: Cost monitoring
- [ ] TASK-016: Topic metadata
- [ ] Monitoring: Prometheus + Grafana (new task for later)
- [ ] Backups: Automated PostgreSQL + MinIO backups

### Phase 2 Triggers (When 1k+ users)
These are NOT in scope now but designed for:
- Add Elasticsearch (search)
- Add TimescaleDB (analytics)
- Scale backend horizontally (docker compose scale backend=3)
- Add read replica for PostgreSQL
- CDN for static files
- Consider extracting Practice Service (sandboxes)

---

## NOTES FOR IMPLEMENTATION

1. **Never alter schema without a migration file** - even small changes
2. **Feature flags for everything new** - deploy disabled, enable when ready
3. **Redis DBs are separate** - use DB 0 for cache, DB 1 for sessions, DB 2 for rate limiting
4. **MinIO in dev, real S3 in prod** - just change `S3_ENDPOINT_URL` env var
5. **Don't over-engineer yet** - monolith is fine until 1k users
6. **Every service needs health check** - Docker needs to know what's alive
7. **Logs to stdout** - Docker handles log routing, not your app

---

*Generated: 2026-02-17 | Review: CTO | Status: Ready for Implementation*
