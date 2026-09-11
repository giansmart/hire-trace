from fastapi import FastAPI

from hire_trace.api.routes import jobs

app = FastAPI(title="HireTrace")
app.include_router(jobs.router)
