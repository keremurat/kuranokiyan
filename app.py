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
    Kuran'daki bir surenin detaylı bilgilerini webden çeker.

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
        
        # Sure detaylı bilgilerini çıkar
        sure_details = {
            "sure_adi": sure_name,
            "sure_url": sure_url
        }
        
        # Sure numarasını ve ayet sayısını bul
        title = sure_soup.find("title")
        if title:
            title_text = title.get_text()
            # Örnek: "1. Fatiha Suresi - 7 Ayet"
            import re
            match = re.search(r'(\d+)\.\s*(.+?)\s*-\s*(\d+)\s*Ayet', title_text)
            if match:
                sure_details["sure_numarasi"] = int(match.group(1))
                sure_details["ayet_sayisi"] = int(match.group(3))
        
        # Anlamı ve açıklamayı bul
        meaning = None
        description = None
        
        # Ana içerik alanını bul
        content_divs = sure_soup.find_all("div", class_=True)
        for div in content_divs:
            classes = div.get("class", [])
            text = div.get_text(strip=True)
            
            # Anlam alanını bul
            if any("meal" in c.lower() or "meaning" in c.lower() for c in classes):
                if len(text) > 20:  # Anlam genellikle uzun metindir
                    meaning = text
            
            # Açıklama alanını bul  
            if any("aciklama" in c.lower() or "description" in c.lower() or "tanitim" in c.lower() for c in classes):
                if len(text) > 20:
                    description = text
        
        # Alternatif: paragraflardan anlam bul
        if not meaning:
            paragraphs = sure_soup.find_all("p")
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:  # Uzun paragraf anlam olabilir
                    meaning = text
                    break
        
        # Meta bilgileri bul (mekan, dönem vs.)
        meta_info = {}
        info_divs = sure_soup.find_all("div")
        for div in info_divs:
            text = div.get_text(strip=True)
            if "Mekkî" in text or "Medenî" in text:
                meta_info["iniş_yeri"] = "Mekke" if "Mekkî" in text else "Medine"
            if "iniş sırası" in text.lower():
                import re
                order_match = re.search(r'(\d+)', text)
                if order_match:
                    meta_info["iniş_sirasi"] = int(order_match.group(1))
        
        sure_details.update(meta_info)
        
        if meaning:
            sure_details["anlam"] = meaning
        if description:
            sure_details["aciklama"] = description
            
        if not meaning and not description:
            result["error"] = f"'{sure_name}' için detaylı bilgiler bulunamadı. Sayfa yapısı değişmiş olabilir."
            return result
            
        result["success"] = True
        result["data"] = sure_details
        return result
    except Exception as e:
        result["error"] = f"Web isteği veya parsing hatası: {str(e)}"
        return result