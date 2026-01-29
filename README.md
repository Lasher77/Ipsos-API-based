# BVMW Typing Tool Segmenter API

Ein FastAPI-Microservice, der die Excel-basierte Mitglieds-Segmentierung anhand einer JSON-Regeldatei 1:1 ersetzt.

## Features
- Berechnet binäre Features anhand der Rules-JSON.
- Segment-Scoring inkl. deterministischem Tie-Breaking.
- Klassifiziert Core/Mid/Rest auf Basis der Thresholds.
- Einzel- und Batch-Endpoints.

## Lokales Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Service starten:

```bash
uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t bvmw-segmenter .
docker run -p 8000:8000 bvmw-segmenter
```

Oder via Docker Compose:

```bash
docker compose up
```

## API Beispiele

Health Check:

```bash
curl http://localhost:8000/health
```

Segmentierung:

```bash
curl -X POST "http://localhost:8000/segment?include_features=true&pretty_scores=true" \
  -H "Content-Type: application/json" \
  -d '{"Status_ Mitgliedschaft": "Mitglied beim Mittelstand. BVMW", "Wirtschaftsregion": "Bayern Nord"}'
```

Batch:

```bash
curl -X POST "http://localhost:8000/segment/batch" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"Status_ Mitgliedschaft": "Mitglied beim Mittelstand. BVMW"}, {"Wirtschaftsregion": "Bayern Nord"}]}'
```

## n8n Beispiel (textuell)

1. HTTP Request Node: POST `/segment` mit Member JSON.
2. Ergebnis-Response prüfen und gewünschte Felder (segment, type, scores) extrahieren.
3. Salesforce Update Node: Felder mit den neuen Segmentierungswerten aktualisieren.

## Regeln
Die Rules-Datei liegt unter `rules/bvmw_typing_tool_rules_v2.json`. Standardpfad kann via Umgebungsvariable `SEGMENTER_RULES_PATH` überschrieben werden.
