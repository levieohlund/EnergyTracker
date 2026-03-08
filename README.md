# Energy Tracker API

Ett enkelt REST-API byggt med FastAPI för att lagra och läsa fiktiv energidata för byggprojekt.

## Innehåll

- Python + FastAPI
- SQLite-databas (`energy.db` lokalt, eller `/app/data/energy.db` i Docker via environment)
- Endpoints för att:
  - lägga till energimätningar
  - hämta alla energimätningar
  - verifiera hälsa (`/health`)

## Projektstruktur

- `main.py` – API och databaslogik
- `requirements.txt` – Python-beroenden
- `Dockerfile` – containerisering av appen
- `docker-compose.yml` – enkel lokal körning med Docker Compose
- `.dockerignore` – filer/mappar som inte ska in i imagen

## Förkrav

- Python 3.10+ (rekommenderat: 3.13)
- `pip`
- (Valfritt) Docker Desktop om du vill köra i container

## 1) Lokal körning (utan Docker)

### Installera beroenden

```bash
pip install -r requirements.txt
```

### Starta API:t

```bash
python -m uvicorn main:app --reload
```

API:t körs då på:

- `http://127.0.0.1:8000`
- Interaktiv dokumentation: `http://127.0.0.1:8000/docs`

## 2) API-endpoints

### GET `/health`
Kontrollerar att API:t är igång.

**Exempel-svar:**

```json
{
  "status": "ok"
}
```

### POST `/measurements`
Lägger till en ny energimätning.

**Request body (JSON):**

```json
{
  "project_name": "Byggprojekt A",
  "date": "2026-03-08",
  "kwh_consumed": 123.4
}
```

**Exempel-svar:**

```json
{
  "id": 1,
  "project_name": "Byggprojekt A",
  "date": "2026-03-08",
  "kwh_consumed": 123.4
}
```

### GET `/measurements`
Hämtar alla sparade mätningar.

**Exempel-svar:**

```json
[
  {
    "id": 1,
    "project_name": "Byggprojekt A",
    "date": "2026-03-08",
    "kwh_consumed": 123.4
  }
]
```

## 3) Snabba testanrop

### Med `curl`

```bash
curl -X POST "http://127.0.0.1:8000/measurements" \
  -H "Content-Type: application/json" \
  -d "{\"project_name\":\"Byggprojekt A\",\"date\":\"2026-03-08\",\"kwh_consumed\":123.4}"

curl "http://127.0.0.1:8000/measurements"
curl "http://127.0.0.1:8000/health"
```

### Med PowerShell

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/measurements" -ContentType "application/json" -Body '{"project_name":"Byggprojekt A","date":"2026-03-08","kwh_consumed":123.4}'

Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/measurements"
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/health"
```

## 4) Körning med Docker

### Bygg image manuellt

```bash
docker build -t energy-tracker .
```

### Kör container manuellt

```bash
docker run --rm -p 8000:8000 energy-tracker
```

## 5) Körning med Docker Compose

Projektet innehåller en named volume (`energy_data`) för persistent databas i containerläge.

### Starta

```bash
docker compose up --build
```

### Kontrollera status (inklusive healthcheck)

```bash
docker compose ps
```

När allt fungerar ska `api` visas som `healthy`.

### Stoppa

```bash
docker compose down
```

> Obs: Volymen ligger kvar efter `down`, så data bevaras mellan omstarter.

## 6) Databasinformation

- Lokalt (utan Docker): `energy.db` i projektroten.
- Docker Compose: `DB_FILE=/app/data/energy.db`, lagras i named volume `energy_data`.

Tabellen som skapas automatiskt vid uppstart heter `measurements` och har kolumner:

- `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT)
- `project_name` (TEXT)
- `date` (TEXT i ISO-format, t.ex. `2026-03-08`)
- `kwh_consumed` (REAL)

## 7) Vanliga problem och lösningar

### Port 8000 är upptagen
Stoppa processen som använder porten, eller mappa en annan port i Docker/Compose.

### `ModuleNotFoundError`
Kör om:

```bash
pip install -r requirements.txt
```

### API startar men sparar ingen data i Docker
Kontrollera att du startar via `docker compose up` så att volym + `DB_FILE` används.

---

## Snabbstart (kort version)

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Öppna sedan `http://127.0.0.1:8000/docs`.
