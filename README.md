# Autonomous Lead Enrichment Agent

An AI-powered lead enrichment system that crawls public company websites and extracts structured company, contact, and leadership information.

## Features

- Dynamic website crawling with Playwright
- JavaScript-rendered page support
- HTML/content cleaning with BeautifulSoup
- Public email extraction
- LinkedIn URL discovery
- Leadership and team member extraction
- OpenAI-based structured extraction
- Pydantic validation
- Error handling and fallback extraction
- FastAPI backend
- React dashboard
- JSON and CSV output

## Architecture

```text
React Dashboard
      ↓
FastAPI Backend
      ↓
LeadEnrichmentAgent
      ↓
Playwright Crawler
      ↓
Content Cleaner
      ↓
Deterministic Extraction
      ↓
OpenAI
      ↓
Pydantic Validation
      ↓
Structured Lead Data
```

## Project Structure

```text
Lead-enrichment-agent/
│
├── app/
│   ├── agent.py
│   ├── api.py
│   ├── crawler.py
│   ├── content_cleaner.py
│   ├── deterministic_extractor.py
│   ├── extractor.py
│   ├── schemas.py
│   └── search.py
│
├── frontend/
│   ├── public/
│   │   └── output.json
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       └── main.jsx
│
├── output/
│   ├── output.json
│   └── output.csv
│
├── main.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Tech Stack

- **Python** — Backend and agent development
- **FastAPI** — REST API
- **Playwright** — Browser automation and web crawling
- **BeautifulSoup** — Content cleaning
- **OpenAI** — LLM-based information extraction
- **Pydantic** — Structured output validation
- **React + Vite** — Frontend dashboard
- **JSON / CSV** — Output formats

## How It Works

The user provides a company domain through the React dashboard.

The system then:

1. Crawls relevant public pages.
2. Handles JavaScript-rendered content using Playwright.
3. Cleans unnecessary HTML and website boilerplate.
4. Extracts public emails and LinkedIn URLs deterministically.
5. Sends cleaned content to OpenAI.
6. Generates structured company intelligence.
7. Validates the response using Pydantic.
8. Returns the result through FastAPI.
9. Displays the enriched information in the React dashboard.

## Structured Information

The agent extracts:

- Company overview
- Target audience
- Public contact emails
- Leadership/team members
- Roles
- LinkedIn URLs when available
- Source URLs
- Confidence score

## Sample Output

```json
{
  "domain": "postman.com",
  "company_overview": "Postman is a platform for building and using APIs. It provides tools for API design, testing, and collaboration.",
  "target_audience": "developers",
  "contact_points": [
    {
      "email": "info@postman.com",
      "source_url": "https://postman.com/company/about-postman"
    }
  ],
  "leadership_team": [
    {
      "name": "Abhinav Asthana",
      "role": "CEO",
      "linkedin_url": null,
      "source_url": "https://postman.com/company/about-postman"
    }
  ],
  "confidence_score": 0.8
}
```

## API

### Health Check

```http
GET /
```

Example response:

```json
{
  "status": "running",
  "service": "Lead Enrichment Agent API"
}
```

### Enrich Lead

```http
POST /enrich
```

Request:

```json
{
  "domain": "github.com"
}
```

The API passes the domain to the `LeadEnrichmentAgent` and returns the structured enrichment result.

## Installation

### 1. Clone the Repository

```powershell
git clone <your-repository-url>
cd Lead-enrichment-agent
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
playwright install
```

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

Do not commit the `.env` file to GitHub.

Add this to `.gitignore`:

```text
.env
```

## Run Backend

From the project root:

```powershell
python -m uvicorn app.api:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

## Run Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Run Agent Directly

The agent can also be executed using:

```powershell
python main.py
```

Generated results are stored in:

```text
output/output.json
```

CSV results are stored in:

```text
output/output.csv
```

## Test Domains

The assignment domains are:

```text
postman.com
supabase.com
vapi.ai
```

The API can also be tested with other public company domains:

```text
github.com
stripe.com
notion.so
```

## Error Handling

The system handles:

- Invalid domains
- 404 pages
- Page timeouts
- Browser navigation failures
- JavaScript-rendered pages
- Missing website sections
- Missing emails
- Missing leadership information
- LLM extraction errors
- Invalid structured responses

A failure on one page does not stop the complete enrichment process.

## Hallucination Prevention

The LLM is instructed to:

- Use only the supplied crawled content
- Avoid unsupported information
- Avoid guessing missing details
- Return only verified public emails
- Identify leadership only when supported by evidence
- Return missing optional information as `null` or an empty list
- Include source URLs where available

## Confidence Score

Each company receives a confidence score between `0.0` and `1.0`.

Example:

```json
{
  "confidence_score": 0.8
}
```

The score is validated using Pydantic.

## React Dashboard

The React interface provides:

- Company domain search
- Enrich Lead button
- Company overview
- Target audience
- Public emails
- Leadership/team information
- Confidence score
- Processed companies table

The dashboard communicates with the FastAPI backend to perform live enrichment.

## Design Principles

### Evidence First

The system prioritizes information supported by public sources instead of guessing.

### Structured Output

Pydantic validation keeps AI-generated results consistent and predictable.

### Graceful Failure

Individual page or extraction failures do not terminate the complete process.

### Modular Architecture

The system separates:

- Crawling
- Content cleaning
- Deterministic extraction
- LLM extraction
- Validation
- API
- Frontend

## Future Improvements

- External search integration
- LinkedIn profile discovery
- Token and API cost tracking
- Concurrent website crawling
- Database storage
- Excel export
- Authentication
- Lead history and analytics

## Assignment Deliverables

The project includes:

- Modular Python implementation
- Playwright-based web crawling
- Dynamic website handling
- Content cleaning
- Deterministic extraction
- LLM structured extraction
- Pydantic validation
- Error handling and fallback logic
- Sample JSON output
- CSV output
- FastAPI backend
- React frontend
- Project documentation

## Author

**Hari Krishna R.**

B.E. Civil Engineering — 2025 Graduate

### Focus Areas

- Python
- Full Stack Development
- Artificial Intelligence
- Machine Learning
- Generative AI
- AI Agents

### LinkedIn

https://www.linkedin.com/in/hari-krishna-r-a9a09823a/

## License

This project was created as a technical assignment and demonstration of an autonomous AI-powered lead enrichment workflow.
