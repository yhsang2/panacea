from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
from functools import lru_cache
import re
import json


# =============================
# 1) Models
# =============================
@dataclass(frozen=True)
class EvidenceDoc:
    doc_id: str
    title: str
    source: str                 # "PubMed", "NICE", "WHO", "CDC", etc.
    doc_type: str               # "guideline" | "review" | "clinical" | "emergency" | "systematic"
    year: int
    journal_or_org: str
    abstract_or_summary: str
    conditions: List[str]
    keywords: List[str]
    pubmed_query: Optional[str] = None
    url: Optional[str] = None


# =============================
# 2) Text utilities
# =============================
def _norm(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokenize(s: str) -> List[str]:
    s = _norm(s)
    parts = re.split(r"[^0-9a-z가-힣]+", s)
    return [p for p in parts if len(p) >= 2]


def _dedupe_keep_order(xs: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# =============================
# 3) Domain dictionaries
# =============================
SYNONYMS: Dict[str, List[str]] = {
    "급성 인두염": ["인후통", "목아픔", "인후염", "pharyngitis", "sore throat", "tonsillitis"],
    "급성 관상동맥 증후군": ["흉통", "가슴통증", "압박감", "식은땀", "방사통", "acs", "myocardial infarction"],
    "복부 질환": ["복통", "배아픔", "구토", "설사", "abdominal pain", "appendicitis"],
    "급성 호흡기 질환": ["호흡곤란", "숨참", "천명", "dyspnea", "shortness of breath", "wheeze"],
}

RED_FLAGS: Dict[str, List[str]] = {
    "cardiac": ["의식저하", "실신", "청색증", "식은땀", "심한 흉통", "호흡곤란"],
    "resp": ["호흡곤란", "청색증", "쌕쌕", "숨을 못 쉼", "입술이 파래", "가쁜 호흡"],
    "gi": ["심한 복통", "토혈", "혈변", "복부 경직", "지속 구토"],
}

DOC_TYPE_WEIGHT: Dict[str, float] = {
    "guideline": 1.40,
    "systematic": 1.30,
    "review": 1.15,
    "clinical": 1.05,
    "emergency": 1.25,
}

RECENCY_BOOST_MAX = 0.55


# =============================
# 4) In-memory corpus (PoC)
# =============================
CORPUS: List[EvidenceDoc] = [
    EvidenceDoc(
        doc_id="pharyngitis_lancet_2021",
        title="Acute pharyngitis in adults",
        source="PubMed",
        doc_type="review",
        year=2021,
        journal_or_org="The Lancet",
        abstract_or_summary=(
            "급성 인두염은 바이러스 원인이 흔하며, 대부분 대증 치료로 호전된다. "
            "세균성 가능성 평가(예: Centor 기준)가 임상에서 사용되며, 항생제는 제한적으로 고려된다."
        ),
        conditions=["급성 인두염"],
        keywords=["급성 인두염", "인후통", "목", "발열", "기침", "centor", "pharyngitis", "sore throat"],
        pubmed_query="acute pharyngitis adults clinical review centor",
    ),
    EvidenceDoc(
        doc_id="acs_nejm_2020",
        title="Management of acute coronary syndromes",
        source="PubMed",
        doc_type="review",
        year=2020,
        journal_or_org="NEJM",
        abstract_or_summary=(
            "급성 관상동맥 증후군은 흉통/압박감/발한을 동반할 수 있다. "
            "응급 평가(심전도/심근효소)와 조기 치료가 예후를 좌우한다."
        ),
        conditions=["급성 관상동맥 증후군"],
        keywords=["acs", "급성 관상동맥", "흉통", "압박", "식은땀", "심전도", "troponin", "myocardial infarction"],
        pubmed_query="acute coronary syndrome management ECG troponin",
    ),
    EvidenceDoc(
        doc_id="dyspnea_lancet_2020",
        title="Approach to dyspnea in adults",
        source="PubMed",
        doc_type="clinical",
        year=2020,
        journal_or_org="The Lancet",
        abstract_or_summary=(
            "호흡곤란은 호흡기/심혈관/대사 등 다양한 원인을 가진다. "
            "중증도 평가와 위험 징후 확인 후 적절한 검사/진료과 의뢰가 중요하다."
        ),
        conditions=["급성 호흡기 질환", "급성 관상동맥 증후군"],
        keywords=["dyspnea", "호흡곤란", "숨", "가쁘", "천명", "흉통", "hypoxia"],
        pubmed_query="dyspnea adults clinical approach red flags",
    ),
    EvidenceDoc(
        doc_id="abdominal_bmj_2019",
        title="Evaluation of acute abdominal pain",
        source="PubMed",
        doc_type="clinical",
        year=2019,
        journal_or_org="BMJ",
        abstract_or_summary=(
            "복통은 위치/양상/동반증상에 따라 감별이 달라진다. "
            "외과적 응급(복막자극, 지속 통증, 혈변 등) 징후 확인이 중요하다."
        ),
        conditions=["복부 질환"],
        keywords=["복통", "abdominal pain", "appendicitis", "오른쪽", "구토", "복막", "혈변"],
        pubmed_query="acute abdominal pain evaluation surgical emergency signs",
    ),
    EvidenceDoc(
        doc_id="emergency_redflags_general",
        title="Red flags for urgent evaluation in symptom-based triage",
        source="Clinical Practice",
        doc_type="emergency",
        year=2022,
        journal_or_org="Clinical consensus",
        abstract_or_summary=(
            "증상 기반 트리아지에서 응급 위험 신호(흉통+호흡곤란, 의식저하, 청색증, 심한 출혈 등)는 "
            "즉각적인 응급 평가가 필요하다."
        ),
        conditions=["급성 관상동맥 증후군", "급성 호흡기 질환", "복부 질환", "급성 인두염"],
        keywords=["응급", "red flags", "의식저하", "청색증", "호흡곤란", "흉통", "출혈", "심한 통증"],
        pubmed_query=None,
        url=None,
    ),
]


# =============================
# 5) Cache-safe evidence handling
# =============================
EvidenceInput = Optional[Union[Dict[str, Any], str]]

def _evidence_to_key(evidence: EvidenceInput) -> str:
    """
    Convert evidence into a stable, hashable cache key string.
    - dict -> JSON (sorted keys)
    - str  -> use as-is (or normalize)
    - None -> ""
    """
    if evidence is None:
        return ""
    if isinstance(evidence, str):
        return evidence.strip()
    # dict or other mapping-like
    try:
        return json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except TypeError:
        # fallback: stringify (still hashable)
        return str(evidence)


def _key_to_evidence_dict(evidence_key: str) -> Dict[str, Any]:
    """
    Parse evidence_key back into dict if possible.
    If not JSON, return empty dict (safe).
    """
    if not evidence_key:
        return {}
    try:
        obj = json.loads(evidence_key)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


# =============================
# 6) Query building / scoring
# =============================
def build_query(condition_key: str, symptoms_text: str = "", evidence: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    condition_key = (condition_key or "").strip()
    symptoms_text = symptoms_text or ""
    evidence = evidence or {}

    base_terms = _tokenize(condition_key)
    syn_terms = []
    for s in SYNONYMS.get(condition_key, []):
        syn_terms += _tokenize(s)
    symptom_terms = _tokenize(symptoms_text)

    # rule evidence keywords 활용
    ev_terms = []
    for k in ("gate_matched", "support_matched"):
        v = evidence.get(k, [])
        if isinstance(v, list):
            for t in v:
                ev_terms += _tokenize(str(t))

    terms = _dedupe_keep_order(base_terms + syn_terms + symptom_terms + ev_terms)

    # red flag detection (simple)
    redflag_hits = []
    st_norm = _norm(symptoms_text)
    for flags in RED_FLAGS.values():
        for f in flags:
            if _norm(f) in st_norm:
                redflag_hits.append(f)

    return {
        "condition_key": condition_key,
        "terms": terms,
        "red_flags": _dedupe_keep_order(redflag_hits),
    }


def _recency_boost(year: int, now_year: int = 2026) -> float:
    age = max(now_year - year, 0)
    boost = max(0.0, RECENCY_BOOST_MAX - 0.06 * age)
    return round(boost, 3)


def score_doc(doc: EvidenceDoc, query: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
    terms = query["terms"]
    condition_key = query["condition_key"]
    red_flags = query["red_flags"]

    cond_match = 1.0 if condition_key in doc.conditions else 0.0

    doc_kw = " ".join([_norm(k) for k in doc.keywords])
    title_tokens = set(_tokenize(doc.title))
    body_tokens = set(_tokenize(doc.abstract_or_summary))

    overlap_kw = [t for t in terms if t in doc_kw]
    overlap_title = [t for t in terms if t in title_tokens]
    overlap_body = [t for t in terms if t in body_tokens]

    overlap_score = (len(overlap_kw) * 1.15) + (len(overlap_title) * 0.95) + (len(overlap_body) * 0.55)

    type_w = DOC_TYPE_WEIGHT.get(doc.doc_type, 1.0)
    rec = _recency_boost(doc.year)

    redflag_boost = 0.0
    if red_flags:
        if doc.doc_type == "emergency":
            redflag_boost = 1.2
        if doc.doc_type in ("guideline", "clinical"):
            redflag_boost += 0.25

    score = (2.0 * cond_match + overlap_score) * type_w + rec + redflag_boost

    evidence = {
        "cond_match": cond_match,
        "doc_type": doc.doc_type,
        "doc_type_weight": type_w,
        "recency_boost": rec,
        "red_flags": red_flags,
        "redflag_boost": round(redflag_boost, 2),
        "overlap_kw": sorted(set(overlap_kw)),
        "overlap_title": sorted(set(overlap_title)),
        "overlap_body": sorted(set(overlap_body)),
    }
    return float(score), evidence


def _group_by_type(docs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for d in docs:
        grouped.setdefault(d["doc_type"], []).append(d)
    return grouped


# =============================
# 7) Cached retrieval core (hashable args only!)
# =============================
@lru_cache(maxsize=256)
def _search_pubmed_cached(
    condition_key: str,
    symptoms_text: str,
    evidence_key: str,
    top_k: int,
) -> List[Dict[str, Any]]:
    evidence_dict = _key_to_evidence_dict(evidence_key)
    q = build_query(condition_key, symptoms_text, evidence_dict)

    scored: List[Tuple[float, EvidenceDoc, Dict[str, Any]]] = []
    for doc in CORPUS:
        s, ev = score_doc(doc, q)
        if s > 0:
            scored.append((s, doc, ev))

    scored.sort(key=lambda x: x[0], reverse=True)
    picked = scored[:max(1, int(top_k))]

    results: List[Dict[str, Any]] = []
    for s, doc, ev in picked:
        if doc.url:
            url = doc.url
        else:
            query_term = doc.pubmed_query or doc.title
            url = f"https://pubmed.ncbi.nlm.nih.gov/?term={_norm(query_term).replace(' ', '+')}"

        results.append({
            "doc_id": doc.doc_id,
            "title": doc.title,
            "source": doc.source,
            "doc_type": doc.doc_type,
            "journal": doc.journal_or_org,
            "year": doc.year,
            "summary": doc.abstract_or_summary,
            "url": url,
            "retrieval": {
                "score": round(s, 2),
                **ev,
            }
        })
    return results


# =============================
# 8) Public API (accepts dict evidence safely)
# =============================
def search_pubmed(
    condition_key: str,
    symptoms_text: str = "",
    evidence: EvidenceInput = None,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Public entry:
    - evidence can be dict or str (safe)
    - internally converted to evidence_key for caching
    """
    evidence_key = _evidence_to_key(evidence)
    return _search_pubmed_cached(condition_key.strip(), symptoms_text or "", evidence_key, int(top_k))


def search_pubmed_grouped(
    condition_key: str,
    symptoms_text: str = "",
    evidence: EvidenceInput = None,
    top_k: int = 7,
) -> Dict[str, Any]:
    docs = search_pubmed(condition_key, symptoms_text, evidence, top_k=top_k)
    q = build_query(condition_key, symptoms_text, _key_to_evidence_dict(_evidence_to_key(evidence)))
    return {
        "query": q,
        "docs": docs,
        "grouped": _group_by_type(docs),
    }
