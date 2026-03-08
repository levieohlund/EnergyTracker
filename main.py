from datetime import date
from typing import List
import os

import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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


# Dashboard på startsidan som visar snabb statistik från databasen.
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> str:
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            # 1. Senaste mätvärdet (senaste datum + senaste id).
            cursor.execute(
                """
                SELECT kwh_consumed
                FROM measurements
                ORDER BY date DESC, id DESC
                LIMIT 1
                """
            )
            latest = cursor.fetchone()
            latest_val = f"{latest[0]:.2f}" if latest else "0.00"

            # 2. Dagens högsta värde (utifrån kolumnen date).
            cursor.execute(
                """
                SELECT MAX(kwh_consumed)
                FROM measurements
                WHERE date = date('now')
                """
            )
            peak = cursor.fetchone()
            peak_val = f"{peak[0]:.2f}" if peak and peak[0] is not None else "0.00"

            # 3. Totalt antal mätningar i tabellen.
            cursor.execute("SELECT COUNT(*) FROM measurements")
            total_count = cursor.fetchone()[0]
    except sqlite3.Error:
        latest_val, peak_val, total_count = "Error", "Error", 0

    return f"""
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Energy Tracker Pro</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>
            .glass {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }}
        </style>
    </head>
    <body class="bg-[#0f172a] text-slate-200 min-h-screen font-sans">
        <div class="container mx-auto px-6 py-12">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-16 gap-6">
                <div>
                    <h1 class="text-5xl font-extrabold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent mb-2">
                        EnergyTracker <span class="font-light italic">Pro</span>
                    </h1>
                    <p class="text-slate-400 flex items-center">
                        <span class="w-3 h-3 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                        Systemet är Live på AWS EC2
                    </p>
                </div>
                <div class="flex gap-4">
                    <a href="/measurements/table" class="glass hover:bg-white/10 px-6 py-4 rounded-2xl font-bold transition-all flex items-center gap-3 text-blue-400">
                        <i class="fas fa-table"></i> Mätningar
                    </a>
                    <a href="/docs" class="glass hover:bg-white/10 px-6 py-4 rounded-2xl font-bold transition-all flex items-center gap-3 text-yellow-400">
                        <i class="fas fa-code"></i> API Referens
                    </a>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="glass p-8 rounded-[2rem] relative overflow-hidden group">
                    <div class="absolute -right-4 -top-4 text-yellow-500/10 text-9xl rotate-12 group-hover:rotate-0 transition-transform">
                        <i class="fas fa-bolt"></i>
                    </div>
                    <h2 class="text-slate-400 uppercase tracking-widest text-sm font-bold mb-4">Senaste Mätning</h2>
                    <div class="flex items-baseline gap-2">
                        <span class="text-6xl font-black text-white">{latest_val}</span>
                        <span class="text-xl text-slate-500">kWh</span>
                    </div>
                </div>

                <div class="glass p-8 rounded-[2rem] relative overflow-hidden group">
                    <div class="absolute -right-4 -top-4 text-blue-500/10 text-9xl rotate-12 group-hover:rotate-0 transition-transform">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <h2 class="text-slate-400 uppercase tracking-widest text-sm font-bold mb-4">Dagens Topp</h2>
                    <div class="flex items-baseline gap-2">
                        <span class="text-6xl font-black text-white">{peak_val}</span>
                        <span class="text-xl text-slate-500">kWh</span>
                    </div>
                </div>

                <div class="glass p-8 rounded-[2rem] flex flex-col justify-between">
                    <h2 class="text-slate-400 uppercase tracking-widest text-sm font-bold mb-6">Databas Status</h2>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center">
                            <span class="text-slate-500">Totala Poster</span>
                            <span class="font-mono text-xl text-yellow-400">{total_count}</span>
                        </div>
                        <div class="h-1 bg-white/10 rounded-full overflow-hidden">
                            <div class="h-full bg-yellow-500 w-3/4"></div>
                        </div>
                        <p class="text-xs text-slate-500">SQLite Engine: {DB_FILE} active</p>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


# HTML-vy med tabell över alla mätningar (API:et på /measurements är fortsatt JSON).
@app.get("/measurements/table", response_class=HTMLResponse, include_in_schema=False)
async def measurements_table() -> str:
    try:
        with sqlite3.connect(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT id, project_name, date, kwh_consumed
                FROM measurements
                ORDER BY id DESC
                """
            ).fetchall()
    except sqlite3.Error:
        rows = []

    table_rows = "".join(
        f"""
        <tr class="border-b border-white/10 hover:bg-white/5">
            <td class="px-4 py-3">{row['id']}</td>
            <td class="px-4 py-3">{row['project_name']}</td>
            <td class="px-4 py-3">{row['date']}</td>
            <td class="px-4 py-3 text-right">{row['kwh_consumed']:.2f}</td>
        </tr>
        """
        for row in rows
    )

    if not table_rows:
        table_rows = """
        <tr>
            <td colspan="4" class="px-4 py-6 text-center text-slate-400">Inga mätningar ännu.</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mätningar | Energy Tracker</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-[#0f172a] text-slate-200 min-h-screen font-sans">
        <div class="container mx-auto px-6 py-10">
            <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
                <h1 class="text-3xl font-bold">Energimätningar</h1>
                <div class="flex gap-3">
                    <a href="/" class="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 transition">Till dashboard</a>
                    <a href="/measurements" class="px-4 py-2 rounded-xl bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 transition">Visa JSON</a>
                </div>
            </div>

            <div class="rounded-2xl border border-white/10 overflow-hidden bg-white/5">
                <table class="w-full text-left">
                    <thead class="bg-white/10 text-slate-300 text-sm uppercase tracking-wide">
                        <tr>
                            <th class="px-4 py-3">ID</th>
                            <th class="px-4 py-3">Projekt</th>
                            <th class="px-4 py-3">Datum</th>
                            <th class="px-4 py-3 text-right">kWh</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """


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
