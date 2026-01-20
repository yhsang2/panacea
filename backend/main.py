from typing import Any, Dict, List
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from schemas import SymptomRequest
from triage.rule_based import rule_based_triage
from pubmed_rag import search_pubmed

app = FastAPI(title="CareGuide API")

# PoC: allow all origins (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def llm_explain(symptoms: str, triage_result: dict) -> str:
    # PoC: explanation text (replace with real LLM later)
    return (
        f"입력하신 증상(\"{symptoms}\")은 "
        f"\"{triage_result['condition_key']}\" 범주에서 흔히 보고되는 패턴과 일부 유사합니다. "
        "정확한 진단은 의료진의 대면 평가가 필요하며, "
        "증상이 악화되거나 응급 징후가 나타나면 즉시 의료기관을 방문하세요."
    )


def normalize_candidate(c: Dict[str, Any]) -> Dict[str, Any]:
    """
    FastAPI jsonable_encoder에서 RecursionError가 나지 않도록
    candidates 내부에 candidates(중첩/순환 가능)를 제거한 얕은 복사본을 반환.
    """
    c = dict(c)
    c.pop("candidates", None)  # ✅ nested candidates 제거
    return c


@app.post("/triage")
def triage(req: SymptomRequest):
    # include_candidates=True: 의료진 모드에서 후보 규칙 목록 확인 가능
    triage_result = rule_based_triage(req.symptoms, include_candidates=True)

    # PubMed RAG (mock)
    papers = search_pubmed(
        triage_result["condition_key"],
        symptoms_text=req.symptoms,
        evidence=triage_result.get("evidence", {}),  # ✅ dict OK
        top_k=5
    ) or []
    for p in papers:
        if isinstance(p, dict) and "url" not in p:
            p["url"] = f"https://pubmed.ncbi.nlm.nih.gov/?term={triage_result['condition_key']}"

    explanation = llm_explain(req.symptoms, triage_result)

    # ✅ RecursionError 방지: candidates를 정규화해서 반환
    raw_candidates = triage_result.get("candidates") or []
    safe_candidates: List[Dict[str, Any]] = [
        normalize_candidate(c) for c in raw_candidates if isinstance(c, dict)
    ]

    return {
        "suspected_conditions": triage_result["suspected_conditions"],
        "recommended_departments": triage_result["recommended_departments"],
        "emergency": triage_result["emergency"],
        "urgency_level": triage_result["urgency_level"],
        "action_reason": triage_result["action_reason"],
        "next_actions": triage_result["next_actions"],
        "confidence": triage_result["confidence"],
        "confidence_label": triage_result["confidence_label"],
        "rule_id": triage_result["rule_id"],
        "evidence": triage_result.get("evidence", {}),
        "candidates": safe_candidates,
        "research_basis": papers,
        "llm_explanation": explanation,
        "disclaimer": (
            "본 서비스는 의료 진단/처방을 제공하지 않습니다. "
            "의료 정보 정리 및 트리아지(어디로 가면 좋을지) 참고용입니다."
        ),
    }
