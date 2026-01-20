CareGuide – Medical Triage PoC
==============================

CareGuide is an explainable, rule-based medical triage service designed to guide users
to the appropriate medical department based on self-reported symptoms.

This project intentionally does NOT provide medical diagnosis or treatment.
It focuses on triage, safety, explainability, and regulatory readiness, making it
suitable for hospital PoCs, internal ventures, and early-stage validation.


Key Features
------------

- Rule-based Medical Triage
  Explicit and auditable clinical rules with clear separation between
  medical logic and API orchestration.

- Rule Weight & Confidence Score
  Each rule has a clinical risk weight.
  A heuristic confidence score (0–1) is provided.
  This score is NOT a diagnostic probability.
  Human-readable labels are included: High / Medium / Low.

- Explainability by Design
  Keyword matching evidence is included in responses.
  Rule IDs are exposed for auditing and medical review.
  Candidate rule lists are available for clinician use.

- PubMed RAG Integration (PoC)
  Relevant medical literature references are returned.
  Direct links to PubMed search results are provided.

- Mobile-first UI
  Optimized for iOS WebView and mobile browsers.
  Patient mode and clinician mode are clearly separated.

- Medical & Legal Safety
  No diagnosis or prescription.
  Clear medical disclaimers.
  Rule-first architecture (AI usage is optional and controlled).


Why Rule-Based First?
--------------------

Hospitals and medical institutions strongly prefer systems that are:

- Explainable
- Auditable
- Deterministic
- Legally defensible

CareGuide intentionally starts with a rule-based triage engine.
AI models are positioned only as optional assistants, never as
final decision-makers.


Architecture Overview
---------------------

User Input
  ↓
Rule-based Triage Engine
  ↓
Confidence Scoring & Safety Checks
  ↓
PubMed Reference Retrieval
  ↓
Structured, Explainable Response

AI models (LLMs or embeddings) may later be added only as
input normalization or support layers.


Project Structure
-----------------

medical-llm-poc/
  backend/
    main.py                 FastAPI entry point
    schemas.py              Request/Response models
    pubmed_rag.py           PubMed reference retrieval (PoC)
    triage/
      rule_based.py         Rule engine with weight & confidence
      __init__.py

  frontend/
    index.html              Mobile-first UI

  README.txt


Getting Started
---------------

1. Backend

cd backend
pip install -r requirements.txt
uvicorn main:app --reload

API documentation:
http://127.0.0.1:8000/docs


2. Frontend

Open the following file in a browser or mobile WebView:

frontend/index.html


API Response Example
--------------------

suspected_conditions:
  ["Acute pharyngitis is suspected"]

recommended_departments:
  ["Otolaryngology"]

emergency:
  false

confidence:
  0.72

confidence_label:
  Medium

rule_id:
  acute_pharyngitis

evidence:
  gate_matched: ["throat"]
  support_matched: ["pain", "swallowing"]
  support_ratio: 0.4
  weight: 0.65

candidates:
  [...]

research_basis:
  [...]

llm_explanation:
  Textual explanation for users and clinicians.

disclaimer:
  This service does not provide medical diagnosis or treatment.


Important Disclaimer
--------------------

This project:

- Does NOT provide medical diagnosis
- Does NOT provide prescriptions or treatment plans
- Is NOT a medical device

It is intended only for medical information organization
and triage guidance.


Future Roadmap
--------------

- LLM-based symptom normalization (safe NLP layer)
- Embedding-based rule matching enhancement
- Clinician rule management UI
- Rule performance analytics and tuning
- Hospital EMR integration (read-only)


License
-------

This project is provided for research, PoC, and internal evaluation purposes.
Before production or public deployment, ensure compliance with
local medical regulations.


Acknowledgements
----------------

- PubMed / NCBI for medical literature access
- FastAPI open-source ecosystem


CareGuide
Explainable. Safe. Clinically Responsible.
