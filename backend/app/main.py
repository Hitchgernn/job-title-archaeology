from fastapi import FastAPI

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
