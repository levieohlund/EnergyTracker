from datetime import date
from typing import List
import os

import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# Namnet på SQLite-databasen. Filen skapas automatiskt om den inte finns.
DB_FILE = os.getenv("DB_FILE", "energy.db")

# Skapar en FastAPI-applikation.
app = FastAPI(title="Energy Tracker API")


# Pydantic-modell för inkommande energimätning (POST-request).
class MeasurementCreate(BaseModel):
    project_name: str = Field(..., min_length=1, description="Namn på projekt")
    date: date
    kwh_consumed: float = Field(..., ge=0, description="Förbrukning i kWh")


# Pydantic-modell för data som skickas tillbaka från API:t.
class Measurement(MeasurementCreate):
    id: int


# Hjälpfunktion som skapar databas och tabell om de inte redan finns.
def init_db() -> None:
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                date TEXT NOT NULL,
                kwh_consumed REAL NOT NULL
            )
            """
        )
        conn.commit()


# Körs när appen startar för att säkerställa att tabellen finns.
@app.on_event("startup")
def on_startup() -> None:
    init_db()


# Enkel health-endpoint för att verifiera att API:t är igång.
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# POST-endpoint för att lägga till en ny energimätning.
@app.post("/measurements", response_model=Measurement)
def create_measurement(measurement: MeasurementCreate) -> Measurement:
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.execute(
                """
                INSERT INTO measurements (project_name, date, kwh_consumed)
                VALUES (?, ?, ?)
                """,
                (
                    measurement.project_name,
                    measurement.date.isoformat(),
                    measurement.kwh_consumed,
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid

        return Measurement(id=new_id, **measurement.model_dump())
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f"Databasfel: {exc}") from exc


# GET-endpoint för att hämta alla sparade energimätningar.
@app.get("/measurements", response_model=List[Measurement])
def list_measurements() -> List[Measurement]:
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, project_name, date, kwh_consumed
                FROM measurements
                ORDER BY id
                """
            ).fetchall()

        return [
            Measurement(
                id=row["id"],
                project_name=row["project_name"],
                date=date.fromisoformat(row["date"]),
                kwh_consumed=row["kwh_consumed"],
            )
            for row in rows
        ]
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail=f"Databasfel: {exc}") from exc
