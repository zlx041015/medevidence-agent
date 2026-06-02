import json
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

from medevidence_agent.models import SourceDocument


PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def build_pubmed_query(keywords: list[str]) -> str:
    cleaned = [keyword.strip() for keyword in keywords if keyword.strip()]
    if not cleaned:
        return ""

    quoted = [f'"{keyword}"' if " " in keyword else keyword for keyword in cleaned]

    if len(quoted) == 1:
        return quoted[0]

    if len(quoted) == 2:
        return f"{quoted[0]} AND {quoted[1]}"

    core_terms = quoted[:2]
    support_terms = quoted[2:]
    support_group = " OR ".join(support_terms)
    return f"({core_terms[0]} AND {core_terms[1]}) AND ({support_group})"


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

    core_only = cleaned[:2]
    if core_only:
        core_query = build_pubmed_query(core_only)
        pmids = search_pubmed_pmids(core_query, retmax=retmax)
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
