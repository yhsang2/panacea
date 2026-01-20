from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class Rule:
    id: str
    condition_key: str
    display_label: str                 # 사용자에게 보여줄 라벨(“패턴” 중심)
    keywords_any: List[str]            # gate: 최소 1개는 맞아야 함
    keywords_support: List[str]        # confidence 증가
    department: List[str]
    emergency: bool
    weight: float                      # 0~1 (진단확률 아님)
    urgency_level: str                 # "emergency" | "urgent" | "routine" | "observe"
    action_reason: str                 # 왜 이런 액션이 필요한지(짧게)
    next_actions: List[str]            # 사용자 행동 가이드


# -----------------------------
# Rules (extend freely)
# -----------------------------
RULES: List[Rule] = [
    # ✅ NEW: Right lower quadrant abdominal pain pattern (appendicitis-like without diagnosing)
    Rule(
        id="rlq_abdominal_pain_pattern",
        condition_key="복부 질환",
        display_label="우하복부 급성 복통 패턴(수술적 원인 평가 필요 가능)",
        keywords_any=["오른쪽", "우하", "오른쪽아랫배", "오른쪽 아랫배", "우하복부"],
        keywords_support=["복통", "배", "통증", "구토", "식욕", "발열", "열", "걷기", "움직", "반발", "눌렀"],
        department=["외과", "응급의학과"],
        emergency=False,  # 여기서 진단/응급 확정 금지 → 아래 next_actions에서 조건부로 안내
        weight=0.78,
        urgency_level="urgent",
        action_reason=(
            "오른쪽 아랫배 통증은 일부 경우 빠른 평가가 필요한 원인과 연관될 수 있어, "
            "오늘 안에 진료를 권장합니다."
        ),
        next_actions=[
            "오늘 안에 외과 또는 응급의학과 진료를 권장합니다.",
            "발열/구토/통증 악화/걷기 어려움/눌렀다 뗄 때 심해짐이 있으면 응급실 방문을 고려하세요.",
            "통증 시작 시점, 위치 변화, 동반 증상(구토/발열/설사)을 메모해 의료진에게 전달하세요.",
        ],
    ),

    Rule(
        id="acute_coronary_syndrome_pattern",
        condition_key="급성 관상동맥 증후군",
        display_label="흉통-심혈관 위험 패턴",
        keywords_any=["가슴", "흉통"],
        keywords_support=["통증", "쥐어짜", "압박", "식은땀", "호흡곤란", "어지러", "방사"],
        department=["응급의학과", "심장내과"],
        emergency=True,
        weight=0.95,
        urgency_level="emergency",
        action_reason="흉통과 동반 증상은 즉시 평가가 필요한 경우가 있어, 지체 없이 진료가 필요합니다.",
        next_actions=[
            "즉시 응급실 방문을 권장합니다.",
            "가능하면 혼자 이동하지 말고 주변 도움을 받으세요.",
        ],
    ),

    Rule(
        id="respiratory_distress_pattern",
        condition_key="급성 호흡기 질환",
        display_label="호흡곤란 위험 패턴",
        keywords_any=["호흡", "숨"],
        keywords_support=["곤란", "가쁘", "쌕쌕", "천명", "청색", "가슴"],
        department=["응급의학과", "호흡기내과"],
        emergency=True,
        weight=0.90,
        urgency_level="emergency",
        action_reason="호흡곤란은 중증 원인과 연관될 수 있어 즉시 평가가 필요합니다.",
        next_actions=[
            "즉시 응급실 방문을 권장합니다.",
            "입술/손끝이 파래지거나 의식이 흐려지면 즉시 119를 고려하세요.",
        ],
    ),

    Rule(
        id="acute_pharyngitis_pattern",
        condition_key="급성 인두염",
        display_label="인후통-상기도 감염 패턴",
        keywords_any=["목", "인후"],
        keywords_support=["아프", "삼키", "따끔", "기침", "발열", "미열", "콧물"],
        department=["이비인후과"],
        emergency=False,
        weight=0.65,
        urgency_level="routine",
        action_reason="흔한 상기도 증상 패턴과 유사하나, 증상이 지속되면 평가가 필요합니다.",
        next_actions=[
            "증상이 3~5일 이상 지속되거나 고열이 있으면 진료를 권장합니다.",
            "호흡곤란/심한 탈수/의식 변화가 있으면 즉시 응급실을 고려하세요.",
        ],
    ),

    Rule(
        id="acute_abdominal_pain_general",
        condition_key="복부 질환",
        display_label="급성 복통 패턴",
        keywords_any=["복통", "배"],
        keywords_support=["구토", "설사", "발열", "오른쪽", "압통", "식욕"],
        department=["내과"],
        emergency=False,
        weight=0.60,
        urgency_level="routine",
        action_reason="복통은 다양한 원인이 있어, 증상 양상에 따라 진료가 필요할 수 있습니다.",
        next_actions=[
            "통증이 지속되거나 악화되면 내과 진료를 권장합니다.",
            "혈변/토혈/심한 탈수/복부가 딱딱해지는 느낌이 있으면 응급실을 고려하세요.",
        ],
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
    confidence: 0~1 휴리스틱 지표 (진단 확률 아님)
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
    Returns:
      - display_label (패턴 중심)
      - urgency_level / next_actions / action_reason
      - condition_key (내부 연동용: PubMed RAG)
    """
    if not symptoms or not symptoms.strip():
        c = 0.2
        return {
            "condition_key": "비특이적 증상",
            "display_label": "추가 정보 필요",
            "suspected_conditions": ["증상이 충분히 입력되지 않아 추가 정보가 필요합니다"],
            "recommended_departments": ["내과"],
            "emergency": False,
            "urgency_level": "observe",
            "action_reason": "증상 정보가 부족해 우선 추가 정보가 필요합니다.",
            "next_actions": ["통증 위치/기간/동반 증상을 조금 더 구체적으로 입력해 주세요."],
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
            "display_label": rule.display_label,
            "suspected_conditions": [f"{rule.display_label}과(와) 유사한 양상이 의심됩니다"],
            "recommended_departments": rule.department,
            "emergency": rule.emergency,
            "urgency_level": rule.urgency_level,
            "action_reason": rule.action_reason,
            "next_actions": rule.next_actions,
            "confidence": conf,
            "confidence_label": confidence_label(conf),
            "rule_id": rule.id,
            "evidence": details,
        })

    if not candidates:
        c = 0.3
        return {
            "condition_key": "비특이적 증상",
            "display_label": "비특이적 증상",
            "suspected_conditions": ["비특이적 증상으로 추가 평가가 필요합니다"],
            "recommended_departments": ["내과"],
            "emergency": False,
            "urgency_level": "routine",
            "action_reason": "입력된 증상만으로 특정 패턴이 뚜렷하지 않아 일반 진료를 권장합니다.",
            "next_actions": ["증상이 지속/악화되면 내과 진료를 권장합니다."],
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
