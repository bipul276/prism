from fastapi import FastAPI, HTTPException, Request
from ml.database import engine, Base
from ml.models import Claim, AnalysisResult
import chromadb
import os
from pydantic import BaseModel
from ml.workers.tasks import analyze_text_task
from celery.result import AsyncResult

# Rate Limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Setup Limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/hour"])

app = FastAPI(title="PRISM API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

class AnalyzeRequest(BaseModel):
    text: str

@app.on_event("startup")
async def startup():
    print("Starting PRISM API... Checking dependencies...")
    
    # 1. Environment Validation
    required_vars = ["DATABASE_URL", "REDIS_URL", "CHROMA_HOST"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Missing critical environment variables: {missing}")

    # 2. Connectivity Checks
    # Redis
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL"))
        r.ping()
        print("✅ Redis connected.")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        # raise e # Optional: Fail hard

    # Chroma
    try:
        host = os.getenv("CHROMA_HOST")
        port = int(os.getenv("CHROMA_PORT", 8000))
        # Simple TCP check or HTTP ping logic
        # For simplicity, we assume if imports loaded, specific checks happen in modules.
        # Ideally: requests.get(f"http://{host}:{port}/api/v1/heartbeat")
        print(f"✅ Configured Chroma at {host}:{port}")
    except Exception as e:
        print(f"❌ Chroma config error: {e}")

    # 3. Database Creation & Auto-Ingestion
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database schema synced.")
        
        # Check if DB is empty
        from ml.database import AsyncSessionLocal
        from ml.models import Claim
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Claim))
            existing = result.scalars().first()
            if not existing:
                print("📭 Database is empty. Triggering auto-ingestion...")
                from ml.ingest import main as ingest_main
                await ingest_main()
            else:
                print("📚 Database already populated.")
                
    except Exception as e:
        print(f"❌ Database init failed: {e}")
        raise e

    print("PRISM API Ready. v1.0.0")

@app.get("/health")
async def health_check():
    return {
        "status": "ok", 
        "service": "prism-api", 
        "version": "1.0.0",
        "dependencies": ["postgres", "redis", "chromadb"]
    }

@app.post("/api/analyze")
@limiter.limit("5/minute")
async def analyze_claim(request: AnalyzeRequest, request_obj: Request):
    # Enqueue task
    task = analyze_text_task.delay(request.text)
    return {"job_id": task.id, "status": "submitted"}

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    task_result = AsyncResult(job_id)
    if task_result.state == 'PENDING':
        return {"status": "processing"}
    elif task_result.state == 'SUCCESS':
        return {"status": "completed", "result": task_result.result}
    elif task_result.state == 'FAILURE':
        return {"status": "failed", "error": str(task_result.result)}
    else:
        return {"status": task_result.state}
