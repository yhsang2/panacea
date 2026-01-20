from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class Rule:
    id: str
    condition_key: str
    keywords_any: List[str]          # at least one should match (gate)
    keywords_support: List[str]      # confidence increases by match ratio
    department: List[str]
    emergency: bool
    weight: float                   # 0~1: rule priority / clinical-risk weight (NOT probability)


RULES: List[Rule] = [
    Rule(
        id="acute_coronary_syndrome",
        condition_key="급성 관상동맥 증후군",
        keywords_any=["가슴", "흉통"],
        keywords_support=["통증", "쥐어짜", "압박", "식은땀", "호흡곤란"],
        department=["응급의학과", "심장내과"],
        emergency=True,
        weight=0.95,
    ),
    Rule(
        id="respiratory_distress",
        condition_key="급성 호흡기 질환",
        keywords_any=["호흡", "숨"],
        keywords_support=["곤란", "가쁘", "쌕쌕", "천명", "청색증"],
        department=["응급의학과", "호흡기내과"],
        emergency=True,
        weight=0.90,
    ),
    Rule(
        id="acute_pharyngitis",
        condition_key="급성 인두염",
        keywords_any=["목", "인후"],
        keywords_support=["아프", "삼키", "따끔", "기침", "발열", "미열"],
        department=["이비인후과"],
        emergency=False,
        weight=0.65,
    ),
    Rule(
        id="acute_abdominal_pain",
        condition_key="복부 질환",
        keywords_any=["복통", "배"],
        keywords_support=["오른쪽", "구토", "설사", "발열", "압통", "식욕부진"],
        department=["내과", "외과"],
        emergency=False,
        weight=0.60,
    ),
]


def _contains(text: str, token: str) -> bool:
    return token in text


def _match_any(text: str, tokens: List[str]) -> Tuple[bool, List[str]]:
    matched = [t for t in tokens if _contains(text, t)]
    return (len(matched) > 0), matched


def _match_support(text: str, tokens: List[str]) -> Tuple[int, List[str], List[str]]:
    matched = [t for t in tokens if _contains(text, t)]
    missing = [t for t in tokens if t not in matched]
    return len(matched), matched, missing


def calculate_confidence(symptoms: str, rule: Rule) -> Tuple[float, Dict[str, Any]]:
    """
    Returns (confidence, details)

    - confidence: 0.0 ~ 1.0 (heuristic score, NOT medical probability)
    - details: explainable match information
    """
    s = symptoms.lower().strip()

    gate_ok, gate_matched = _match_any(s, rule.keywords_any)
    if not gate_ok:
        return 0.0, {
            "gate_ok": False,
            "gate_matched": [],
            "support_matched": [],
            "support_missing": rule.keywords_support,
            "support_ratio": 0.0,
            "weight": rule.weight,
        }

    support_count, support_matched, support_missing = _match_support(s, rule.keywords_support)
    denom = max(len(rule.keywords_support), 1)
    support_ratio = support_count / denom

    # baseline comes from gate match; supports add confidence
    base = 0.35 + 0.65 * support_ratio
    confidence = base * float(rule.weight)

    confidence = max(0.0, min(1.0, confidence))
    confidence = round(confidence, 2)

    return confidence, {
        "gate_ok": True,
        "gate_matched": gate_matched,
        "support_matched": support_matched,
        "support_missing": support_missing,
        "support_ratio": round(support_ratio, 2),
        "weight": rule.weight,
    }


def confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "높음"
    if confidence >= 0.50:
        return "중간"
    return "낮음"


def rule_based_triage(symptoms: str, include_candidates: bool = True) -> Dict[str, Any]:
    """
    Rule-based triage with weight + confidence score.

    Note: confidence is a heuristic indicator, not a diagnosis probability.
    """
    if not symptoms or not symptoms.strip():
        c = 0.2
        return {
            "condition_key": "비특이적 증상",
            "suspected_conditions": ["증상이 충분히 입력되지 않아 추가 정보가 필요합니다"],
            "recommended_departments": ["내과"],
            "emergency": False,
            "confidence": c,
            "confidence_label": confidence_label(c),
            "rule_id": "empty_input",
            "evidence": {"reason": "empty_input"},
            "candidates": [] if include_candidates else None,
        }

    candidates: List[Dict[str, Any]] = []

    for rule in RULES:
        conf, details = calculate_confidence(symptoms, rule)
        if conf <= 0.0:
            continue

        candidates.append({
            "condition_key": rule.condition_key,
            "suspected_conditions": [f"{rule.condition_key}이(가) 의심됩니다"],
            "recommended_departments": rule.department,
            "emergency": rule.emergency,
            "confidence": conf,
            "confidence_label": confidence_label(conf),
            "rule_id": rule.id,
            "evidence": details,
        })

    if not candidates:
        c = 0.3
        return {
            "condition_key": "비특이적 증상",
            "suspected_conditions": ["비특이적 증상으로 추가 평가가 필요합니다"],
            "recommended_departments": ["내과"],
            "emergency": False,
            "confidence": c,
            "confidence_label": confidence_label(c),
            "rule_id": "fallback",
            "evidence": {"reason": "no_rule_matched"},
            "candidates": [] if include_candidates else None,
        }

    candidates_sorted = sorted(
        candidates,
        key=lambda x: (x["confidence"], 1 if x["emergency"] else 0, x["evidence"].get("weight", 0.0)),
        reverse=True,
    )
    best = candidates_sorted[0]
    best["candidates"] = candidates_sorted if include_candidates else None
    return best
