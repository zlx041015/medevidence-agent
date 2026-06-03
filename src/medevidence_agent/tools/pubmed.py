import json
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

from medevidence_agent.models import SourceDocument


PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def split_query_terms(keywords: list[str]) -> tuple[list[str], list[str]]:
    cleaned = [keyword.strip() for keyword in keywords if keyword.strip()]
    disease_terms: list[str] = []
    support_terms: list[str] = []

    disease_markers = [
        "diabetes",
        "hypertension",
        "kidney",
        "renal",
        "thyroid",
        "goiter",
        "cholesterol",
        "hyperlipidemia",
        "coronary",
        "heart failure",
        "atrial fibrillation",
        "stroke",
        "copd",
        "asthma",
        "pneumonia",
        "tuberculosis",
        "anemia",
        "osteoporosis",
        "gout",
        "arthritis",
        "reflux",
        "ulcer",
        "gastroenteritis",
        "fatty liver",
        "hepatitis",
        "urinary tract infection",
        "prostatic hyperplasia",
        "kidney stone",
        "depression",
        "anxiety",
        "insomnia",
        "migraine",
        "eczema",
        "urticaria",
        "acne",
        "obesity",
        "cancer",
    ]

    support_markers = [
        "guideline",
        "screening",
        "monitoring",
        "risk",
        "management",
        "treatment",
        "therapy",
        "first-line",
        "follow-up",
        "control",
        "secondary prevention",
        "severity",
    ]

    for keyword in cleaned:
        lowered = keyword.lower()
        if any(marker in lowered for marker in disease_markers):
            disease_terms.append(keyword)
        elif any(marker in lowered for marker in support_markers):
            support_terms.append(keyword)
        else:
            support_terms.append(keyword)

    if not disease_terms and cleaned:
        disease_terms = cleaned[:1]
        support_terms = cleaned[1:]

    return disease_terms, support_terms


def build_pubmed_query(keywords: list[str]) -> str:
    disease_terms, support_terms = split_query_terms(keywords)
    cleaned = disease_terms + support_terms
    if not cleaned:
        return ""

    def quote(term: str) -> str:
        return f'"{term}"' if " " in term else term

    disease_quoted = [quote(term) for term in disease_terms]
    support_quoted = [quote(term) for term in support_terms]

    if not support_quoted:
        if len(disease_quoted) == 1:
            return disease_quoted[0]
        return " AND ".join(disease_quoted)

    disease_group = " AND ".join(disease_quoted) if len(disease_quoted) > 1 else disease_quoted[0]
    support_group = " OR ".join(support_quoted)
    return f"({disease_group}) AND ({support_group})"


def search_pubmed_pmids(query: str, retmax: int = 5) -> list[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": str(retmax),
        "sort": "relevance",
    }

    url = f"{PUBMED_ESEARCH_URL}?{urlencode(params)}"

    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")

    data = json.loads(raw)
    return data["esearchresult"]["idlist"]


def search_pubmed_pmids_with_fallback(keywords: list[str], retmax: int = 5) -> list[str]:
    cleaned = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not cleaned:
        return []

    query = build_pubmed_query(cleaned)
    pmids = search_pubmed_pmids(query, retmax=retmax)
    if pmids:
        return pmids

    disease_terms, support_terms = split_query_terms(cleaned)

    core_only = disease_terms[:2] if disease_terms else cleaned[:2]
    if core_only:
        core_query = build_pubmed_query(core_only + support_terms[:1])
        pmids = search_pubmed_pmids(core_query, retmax=retmax)
        if pmids:
            return pmids

    if disease_terms:
        disease_query = " OR ".join(f'"{term}"' if " " in term else term for term in disease_terms)
        pmids = search_pubmed_pmids(disease_query, retmax=retmax)
        if pmids:
            return pmids

    if len(cleaned) > 1:
        quoted = [f'"{keyword}"' if " " in keyword else keyword for keyword in cleaned]
        broad_query = " OR ".join(quoted)
        pmids = search_pubmed_pmids(broad_query, retmax=retmax)
        if pmids:
            return pmids

    return search_pubmed_pmids(cleaned[0], retmax=retmax)


def infer_publication_type(article: ET.Element, title: str) -> str:
    title_lower = title.lower()
    publication_types = [
        (node.text or "").strip().lower()
        for node in article.findall(".//PublicationType")
        if node.text
    ]
    publication_blob = " ".join(publication_types)

    if "guideline" in publication_blob or "guideline" in title_lower:
        return "guideline"
    if "practice guideline" in publication_blob:
        return "guideline"
    if "systematic review" in publication_blob or "systematic review" in title_lower:
        return "systematic_review"
    if "meta-analysis" in publication_blob or "meta-analysis" in title_lower:
        return "meta_analysis"
    if "review" in publication_blob or "review" in title_lower:
        return "review"
    if "randomized controlled trial" in publication_blob or "randomized" in title_lower:
        return "trial"
    if "clinical trial" in publication_blob or "trial" in title_lower:
        return "trial"
    if "case reports" in publication_blob or "case report" in title_lower:
        return "case_report"
    return "pubmed_article"


def infer_quality_score(source_type: str, year: int) -> float:
    base_scores = {
        "guideline": 0.95,
        "systematic_review": 0.90,
        "meta_analysis": 0.90,
        "review": 0.82,
        "trial": 0.80,
        "case_report": 0.58,
        "pubmed_article": 0.72,
    }
    score = base_scores.get(source_type, 0.72)

    if year >= 2020:
        score += 0.03
    elif year < 2005:
        score -= 0.05

    return round(max(0.4, min(score, 0.98)), 3)


def _extract_year(article: ET.Element) -> int:
    year = article.findtext(".//PubDate/Year")
    if year and year.isdigit():
        return int(year)

    medline_date = article.findtext(".//PubDate/MedlineDate", default="")
    digits = "".join(ch for ch in medline_date if ch.isdigit())
    if len(digits) >= 4:
        return int(digits[:4])

    return 1900


def fetch_pubmed_articles(pmids: list[str]) -> list[SourceDocument]:
    if not pmids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
    }

    url = f"{PUBMED_EFETCH_URL}?{urlencode(params)}"

    with urlopen(url, timeout=30) as response:
        raw = response.read().decode("utf-8")

    root = ET.fromstring(raw)
    articles: list[SourceDocument] = []

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", default="unknown")
        title = article.findtext(".//ArticleTitle", default="No title")
        year = _extract_year(article)
        source_type = infer_publication_type(article, title)
        quality_score = infer_quality_score(source_type, year)

        abstract_texts = article.findall(".//Abstract/AbstractText")
        abstract_parts = []
        for abstract in abstract_texts:
            if abstract.text:
                abstract_parts.append(abstract.text.strip())

        abstract_text = " ".join(abstract_parts).strip()
        content = f"{title}\n\n{abstract_text}" if abstract_text else title

        articles.append(
            SourceDocument(
                source_id=f"pmid_{pmid}",
                title=title,
                source_type=source_type,
                year=year,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                quality_score=quality_score,
                content=content,
                relevance_score=0.0,
            )
        )

    return articles
