Citation Verifier — Implementation Plan
SanD Hacks 2026 | AGNTCY Track | UCSD CSES | Jan 31 - Feb 1

---
Overview

A multi-agent citation verification system built on the AGNTCY App SDK. Users submit text through
a Flask web frontend. A supervisor agent orchestrates a team of specialized agents — a parser agent
extracts citations, verifier agents check sources in parallel via broadcast, and an analyst agent
scores claims against source content. The system produces a hallucination report with per-citation
confidence scores.

This is a multi-agent system (not a monolithic app). Each agent is an independent process that
communicates via the A2A (Agent-to-Agent) protocol over the SLIM message bus. The AGNTCY broadcast
pattern handles parallel verification natively — no ThreadPoolExecutor needed.

---
Why Multi-Agent? (Hackathon Framing)

The Citation Verifier is a natural fit for multi-agent architecture:

1. Parallel verification: Each API (CrossRef, Semantic Scholar, etc.) is an independent agent.
   The supervisor broadcasts a citation to all verifiers simultaneously and aggregates results.
   This solves the "Waiting Room" concurrency problem by design.

2. Modularity: Adding a new data source means adding a new agent — no changes to existing code.
   A new team member could build a PubMed verifier agent without touching anything else.

3. Failure isolation: If the Semantic Scholar agent crashes, the other verifiers keep running.
   The supervisor collects whatever results come back.

4. Observability: AGNTCY's IOA Observe SDK gives OTEL-based tracing across all agents — you can
   see exactly which verifier found what, how long each took, and where failures occurred.

Hackathon level mapping:
- Level 1: Get the system running, understand agent roles, modify verifier behavior
- Level 2: Add new verifier agents, implement the broadcast verification pattern
- Level 3: LLM-based semantic analysis agent, agent coordination patterns, observability

---
Known Challenges & Solutions

1. The "Waiting Room" Problem (Concurrency)

Problem: If verification runs sequentially, 10 citations at 5 seconds each = 50 second hang.

Solution: The AGNTCY broadcast pattern. The Supervisor agent broadcasts each citation to all
Verifier agents simultaneously using client.broadcast_message(). Each verifier runs as its own
process and responds independently. Results stream back as they arrive.

This replaces ThreadPoolExecutor entirely — concurrency is handled at the infrastructure level
by the SLIM message bus, not in application code.

2. The "Nuance" Problem (Semantic Gap)

Problem: TF-IDF is a "bag of words" model. "The study disproved X" vs "The study proved X" gets
a high TF-IDF match despite opposite meanings.

Solution: The Analyst agent uses LLM-based semantic comparison as its PRIMARY strategy. The LLM
judges whether a source supports, contradicts, or is unrelated to a claim — catching negation,
paraphrasing, and misrepresentation. TF-IDF is the fallback when no LLM API key is provided, with
a warning on the report that results are less accurate.

---
Architecture

User pastes text -> Flask web frontend (app.py)
  -> Sends text to Supervisor Agent via A2A
  -> Supervisor sends text to Parser Agent (direct A2A)
  <- Parser returns structured citations
  -> For each citation, Supervisor broadcasts to all Verifier Agents:
       [CrossRef] [Semantic Scholar] [Unpaywall] [OpenLibrary] [Web]
  <- Each verifier responds with what it found (parallel, via SLIM)
  -> Supervisor sends citation + source data to Analyst Agent (direct A2A)
  <- Analyst returns confidence scores + match results
  -> Supervisor compiles final report
  <- Report returned to Flask frontend -> rendered for user

Communication patterns used:
  - Direct A2A: Flask <-> Supervisor, Supervisor <-> Parser, Supervisor <-> Analyst
  - Broadcast:  Supervisor -> all Verifier agents (parallel, aggregated responses)

Infrastructure:
  - SLIM message bus (runs in Docker) — handles all inter-agent messaging
  - Each agent is a separate Python process with its own A2A server
  - docker-compose.yaml orchestrates everything

---
Project Structure

Citation Verifier/
  ├── app.py                          # Flask web frontend + A2A client to Supervisor
  ├── requirements.txt                # Python dependencies
  ├── config.py                       # Shared configuration (API keys, endpoints, LLM settings)
  ├── .env.example                    # Template for environment variables
  ├── docker-compose.yaml             # SLIM message bus + all agent services
  │
  ├── agents/
  │   ├── common/                     # Shared utilities across agents
  │   │   ├── __init__.py
  │   │   ├── llm_config.py           # LiteLLM / LLM provider setup
  │   │   └── models.py               # Shared Pydantic models (Citation, VerificationResult, etc.)
  │   │
  │   ├── supervisor/                 # Orchestrator agent (LangGraph workflow)
  │   │   ├── __init__.py
  │   │   ├── card.py                 # AgentCard for the supervisor
  │   │   ├── graph/
  │   │   │   ├── __init__.py
  │   │   │   ├── graph.py            # LangGraph: parse -> broadcast verify -> analyze -> report
  │   │   │   ├── tools.py            # A2A broadcast tool, direct A2A call tools
  │   │   │   └── models.py           # Supervisor state model
  │   │   └── main.py                 # Entry point: create server, bind transport, start
  │   │
  │   ├── parser/                     # Citation extraction agent
  │   │   ├── __init__.py
  │   │   ├── card.py                 # AgentCard
  │   │   ├── agent.py                # Regex + heuristics citation parsing logic
  │   │   ├── agent_executor.py       # A2A protocol bridge
  │   │   └── server.py               # Server startup
  │   │
  │   ├── verifiers/                  # One sub-folder per verifier agent
  │   │   ├── crossref/
  │   │   │   ├── __init__.py
  │   │   │   ├── card.py             # AgentCard for CrossRef verifier
  │   │   │   ├── agent.py            # CrossRef API logic
  │   │   │   ├── agent_executor.py   # A2A bridge
  │   │   │   └── server.py           # Server startup
  │   │   ├── semantic_scholar/
  │   │   │   ├── __init__.py
  │   │   │   ├── card.py
  │   │   │   ├── agent.py
  │   │   │   ├── agent_executor.py
  │   │   │   └── server.py
  │   │   ├── unpaywall/
  │   │   │   ├── __init__.py
  │   │   │   ├── card.py
  │   │   │   ├── agent.py
  │   │   │   ├── agent_executor.py
  │   │   │   └── server.py
  │   │   ├── openlibrary/
  │   │   │   ├── __init__.py
  │   │   │   ├── card.py
  │   │   │   ├── agent.py
  │   │   │   ├── agent_executor.py
  │   │   │   └── server.py
  │   │   └── web/
  │   │       ├── __init__.py
  │   │       ├── card.py
  │   │       ├── agent.py
  │   │       ├── agent_executor.py
  │   │       └── server.py
  │   │
  │   └── analyst/                    # Content matching + confidence scoring agent
  │       ├── __init__.py
  │       ├── card.py                 # AgentCard
  │       ├── agent.py                # LLM semantic analysis (primary) + TF-IDF (fallback)
  │       ├── agent_executor.py       # A2A bridge
  │       └── server.py               # Server startup
  │
  ├── templates/
  │   ├── index.html                  # Main page — text input form
  │   ├── processing.html             # Polling page while agents work
  │   └── report.html                 # Results page — hallucination report
  │
  └── static/
      └── style.css                   # Custom styles (Tailwind via CDN for most styling)

Each agent follows the AGNTCY 4-file pattern (modeled after CoffeeAGNTCY):
  card.py          — AgentCard (identity, capabilities, skills)
  agent.py         — Core logic (API calls, LLM calls, business rules)
  agent_executor.py — A2A protocol bridge (request/response handling)
  server.py        — Server startup and SLIM transport binding

---
Dependencies (requirements.txt)

# AGNTCY framework
agntcy-app-sdk>=0.4.1      # Core factory, transport, protocol abstractions
a2a>=0.3.0                 # Agent-to-Agent protocol types and server framework
langgraph>=0.4.1           # Stateful agent workflow orchestration (for supervisor)
langchain-core             # LLM integration, tool definitions
litellm                    # Multi-provider LLM abstraction

# Web frontend
flask>=3.0
uvicorn                    # ASGI server (for agent servers)

# Verification APIs
requests>=2.31
beautifulsoup4>=4.12
lxml>=5.0

# Content analysis
scikit-learn>=1.3          # TF-IDF + cosine similarity (fallback)
anthropic>=0.40            # Claude API for LLM content matching (optional but recommended)
openai>=1.0                # OpenAI API alternative (optional)

# Utilities
python-dotenv>=1.0
pydantic>=2.0              # Data models for agent messages

# Observability (optional)
ioa-observe>=1.0           # AGNTCY OTEL-based tracing

# Browser agent (optional)
playwright>=1.40

Infrastructure requirements:
- Python 3.12+
- Docker + Docker Compose (for SLIM message bus)
- An LLM provider API key (OpenAI, Anthropic, GROQ, or Azure — via LiteLLM)

Free APIs (no key required):
- CrossRef REST API — paper metadata by DOI, title search
- Semantic Scholar API — paper abstracts, references, full metadata
- Unpaywall API — find open-access PDF links (requires email, free)
- OpenLibrary API — book metadata by ISBN/title

---
AGNTCY Concepts Used

1. AgentCard — Every agent declares its identity, capabilities, and skills via a card.
   The supervisor uses cards to discover and address other agents.

2. AgentExecutor — Each agent implements an executor that bridges between the agent's
   core logic and the A2A protocol. Handles request parsing and response formatting.

3. AppSession / AppContainer — The server-side lifecycle. Each agent creates an AppSession,
   adds itself as an AppContainer with a SLIM transport binding, and starts listening.

4. A2A Protocol — Agent-to-Agent communication. Messages are typed (TextPart, DataPart, etc.)
   with roles (user/agent) and tasks that track state.

5. SLIM Transport — Secure Low-Latency Interactive Messaging. The message bus that routes
   messages between agents. Supports point-to-point, broadcast (pub-sub), and group chat.

6. Broadcast Pattern — The supervisor sends the same message to multiple agents at once
   and collects all responses. Used for parallel citation verification.

Key code pattern (how the supervisor broadcasts to verifiers):

  from agntcy_app_sdk.factory import AgntcyFactory
  from agntcy_app_sdk.semantic.a2a.protocol import A2AProtocol

  # Resolve each verifier agent's topic from its card
  verifier_topics = [
      A2AProtocol.create_agent_topic(card)
      for card in [crossref_card, semantic_scholar_card, unpaywall_card,
                   openlibrary_card, web_card]
  ]

  # Broadcast the citation to all verifiers simultaneously
  responses = await client.broadcast_message(
      message=verify_request,
      recipients=verifier_topics,
      broadcast_topic="citation_verification",
  )
  # responses contains one result per verifier — aggregate them

---
Implementation Steps (in order)

Step 1: Project Scaffolding + SLIM Setup

- Create directory structure with agents/ sub-folders
- Write requirements.txt, config.py, .env.example
- Create docker-compose.yaml with SLIM message bus service
- Verify SLIM starts: docker compose up slim
- Set up Flask app with basic routes (GET /, POST /verify)
- Create templates/index.html with text input form (Tailwind CDN)
- Create agents/common/models.py with shared Pydantic models:
    Citation(type, raw_text, doi, url, isbn, title, authors, year)
    VerificationResult(source, found, metadata, content_snippet, confidence)

Step 2: First Agent — Parser Agent (agents/parser/)

Build the parser as a standalone AGNTCY agent to learn the pattern:

card.py:
  - name: "Citation Parser Agent"
  - skills: ["parse_citations"]
  - description: "Extracts citations from academic text"

agent.py — Core parsing logic:
  - DOI patterns: 10.XXXX/... or doi.org/10.XXXX/...
  - URLs: http(s)://...
  - APA style: Author (Year). Title. Journal, Vol(Issue), Pages.
  - MLA style: Author. "Title." Journal, vol. X, no. X, Year, pp. X-X.
  - Inline references: (Author, Year) or [1] numbered refs with bibliography
  - ISBN patterns: ISBN 978-...
  - Each citation tagged: doi, url, book, paper, unknown

agent_executor.py — A2A bridge:
  - Receives text via A2A message
  - Calls agent.parse(text)
  - Returns list of Citation objects as A2A response

server.py — Startup:
  - Creates AgntcyFactory
  - Creates SLIM transport
  - Binds AppSession and starts listening

Test: Send a message to the parser agent and verify it returns structured citations.

Step 3: Verifier Agents (agents/verifiers/)

Each verifier follows the same 4-file pattern. They all receive a Citation via A2A
and return a VerificationResult.

3a. CrossRef verifier (agents/verifiers/crossref/)
  - Query https://api.crossref.org/works/{doi} for DOI lookups
  - Query https://api.crossref.org/works?query.bibliographic=... for title search
  - Extract: title, authors, journal, year, abstract
  - Rate limit: be polite, include mailto: in User-Agent

3b. Semantic Scholar verifier (agents/verifiers/semantic_scholar/)
  - Query https://api.semanticscholar.org/graph/v1/paper/{doi_or_id}
  - Get abstract, citation count, references, TL;DR
  - Fallback title search via /paper/search?query=...

3c. Unpaywall verifier (agents/verifiers/unpaywall/)
  - Query https://api.unpaywall.org/v2/{doi}?email=...
  - Find open-access PDF/HTML URLs for papers behind paywalls

3d. OpenLibrary verifier (agents/verifiers/openlibrary/)
  - Query https://openlibrary.org/api/books?bibkeys=ISBN:...
  - Query https://openlibrary.org/search.json?title=...
  - Extract: title, authors, publisher, year

3e. Web URL verifier (agents/verifiers/web/)
  - HTTP GET the URL, check status code (200 = exists)
  - Extract page content with BeautifulSoup
  - Handle redirects, timeouts, 404s

Step 4: Supervisor Agent (agents/supervisor/)

The orchestrator. Uses LangGraph to define the workflow.

card.py:
  - name: "Citation Verification Supervisor"
  - skills: ["verify_text"]

graph/graph.py — LangGraph workflow:
  1. Receive text from Flask app
  2. Call Parser Agent (direct A2A) -> get list of citations
  3. For each citation, broadcast to all Verifier Agents -> aggregate results
  4. Call Analyst Agent (direct A2A) with citation + verification results -> get scores
  5. Compile final report
  6. Return report to Flask app

graph/tools.py — A2A tools available to the graph:
  - parse_citations_tool: direct A2A call to Parser Agent
  - verify_citation_tool: broadcast to all Verifier Agents
  - analyze_citation_tool: direct A2A call to Analyst Agent

graph/models.py — Supervisor state:
  - text: str (user input)
  - citations: list[Citation]
  - verification_results: dict[citation_id -> list[VerificationResult]]
  - analysis_results: dict[citation_id -> AnalysisResult]
  - report: dict (final structured report)

Step 5: Analyst Agent (agents/analyst/)

Receives a citation, its claim context, and verification results. Returns confidence score.

agent.py — Two-tier content matching:

  Tier 1 — LLM Semantic Analysis (primary, requires API key):
  1. Extract the claim sentence(s) surrounding the citation
  2. Collect source content from verification results (abstracts, full text, page content)
  3. Send both to LLM (via LiteLLM) with prompt:
     - Does the source support, contradict, or have no relation to the claim?
     - Is there negation, exaggeration, or misrepresentation?
  4. Parse response: supported / contradicted / unrelated / insufficient_source
  5. Catches: negation ("proved" vs "disproved"), paraphrasing, partial truths

  Tier 2 — TF-IDF + Cosine Similarity (fallback, no API key needed):
  1. TfidfVectorizer on claim + source content
  2. Cosine similarity: >0.3 = supported, 0.1-0.3 = weak, <0.1 = not supported
  3. WARNING displayed on report: less reliable without LLM

Confidence scoring (0-100) per citation:

  | Factor             | Weight (LLM) | Weight (TF-IDF fallback) |
  |--------------------|--------------|--------------------------|
  | Source exists       | 30%          | 40%                      |
  | Metadata match      | 20%          | 25%                      |
  | Content similarity  | 35%          | 20% (less trustworthy)   |
  | Source quality      | 15%          | 15%                      |

Step 6: Flask Frontend + Supervisor Client (app.py)

Flask serves the web UI and acts as an A2A client to the Supervisor agent.

Routes:
  - GET /             — render index.html (text input form)
  - POST /verify      — send text to Supervisor via A2A, get job/task ID, redirect to processing
  - GET /status/<id>  — query Supervisor task status via A2A, return JSON
  - GET /report/<id>  — render report.html with completed results

Frontend:
  - templates/index.html: Tailwind CSS, text area, submit button, LLM mode toggle
  - templates/processing.html: Progress bar, polls /status/<id> every 2 seconds via JS
  - templates/report.html: Overall score (color-coded), per-citation cards (expandable),
    analysis mode indicator (LLM vs TF-IDF), export as JSON button

Step 7: Docker Compose + Integration

docker-compose.yaml runs everything:
  - slim: SLIM message bus gateway (port 46357)
  - parser: Parser Agent
  - crossref: CrossRef Verifier Agent
  - semantic-scholar: Semantic Scholar Verifier Agent
  - unpaywall: Unpaywall Verifier Agent
  - openlibrary: OpenLibrary Verifier Agent
  - web-verifier: Web URL Verifier Agent
  - analyst: Analyst Agent
  - supervisor: Supervisor Agent
  - web: Flask frontend (port 5000)

Each agent service runs its own server.py. All connect to SLIM on the same network.

Step 8: Error Handling & Observability

- Rate limiting: delays between API calls, respect CrossRef etiquette
- Timeouts: 10s per API call, 30s per broadcast response window
- Graceful degradation: if a verifier agent is down, supervisor uses partial results
- Caching: verifier agents cache API responses locally
- Observability: IOA Observe decorators on agent methods for OTEL tracing
- Health checks: each agent exposes a health endpoint, docker-compose uses them

---
Verification / Testing Plan

1. Unit test the parser agent with sample texts in APA, MLA, Chicago formats
2. Test each verifier agent individually: send a known Citation, check VerificationResult
3. Test the broadcast pattern: supervisor sends one citation, all verifiers respond
4. Test the analyst with adversarial pairs (negation, paraphrasing, unrelated sources)
5. End-to-end: submit text with real + fake citations, verify report flags the fakes correctly
6. Failure test: kill one verifier agent, confirm the system still produces partial results
7. Run locally: docker compose up, open http://localhost:5000, submit text, see report

---
Development Phases — 2-Person Team

Person A: Experienced programmer (AGNTCY framework, agent wiring, LLM integration, supervisor)
Person B: Inexperienced programmer (individual agent logic, frontend, testing)

Both work side by side. Person A sets up the framework and mentors Person B on the agent pattern.
Person B builds real agents from the start by following the template Person A creates.

............................................................................

PHASE 1 — Scaffolding + First Agent (together, sit side by side)
Goal: One working agent communicating over SLIM. Prove the pattern works.

  Person A:
    - Set up project structure, requirements.txt, config.py, .env.example
    - Write docker-compose.yaml with SLIM message bus
    - Build the Parser Agent end-to-end as the REFERENCE IMPLEMENTATION:
      card.py, agent.py, agent_executor.py, server.py
      (This becomes the template Person B copies for every other agent)
    - Write agents/common/models.py (Citation, VerificationResult, AnalysisResult)
    - Write a simple test client that sends text to the Parser Agent and prints results
    - Set up Flask app.py skeleton (GET /, POST /verify — stub that just returns "coming soon")

  Person B:
    - Create all __init__.py files across the entire project
    - Build templates/index.html (Tailwind CDN, text area, "Verify Citations" button)
    - Build templates/report.html with hardcoded example data (get the layout right)
    - Build templates/processing.html with a progress bar placeholder
    - Build static/style.css
    - Run the CoffeeAGNTCY tutorial to understand the AGNTCY agent pattern
      (https://github.com/agntcy/coffeeAgntcy/blob/main/TUTORIAL.md)

  Checkpoint:
    - docker compose up starts SLIM + Parser Agent
    - Person A's test client sends text to the Parser Agent and gets citations back
    - Person B can open Flask app in browser and see the input form + placeholder report

............................................................................

PHASE 2 — Verifier Agents (parallel work, Person B copies the pattern)
Goal: All 5 verifiers running as independent agents.

  Person A:
    - Build agents/verifiers/crossref/ (most complex API, DOI + bibliographic search)
    - Build agents/verifiers/semantic_scholar/ (second API, careful error handling)
    - Build agents/verifiers/unpaywall/ (DOI-dependent flow)
    - Add all three to docker-compose.yaml
    - Write a broadcast test: send one citation to all available verifiers, print results

  Person B:
    - Build agents/verifiers/openlibrary/ (simplest API — copy parser's 4-file structure,
      replace the logic with OpenLibrary API calls. Person A pair-reviews.)
    - Build agents/verifiers/web/ (HTTP GET + BeautifulSoup — Person A reviews error handling)
    - Add both to docker-compose.yaml
    - Test each verifier individually with known DOIs, ISBNs, URLs
    - Document what each verifier returns (helps with report template later)

  Checkpoint:
    - docker compose up starts SLIM + all 5 verifier agents
    - Person A's broadcast test sends a citation and gets responses from all 5
    - Person B has tested each verifier with real data

............................................................................

PHASE 3 — Supervisor + Analyst (Person A leads, Person B supports)
Goal: Full pipeline working end-to-end.

  Person A:
    - Build agents/supervisor/ with LangGraph workflow:
      parse -> broadcast verify -> analyze -> report
    - Build graph/tools.py with A2A broadcast and direct call tools
    - Build agents/analyst/ with LLM (Tier 1) + TF-IDF (Tier 2) content matching
    - Wire Flask app.py as A2A client to Supervisor
    - Implement /verify, /status/<id>, /report/<id> routes

  Person B:
    - Build the report generation logic inside the analyst agent or as a utility
      (Person A defines the data format, Person B implements the dict -> template mapping)
    - Update templates/report.html to render real data:
      overall score with color coding, per-citation cards, analysis mode indicator
    - Add "export as JSON" button on report page
    - Write JavaScript polling logic for processing.html:
      POST /verify -> get ID -> poll /status/<id> -> redirect to /report/<id>

  Checkpoint:
    - docker compose up starts the full system (SLIM + 8 agents + Flask)
    - Submit text with real and fake citations -> get a real hallucination report
    - The broadcast pattern runs all verifiers in parallel — no timeout issues

............................................................................

PHASE 4 — Polish, Observability & Demo Prep (together)
Goal: Make it demo-ready. Add observability. Handle edge cases.

  Person A:
    - Add IOA Observe tracing to key agent methods (shows verification flow in traces)
    - Add graceful degradation: supervisor handles missing/crashed verifier agents
    - Add rate limiting and caching in verifier agents
    - Review all error handling paths

  Person B:
    - Polish the frontend: loading states, error messages, responsive design
    - Write end-to-end test cases:
      * Text with all real citations (expect high scores)
      * Text with all fake citations (expect low scores / flagged)
      * Mixed real and fake (expect correct identification)
      * Negation/contradiction text (test LLM vs TF-IDF accuracy)
    - Test killing individual verifier containers to confirm graceful degradation
    - Prepare demo script: what text to paste, what to show judges

  Checkpoint:
    - Full system is robust and demo-ready
    - Observability traces show the multi-agent coordination
    - Test cases documented and passing

............................................................................

PHASE 5 (STRETCH) — Browser Agent + Advanced Patterns
Goal: Optional enhancements if there is time remaining.

  Person A:
    - Build a Playwright-based Browser Agent for institutional access (opt-in)
    - Explore group chat pattern: verifier agents discuss conflicting results
    - Explore agent trust scoring (weight results by verifier reliability)

  Person B:
    - Add browser agent toggle to index.html
    - Add a "detailed view" mode to report.html showing which verifier found what
    - Build a visualization of the agent communication flow (which agents talked, in what order)

---
Key AGNTCY Resources

- AGNTCY Repo: https://github.com/agntcy
- App SDK: https://github.com/agntcy/app-sdk
- CoffeeAGNTCY (reference app): https://github.com/agntcy/coffeeAgntcy
- Getting Started Tutorial: https://github.com/agntcy/coffeeAgntcy/blob/main/TUTORIAL.md
- YouTube Tutorials:
    https://www.youtube.com/watch?v=CJ-02iKJxw4
    https://www.youtube.com/watch?v=1QE5KL69sag
    https://www.youtube.com/watch?v=kCAe8gHqJ9g

---
Files to Create (in implementation order)

1.  requirements.txt
2.  config.py + .env.example
3.  docker-compose.yaml
4.  agents/common/__init__.py + agents/common/models.py + agents/common/llm_config.py
5.  agents/parser/card.py + agent.py + agent_executor.py + server.py
6.  app.py (Flask skeleton)
7.  templates/index.html
8.  agents/verifiers/crossref/card.py + agent.py + agent_executor.py + server.py
9.  agents/verifiers/semantic_scholar/card.py + agent.py + agent_executor.py + server.py
10. agents/verifiers/unpaywall/card.py + agent.py + agent_executor.py + server.py
11. agents/verifiers/openlibrary/card.py + agent.py + agent_executor.py + server.py
12. agents/verifiers/web/card.py + agent.py + agent_executor.py + server.py
13. agents/analyst/card.py + agent.py + agent_executor.py + server.py
14. agents/supervisor/card.py + graph/graph.py + graph/tools.py + graph/models.py + main.py
15. templates/processing.html
16. templates/report.html
17. static/style.css
