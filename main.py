
from contextlib import asynccontextmanager
from datetime import date, datetime
from sqlite3 import IntegrityError
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from scalar_fastapi import add_scalar_reference

from database import (
    create_database,
    create_shipment,
    delete_shipment,
    get_shipment,
    get_shipments,
    update_shipment,
)


class ShipmentBase(BaseModel):
    sender: str = Field(min_length=1)
    recipient: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    status: str = Field(default="pending", min_length=1)
    estimated_delivery: date | None = None


class ShipmentCreate(ShipmentBase):
    tracking_id: int = Field(gt=0)


class ShipmentUpdate(BaseModel):
    sender: str | None = Field(default=None, min_length=1)
    recipient: str | None = Field(default=None, min_length=1)
    origin: str | None = Field(default=None, min_length=1)
    destination: str | None = Field(default=None, min_length=1)
    status: str | None = Field(default=None, min_length=1)
    estimated_delivery: date | None = None


class Shipment(ShipmentCreate):
    created_at: datetime


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_database()
    yield


app = FastAPI(lifespan=lifespan)
add_scalar_reference(app)


@app.post("/shipments", response_model=Shipment, status_code=status.HTTP_201_CREATED)
def add_shipment(shipment: ShipmentCreate) -> dict[str, Any]:
    try:
        return create_shipment(shipment.model_dump())
    except IntegrityError as error:
        if "UNIQUE constraint failed" in str(error):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tracking ID already exists",
            ) from error
        raise


@app.get("/shipments", response_model=list[Shipment])
def list_shipments() -> list[dict[str, Any]]:
    return get_shipments()


@app.get("/shipments/{tracking_id}", response_model=Shipment)
def read_shipment(tracking_id: int) -> dict[str, Any]:
    shipment = get_shipment(tracking_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@app.put("/shipments/{tracking_id}", response_model=Shipment)
def edit_shipment(
    tracking_id: int, shipment: ShipmentUpdate
) -> dict[str, Any]:
    updated_shipment = update_shipment(
        tracking_id, shipment.model_dump(exclude_unset=True)
    )
    if updated_shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return updated_shipment


@app.delete("/shipments/{tracking_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_shipment(tracking_id: int) -> None:
    if not delete_shipment(tracking_id):
        raise HTTPException(status_code=404, detail="Shipment not found")


@app.get("/track/{tracking_id}", response_model=Shipment)
def track_shipment(tracking_id: int) -> dict[str, Any]:
    return read_shipment(tracking_id)
