import json
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import urlopen

from medevidence_agent.models import SourceDocument


PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


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
        year = article.findtext(".//PubDate/Year", default="1900")

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
                source_type="pubmed_article",
                year=int(year) if year.isdigit() else 1900,
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                quality_score=0.78,
                content=content,
                relevance_score=0.0,
            )
        )

    return articles