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
        # Sure listesi tablosunu bul
        table = soup.find("table")
        if not table:
            result["error"] = "Sure listesi bulunamadı."
            return result
        rows = table.find_all("tr")
        found = None
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            name = cols[1].get_text(strip=True)
            if name.lower() == sure_name.lower():
                found = row
                break
        if not found:
            result["error"] = f"'{sure_name}' adlı sure bulunamadı."
            return result
        # Anlam sütunu genellikle son sütun
        meaning = found.find_all("td")[-1].get_text(strip=True)
        result["success"] = True
        result["data"] = {
            "sure": sure_name,
            "meaning": meaning
        }
        return result
    except Exception as e:
        result["error"] = str(e)
        return result