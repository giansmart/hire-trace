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

```mermaid
flowchart TD
    input(["Job URL / text / screenshot"])

    subgraph built["Built"]
        collectors["collectors<br/>fetch + persist raw HTML"]
        rawdocs[("raw_documents")]
        extraction["extraction<br/>RawDocument → Job<br/>(heuristic today, LLM later)"]
        jobs[("jobs")]
    end

    subgraph planned["Planned"]
        enrichment["enrichment<br/>domain age, description similarity,<br/>cross-reference careers pages / ATS / WHOIS"]
        resolution["resolution<br/>entity resolution<br/>(is 'Micro1' == 'micro1.ai'?)"]
        graph["graph<br/>knowledge graph storage"]
        api["api (FastAPI)"]
    end

    report(["Job Trust Report"])

    input --> collectors
    collectors --> rawdocs
    collectors --> extraction
    extraction --> jobs
    extraction --> enrichment
    enrichment --> resolution
    resolution --> graph
    graph --> api
    api --> report

    classDef built fill:#dff5e1,stroke:#2f9e44,color:#1b4332;
    classDef planned fill:#f1f3f5,stroke:#adb5bd,color:#495057,stroke-dasharray: 4 3;
    class collectors,rawdocs,extraction,jobs built;
    class enrichment,resolution,graph,api planned;
```

### Modules (`src/hire_trace/`)

| Module | Responsibility |
|---|---|
| `api/` | FastAPI routers and request/response handling |
| `core/` | config, DB engine/session, shared exceptions |
| `schemas/` | Pydantic models shared across every stage (`Job`, `Company`, `Publisher`, `Domain`, `Salary`, `RawDocument`, ...) |
| `collectors/` | fetches and persists raw HTML per source, behind a common interface — adding a new source (Indeed, a careers page) means adding a class, not touching the pipeline |
| `extraction/` | turns a `RawDocument` into `Job` entities, behind a common `JobExtractor` interface — a naive heuristic today, an LLM-based one later, without touching collectors or anything downstream |
| `enrichment/` | composable enrichment steps, independently testable |
| `resolution/` | entity resolution — the hardest problem here, kept isolated from enrichment |
| `graph/` | storage behind a repository interface (Postgres/pgvector now, Neo4j later without touching business logic) |
| `pipeline.py` | orchestrates collector → extraction → enrichment → resolution → graph |

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
- **Storage (MVP)**: PostgreSQL + pgvector, via SQLAlchemy (async) + Alembic migrations, in Docker Compose
- **Graph (later)**: Neo4j, once entity relationships are worth querying as a graph
- **Package management**: [uv](https://docs.astral.sh/uv/)

## Status

Early scaffolding. `RawDocument` and the extracted `Job` (as JSONB for now — the
shape is still moving) are persisted in Postgres. A heuristic `JobExtractor` parses
schema.org JSON-LD when present (e.g. LinkedIn posts), falling back to blind
tag-stripping. Building the `collectors → extraction → enrichment → graph` flow
first, before any frontend.
