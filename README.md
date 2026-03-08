# Energy Tracker API

[![Build Status](https://github.com/levieohlund/EnergyTracker/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/levieohlund/EnergyTracker/actions/workflows/deploy.yml)

Ett backendprojekt byggt i FastAPI för att hantera energimätningar i byggprojekt. Fokus ligger på modern drift: containerisering, automatiserad deploy och enkel lokal utveckling.

## Projektöversikt

- Bygger ett REST-API med endpoint för att skapa och läsa energimätningar
- Lagrar data i SQLite
- Körs lokalt med Docker Compose eller direkt via Python
- Deployas automatiskt till AWS EC2 via GitHub Actions

## Teknik

- Python, FastAPI, Uvicorn
- SQLite
- Docker och Docker Compose
- GitHub Actions
- AWS EC2

## Arkitektur i korthet

- API: main.py
- Databas: energy.db (persistent volume i Docker Compose)
- Containerisering: Dockerfile
- Deploy-workflow: .github/workflows/deploy.yml

## API

- GET /health
- POST /measurements
- GET /measurements

Exempel för POST /measurements:

```json
{
  "project_name": "Byggprojekt A",
  "date": "2026-03-08",
  "kwh_consumed": 123.4
}
```

## Kör lokalt

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Dokumentation lokalt:

- http://127.0.0.1:8000/docs

## Kör med Docker Compose

```bash
docker compose up --build -d
docker compose ps
```

Stoppa:

```bash
docker compose down
```

## CI/CD och deploy

Vid push till main körs en GitHub Actions-pipeline som:

1. Ansluter till EC2 via SSH
2. Hämtar senaste kod från main
3. Bygger och startar om tjänsten med Docker Compose

Secrets som används:

- HOST
- USERNAME
- KEY

## Säkerhet och hygiene

- Känsliga värden ligger i GitHub Secrets
- .dockerignore exkluderar .venv, energy.db och __pycache__

## Live

API-dokumentation:

- http://16.170.249.200:8000/docs
