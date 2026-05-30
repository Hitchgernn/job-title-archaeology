from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.archive.router import router as archive_router
from backend.companies.router import router as companies_router
from backend.dashboard.router import router as dashboard_router

app = FastAPI(title="Job Title Archaeology")
app.include_router(dashboard_router)
app.include_router(archive_router)
app.include_router(companies_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIST = _PROJECT_ROOT / "frontend" / "dist"
_ARCHIVE_GENERATED = _FRONTEND_DIST / "archive-generated"
if not _ARCHIVE_GENERATED.exists():
    _ARCHIVE_GENERATED = _PROJECT_ROOT / "frontend" / "public" / "archive-generated"

if _ARCHIVE_GENERATED.exists():
    app.mount("/archive-generated", StaticFiles(directory=_ARCHIVE_GENERATED), name="archive-generated")

if _FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=_FRONTEND_DIST / "assets"), name="frontend-assets")

    @app.get("/")
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str = "") -> FileResponse:
        index_path = _FRONTEND_DIST / "index.html"
        return FileResponse(index_path)
