# HireTrace

Recruitment trust intelligence through open-source data and knowledge graphs.

> "Before you apply, know who you're giving your data to."

## What is this

HireTrace analyzes job postings (starting with LinkedIn) and returns a **Job Trust Report**:
risk signals and evidence, not a binary "this is a scam" verdict. It's closer to
*VirusTotal for job offers* than a blocklist.

The analysis is split into independent scores, since a legitimate company can still run
an invasive or opaque hiring process:

- **Job Legitimacy** — does the company exist, does the posting actually belong to them?
- **Candidate Data Risk** — what are they asking for (CV → low, bank account/crypto → critical)?
- **Hiring Evidence** — reposting patterns, description similarity, ghost-job signals.

## Architecture

Data flows through a pipeline. Each stage only talks to the next through shared data
models — no stage reaches into another's internals. This keeps sources, enrichment
steps, and storage swappable independently.

```
Job URL / text / screenshot
        ↓
   collectors        → extract raw entities (Company, Publisher, Job, Domain)
        ↓
   enrichment         → chainable steps: domain age, description similarity,
        ↓                cross-referencing careers pages / Greenhouse / Lever / WHOIS
   resolution         → entity resolution: is "Micro1" == "micro1.ai" == "Micro1 Inc."?
        ↓
   graph              → knowledge graph storage (who shares domains, recruiters,
        ↓                platforms, near-identical text across postings)
   api (FastAPI)      → Job Trust Report
```

### Modules (`src/hire_trace/`)

| Module | Responsibility |
|---|---|
| `api/` | FastAPI routers and request/response handling |
| `core/` | config, logging, shared exceptions |
| `schemas/` | Pydantic models shared across every stage (`Job`, `Company`, `Publisher`, `Domain`, `Salary`, ...) |
| `collectors/` | one module per source, behind a common interface — adding a new source (Indeed, a careers page) means adding a class, not touching the pipeline |
| `enrichment/` | composable enrichment steps, independently testable |
| `resolution/` | entity resolution — the hardest problem here, kept isolated from enrichment |
| `graph/` | storage behind a repository interface (Postgres/pgvector now, Neo4j later without touching business logic) |
| `pipeline.py` | orchestrates collector → enrichment → resolution → graph |

### Why this shape

- **MVP has no crawler and no supervised ML.** The user pastes the job posting; that's
  the acquisition strategy until there's a labeled dataset worth training on. Risk
  scoring starts as an explicit rule engine.
- **LinkedIn is a discovery source, not a scrape target.** Aggressive automated scraping
  of LinkedIn is fragile (ToS-wise and technically) as a foundation; the plan is to
  cross-reference postings against public sources instead (official careers pages, ATS
  platforms, WHOIS/DNS, business registries).
- **Historical snapshots matter more than current state.** A company posting 300+ jobs
  in 6 months with near-identical descriptions is only visible if the data is kept over
  time, not just queried once.

## Stack

- **Backend**: FastAPI
- **Storage (MVP)**: PostgreSQL + pgvector (embeddings for description similarity)
- **Graph (later)**: Neo4j, once entity relationships are worth querying as a graph
- **Package management**: [uv](https://docs.astral.sh/uv/)

## Status

Early scaffolding. Building the `collectors → enrichment → graph` flow first, before
any frontend.
