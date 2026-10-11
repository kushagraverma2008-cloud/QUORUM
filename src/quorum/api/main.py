from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from quorum.config import settings
from quorum.brains.store import ExpertStore
from quorum.api.routes import router

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: preload expert store into memory
    print(f"[{settings.app_name}] Preloading expert store...")
    store = ExpertStore.get_instance()
    print(f"[{settings.app_name}] Successfully loaded {len(store.get_all_experts())} experts.")
    yield
    print(f"[{settings.app_name}] Shutting down.")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend engine for Quorum (Expert Council) - AI startup evaluation platform.",
    lifespan=lifespan
)

# CORS Middleware (allows Google Stitch and local development clients)
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if "*" in origins:
    allow_origins = ["*"]
else:
    allow_origins = origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Mount static files & root route
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(STATIC_DIR / "index.html"))

    @app.get("/war-room")
    async def serve_war_room():
        return FileResponse(str(STATIC_DIR / "war_room_console.html"))

    @app.get("/curation")
    async def serve_curation():
        return FileResponse(str(STATIC_DIR / "brief_curation.html"))

    @app.get("/theater")
    async def serve_theater():
        return FileResponse(str(STATIC_DIR / "council_theater_analysis.html"))

    @app.get("/report")
    async def serve_report():
        return FileResponse(str(STATIC_DIR / "council_report_stage4.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("quorum.api.main:app", host=settings.host, port=settings.port, reload=True)

