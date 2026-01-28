CareGuide – Action-Oriented Medical Triage PoC
==============================================

CareGuide is a rule-based, explainable medical triage service that helps users
decide WHERE to seek care, HOW urgently to act, and WHAT information to prepare,
based on self-reported symptoms.

This project does NOT diagnose diseases.
It provides symptom pattern recognition, urgency assessment, and evidence-based
medical guidance suitable for hospital PoCs, internal ventures, and early validation.

UI (Result)
------------------
Users can input their symptoms to receive an assessment and guidance on appropriate next actions.

<img width="440" height="1154" alt="작업 결과01" src="https://github.com/user-attachments/assets/5b70120c-59a9-4878-8e22-4552b04956f6" />

Project Philosophy
------------------

CareGuide is intentionally designed around the following principles:

- Diagnosis is NOT the goal
- Actionable guidance IS the goal
- Rules come first, AI is optional
- Every decision must be explainable
- Medical and legal safety take priority

Instead of predicting diseases, CareGuide identifies
"clinical symptom patterns" and recommends appropriate next actions.


What This Service Does
----------------------

- Identifies symptom patterns (e.g., right lower quadrant abdominal pain pattern)
- Estimates urgency level (emergency / urgent / routine / observe)
- Recommends appropriate departments (e.g., Surgery, ER, Internal Medicine)
- Provides concrete next actions for users
- Supplies medical literature references for clinicians
- Explains why a certain action is recommended


## Project Technical Specification

### Backend
- **Framework**: FastAPI (Python)
- **API Style**: RESTful API
- **Schema Validation**: Pydantic
- **Architecture Pattern**:
  - Rule-based decision engine 중심
  - Deterministic logic 우선 설계 (LLM 의존 최소화)

---

### Core Logic
#### Rule-Based Triage Engine
- Keyword / symptom pattern matching
- Explicit medical rules (if-then, weighted rules)

**Outputs**
- Urgency level (`emergency / urgent / routine / observe`)
- Recommended next action
- Pattern-based labels (non-diagnostic)
- Explainable decision output (matched rules exposed)

---

### Retrieval (RAG-style, Optional)
#### Evidence Retrieval Module
- PubMed 기반 문헌 검색
- 목적: 판단 보조 및 근거 제시 (Decision-making 아님)
- Rule 결과를 검색 쿼리로 활용하는 구조

#### RAG Characteristics
- Retrieval-augmented explanation
- Deterministic rule output + external evidence reference

What This Service Does NOT Do
-----------------------------

- Does NOT provide medical diagnosis
- Does NOT provide treatment or prescriptions
- Does NOT replace medical professionals
- Is NOT a certified medical device


Key Features
------------

1. Rule-Based Triage Engine
   - Explicit medical rules with keyword gating
   - Confidence scores based on rule weight (NOT probabilities)
   - Safe, deterministic behavior preferred by hospitals

2. Action-Oriented Output
   - Urgency level (emergency / urgent / routine / observe)
   - Clear next actions instead of vague labels
   - Example:
     "Right lower quadrant acute abdominal pain pattern
      – evaluation today is recommended"

3. Pattern-Based Labels (Not Diagnoses)
   - Uses expressions like:
     "appendicitis-like pattern" instead of "appendicitis"
   - Reduces legal and ethical risk

4. Explainability
   - Shows matched keywords and rule evidence
   - Rule IDs exposed for audit and clinician review
   - Candidate rules available for clinician mode

5. PubMed RAG (Research Support)
   - Retrieves relevant guidelines, reviews, and clinical papers
   - Used to support reasoning, not to make decisions
   - Retrieval logic is explainable and rule-aware

6. Mobile-First UI
   - Optimized for iOS WebView and mobile browsers
   - Patient mode vs clinician mode separation


System Architecture
-------------------

User Input (Free Text)
        ↓
Rule-Based Triage Engine
        ↓
Urgency & Action Determination
        ↓
Evidence-Aware PubMed Retrieval
        ↓
Explainable, Actionable Response


Project Structure
-----------------

medical-llm-poc/
  backend/
    main.py                 FastAPI entry point
    schemas.py              Request / response schemas
    pubmed_rag.py           Evidence retrieval (RAG-style, PoC)
    triage/
      rule_based.py         Rule engine (patterns, urgency, actions)
      __init__.py

  frontend/
    index.html              Mobile-first demo UI

  README.txt


API Output (Example)
-------------------

User input:
"Right lower abdominal pain"

Response:
- Pattern:
  "Right lower quadrant acute abdominal pain pattern
   (possible surgical evaluation needed)"

- Urgency level:
  urgent

- Recommended departments:
  Surgery, Emergency Medicine

- Next actions:
  - Seek surgical or emergency evaluation today
  - Visit ER immediately if fever, vomiting, worsening pain, or rebound tenderness occur
  - Prepare symptom timeline for clinician

- Confidence:
  0.78 (heuristic confidence, NOT diagnostic probability)

- Research basis:
  Clinical reviews and guidelines related to acute abdominal pain


Why Rule-Based First?
--------------------

Hospitals and medical institutions prefer systems that are:

- Explainable
- Auditable
- Deterministic
- Legally defensible

CareGuide starts with rules to ensure safety and trust.
AI models (LLMs, embeddings) may later be added ONLY as
support tools (e.g., symptom normalization), never as final decision-makers.


Futur
