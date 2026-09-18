from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.agent import LeadEnrichmentAgent


app = FastAPI(
    title="Lead Enrichment Agent API",
    description="API for autonomous company lead enrichment",
    version="1.0.0"
)


# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EnrichRequest(BaseModel):
    domain: str


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "Lead Enrichment Agent API"
    }


@app.post("/enrich")
def enrich_lead(request: EnrichRequest):

    domain = request.domain.strip()

    if not domain:
        raise HTTPException(
            status_code=400,
            detail="Domain is required"
        )

    try:
        agent = LeadEnrichmentAgent()

        result = agent.enrich(domain)

        # Convert Pydantic model to JSON-compatible dictionary
        if hasattr(result, "model_dump"):
            return result.model_dump()

        if hasattr(result, "dict"):
            return result.dict()

        return result

    except Exception as e:
        print(f"[API ERROR] {domain}: {e}")

        raise HTTPException(
            status_code=500,
            detail=f"Lead enrichment failed: {str(e)}"
        )