from __future__ import annotations

import os
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .domain import QuoteInputs, calculate_quote
from .store import connect, dashboard


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = os.getenv("DEMO_DATABASE", str(BASE_DIR.parent / ".data" / "manufacturing.db"))


class QuoteRequest(BaseModel):
    material_cost_per_gram: Decimal = Field(gt=0)
    part_weight_grams: Decimal = Field(gt=0)
    machine_hours: Decimal = Field(gt=0)
    machine_hour_cost: Decimal = Field(gt=0)
    labor_minutes: Decimal = Field(ge=0)
    labor_hour_cost: Decimal = Field(ge=0)
    packaging_cost: Decimal = Field(ge=0)
    failure_rate_percent: Decimal = Field(ge=0, lt=100)
    margin_percent: Decimal = Field(ge=0)
    quantity: int = Field(ge=1, le=10_000)


class StatusUpdate(BaseModel):
    status: str = Field(pattern="^(Queued|In production|Quality check|Ready|Delivered|Cancelled)$")


def role(x_demo_role: str = Header(default="viewer")) -> str:
    normalized = x_demo_role.lower()
    if normalized not in {"viewer", "operator", "admin"}:
        raise HTTPException(403, "Unknown demo role")
    return normalized


def build_app(database_path: str = DATABASE_PATH) -> FastAPI:
    connection = connect(database_path)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        connection.close()

    app = FastAPI(
        title="Small Manufacturing Operations Demo",
        version="1.0.0",
        description="Synthetic operations, costing, RBAC and audit demo.",
        lifespan=lifespan,
    )
    app.state.db = connection

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "data": "synthetic"}

    @app.get("/api/dashboard")
    def read_dashboard() -> dict:
        return dashboard(app.state.db)

    @app.get("/api/orders")
    def list_orders() -> list[dict]:
        rows = app.state.db.execute("SELECT * FROM orders ORDER BY due_date, id DESC").fetchall()
        return [dict(row) for row in rows]

    @app.patch("/api/orders/{order_id}/status")
    def update_status(order_id: int, payload: StatusUpdate, current_role: str = Depends(role)) -> dict:
        if current_role not in {"operator", "admin"}:
            raise HTTPException(403, "Operator or admin role required")
        current = app.state.db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if current is None:
            raise HTTPException(404, "Order not found")
        app.state.db.execute("UPDATE orders SET status = ? WHERE id = ?", (payload.status, order_id))
        app.state.db.execute(
            "INSERT INTO audit_log (actor_role, action, entity_type, entity_id, details) VALUES (?, 'status_changed', 'order', ?, ?)",
            (current_role, order_id, f"{current['status']} -> {payload.status}"),
        )
        app.state.db.commit()
        return dict(app.state.db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone())

    @app.post("/api/quotes")
    def quote(payload: QuoteRequest) -> dict:
        result = calculate_quote(QuoteInputs(**payload.model_dump()))
        return {key: float(value) if isinstance(value, Decimal) else value for key, value in result.items()}

    @app.get("/api/audit")
    def audit(current_role: str = Depends(role)) -> list[dict]:
        if current_role != "admin":
            raise HTTPException(403, "Admin role required")
        rows = app.state.db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 50").fetchall()
        return [dict(row) for row in rows]

    app.mount("/assets", StaticFiles(directory=BASE_DIR / "static"), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(BASE_DIR / "static" / "index.html")

    return app


app = build_app()
