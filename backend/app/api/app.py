from pathlib import Path

import duckdb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.settings import get_settings
from app.db.warehouse import Warehouse
from app.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="PRIG SNIES API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    static_dir = Path(__file__).resolve().parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    app.include_router(router)

    @app.on_event("startup")
    def initialize_warehouse() -> None:
        settings = get_settings()
        if settings.warehouse_path.exists():
            return

        warehouse = Warehouse(settings)
        try:
            warehouse.initialize()
        except duckdb.IOException:
            if not settings.warehouse_path.exists():
                raise

    return app
