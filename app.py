import requests
import json

from bs4 import BeautifulSoup
from functools import lru_cache
from datetime import datetime


def dummyTool(param: str) -> str:
    """
    Method description here.
    """
    # Do Some Processing Here
    return f"Your tool will return processed {param}"


@lru_cache(maxsize=128)
def get_sure_meaning(sure_name: str) -> dict:
    """
    Kuran'daki bir surenin anlamını webden çeker.

    Args:
        sure_name (str): Sorgulanan sure adı (ör: 'Fatiha')
    Returns:
        dict: {success, data, error, timestamp}
    Raises:
        None (hatalar response içinde döner)
    """
    result = {
        "success": False,
        "data": None,
        "error": None,
        "timestamp": datetime.utcnow().isoformat()
    }
    if not sure_name or not isinstance(sure_name, str):
        result["error"] = "Geçersiz sure adı. Lütfen bir sure adı girin."
        return result
    try:
        url = "https://www.kuranokuyan.com/sure-listesi"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Sure adlarını ve linklerini bul
        sure_link = None
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if text.lower() == sure_name.lower() or text.lower() == sure_name.lower().replace(" suresi",""):
                sure_link = a["href"]
                break
        if not sure_link:
            result["error"] = f"'{sure_name}' adlı sure bulunamadı veya sayfa yapısı değişmiş olabilir."
            return result
        # Sure detay sayfasına git
        sure_url = sure_link if sure_link.startswith("http") else f"https://www.kuranokuyan.com{sure_link}"
        sure_resp = requests.get(sure_url, timeout=10)
        sure_resp.raise_for_status()
        sure_soup = BeautifulSoup(sure_resp.text, "html.parser")
        # Anlamı bul (örnek: .meal veya .sure-meal gibi bir class olabilir)
        meaning = None
        for div in sure_soup.find_all("div"):
            if div.get("class") and any("meal" in c for c in div.get("class")):
                meaning = div.get_text(strip=True)
                break
        if not meaning:
            # Alternatif: ilk paragraf veya metin
            p = sure_soup.find("p")
            if p:
                meaning = p.get_text(strip=True)
        if not meaning:
            result["error"] = f"'{sure_name}' anlamı ilgili sayfada bulunamadı. Sayfa yapısı değişmiş olabilir."
            return result
        result["success"] = True
        result["data"] = {
            "sure": sure_name,
            "meaning": meaning
        }
        return result
    except Exception as e:
        result["error"] = f"Web isteği veya parsing hatası: {str(e)}"
        return result