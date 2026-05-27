"""
Parser per www.wunderground.com (Weather Underground).
Estrae dati meteo e testo degli articoli da pagine di stazioni/previsioni.
"""

import re
import asyncio
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode


# Punta alla sezione principale del contenuto
_SELETTORE_CSS_WU = "#inner-content"

_TAG_ESCLUSI_WU = [
    "nav", "footer", "header", "script", "style", "noscript",
    ".ad-unit", ".advertisement", ".wu-header",
    ".bottomAd", ".sidebarAd", ".cookie-notice",
    "#onetrust-banner-sdk", ".navbar", ".legal-footer",
    ".related-articles", ".trending-section",
    "#top-banner-ad-browser", "#position-1-banner-ad-browser",
    "#WX_WindowShade", "#report-box",
]


def _url_appartiene_a_wunderground(url: str) -> bool:
    """Restituisce True se l'URL appartiene a www.wunderground.com."""
    return urlparse(url).netloc in ("www.wunderground.com", "wunderground.com")


def _pulisci_markdown_wunderground(md_grezzo: str) -> str:
    """Pulisce il Markdown grezzo dalle pagine di Weather Underground."""
    testo = re.sub(r"!\[.*?\]\(.*?\)", "", md_grezzo)
    testo = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", testo)
    testo = re.sub(r"<!--.*?-->", "", testo, flags=re.DOTALL)
    righe = testo.splitlines()
    righe_pulite = [ln for ln in righe if len(ln.strip()) >= 3 or ln.strip() == ""]
    testo = "\n".join(righe_pulite)
    testo = re.sub(r"\n{3,}", "\n\n", testo)
    return testo.strip()


def _crea_config_crawler() -> CrawlerRunConfig:
    """Costruisce la CrawlerRunConfig condivisa per le pagine Wunderground."""
    return CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        css_selector=_SELETTORE_CSS_WU,
        excluded_tags=_TAG_ESCLUSI_WU,
        remove_overlay_elements=True,
        wait_until="networkidle",
        page_timeout=60000,
        word_count_threshold=5,
    )


def _estrai_con_bs4(html_text: str) -> str:
    """
    Estrattore tramite BeautifulSoup per le pagine di Weather Underground.
    Punta a #inner-content come la config crawl4ai, poi cade su <body>.
    Aggiunge il titolo della pagina come ## heading (markdown).
    """
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript",
                     "ins", "aside"]):
        tag.decompose()

    # Titolo come heading markdown
    title_tag = soup.find("title")
    title_md = ""
    if title_tag and title_tag.string:
        titolo = re.sub(r"\s*[|\-\u2013]\s*Weather Underground.*$", "", title_tag.string).strip()
        if titolo:
            title_md = "## " + titolo + "\n\n"

    radice = soup.select_one("#inner-content") or soup.body or soup
    testo_grezzo = radice.get_text(separator=" ", strip=True)
    testo_grezzo = re.sub(r"\s+", " ", testo_grezzo).strip()
    righe = [ln for ln in testo_grezzo.splitlines() if len(ln.strip()) >= 3 or ln.strip() == ""]
    testo = "\n".join(righe)
    testo = re.sub(r"\n{3,}", "\n\n", testo)
    return (title_md + testo).strip()


async def parse(url: str) -> dict:
    """
    Analizza una pagina www.wunderground.com e restituisce dati strutturati.

    Args:
        url: Un URL da www.wunderground.com.

    Returns:
        dict con chiavi: url, domain, title, html_text, parsed_text.

    Raises:
        ValueError:   Se l'URL non e' da wunderground.com.
        RuntimeError: Se la pagina non puo' essere analizzata.
    """
    if not _url_appartiene_a_wunderground(url):
        raise ValueError(f"L'URL '{url}' non e' da www.wunderground.com")

    cfg_browser = BrowserConfig(headless=True)
    cfg_crawler = _crea_config_crawler()

    async with AsyncWebCrawler(config=cfg_browser) as crawler:
        risultato = await crawler.arun(url=url, config=cfg_crawler)

    if not risultato.success:
        raise RuntimeError(f"Impossibile effettuare il crawl di '{url}': {risultato.error_message}")

    html_text: str = risultato.cleaned_html or risultato.html or ""

    titolo: str = ""
    if risultato.metadata and risultato.metadata.get("title"):
        titolo = re.sub(r"\s*[|\-\u2013]\s*Weather Underground.*$", "", risultato.metadata["title"]).strip()

    # Usa lo stesso estrattore bs4 di parse_html per garantire coerenza
    # tra GET /parse (live) e POST /parse (HTML memorizzato).
    testo_parsato: str = _estrai_con_bs4(html_text)

    return {
        "url": url,
        "domain": "www.wunderground.com",
        "title": titolo,
        "html_text": html_text,
        "parsed_text": testo_parsato,
    }


async def parse_html(url: str, html_text: str) -> dict:
    """
    Analizza una pagina Wunderground dall'HTML fornito senza scaricare dalla rete.
    Usa BeautifulSoup per estrazione deterministica e coerente indipendentemente
    dalla dimensione della pagina.

    Args:
        url:       URL originale, usato per i metadati del dominio.
        html_text: Contenuto HTML grezzo della pagina.

    Returns:
        dict con chiavi: url, domain, title, html_text, parsed_text.

    Raises:
        ValueError: Se l'URL non e' da wunderground.com.
    """
    if not _url_appartiene_a_wunderground(url):
        raise ValueError(f"L'URL '{url}' non e' da www.wunderground.com")

    # Estrae il titolo direttamente dall'HTML
    titolo: str = ""
    try:
        from bs4 import BeautifulSoup as _BS
        _soup = _BS(html_text, "html.parser")
        _tag_titolo = _soup.find("title")
        if _tag_titolo and _tag_titolo.string:
            titolo = re.sub(r"\s*[|\-\u2013]\s*Weather Underground.*$", "", _tag_titolo.string).strip()
    except Exception:
        pass

    # BeautifulSoup direttamente per risultati deterministici — evita non-determinismo
    # di crawl4ai in modalita' raw: su pagine grandi con molto JS, garantendo
    # coerenza tra full_gs_eval e valutazione manuale parse+evaluate.
    testo_parsato = _estrai_con_bs4(html_text)

    return {
        "url": url,
        "domain": "www.wunderground.com",
        "title": titolo,
        "html_text": html_text,
        "parsed_text": testo_parsato,
    }


if __name__ == "__main__":
    risultato = asyncio.run(parse("https://www.wunderground.com/weather/it/rome"))
    print("Titolo:", risultato["title"])
    print(risultato["parsed_text"][:500])
