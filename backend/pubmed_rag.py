# PubMed 논문 요약 Mock DB (PoC용)

PUBMED_DB = {
    "급성 인두염": [
        {
            "title": "Acute pharyngitis in adults",
            "journal": "The Lancet",
            "year": 2021,
            "summary": (
                "급성 인두염은 바이러스 감염이 가장 흔한 원인이며, "
                "대부분 대증 치료로 호전된다. 항생제는 제한적으로 사용해야 한다."
            )
        }
    ],
    "급성 관상동맥 증후군": [
        {
            "title": "Management of acute coronary syndromes",
            "journal": "NEJM",
            "year": 2020,
            "summary": (
                "급성 관상동맥 증후군은 흉통과 발한을 동반하며, "
                "조기 진단과 즉각적인 응급 처치가 생존율을 결정한다."
            )
        }
    ],
    "복부 질환": [
        {
            "title": "Evaluation of acute abdominal pain",
            "journal": "BMJ",
            "year": 2019,
            "summary": (
                "복통은 비특이적인 증상일 수 있으나, "
                "위치와 양상에 따라 외과적 질환 가능성을 평가해야 한다."
            )
        }
    ]
}


def search_pubmed(condition_keyword: str):
    """
    질환 키워드를 기반으로 PubMed 논문 요약 반환
    """
    return PUBMED_DB.get(condition_keyword, [])
