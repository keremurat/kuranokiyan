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


@lru_cache(maxsize=128)
def kuran_arastirma_yap(soru: str) -> dict:
    """
    Kuran ile ilgili genel soruları araştırır ve yanıtlar.
    
    Args:
        soru (str): Kullanıcının sorduğu genel soru (ör: "Kuranda hangi peygamberler var?")
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
    
    if not soru or not isinstance(soru, str):
        result["error"] = "Geçersiz soru. Lütfen bir soru girin."
        return result
    
    try:
        # Sure listesi sayfasından başlangıç bilgileri al
        base_url = "https://www.kuranokuyan.com"
        sure_listesi_url = f"{base_url}/sure-listesi"
        
        resp = requests.get(sure_listesi_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Tüm sure linklerini topla
        sure_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "suresi" in href.lower() or any(c.isdigit() for c in href):
                full_url = href if href.startswith("http") else f"{base_url}{href}"
                sure_links.append({"url": full_url, "sure_adi": text})
        
        # Arama stratejisi: soru tipine göre
        soru_lower = soru.lower()
        arama_sonuclari = []
        
        # Peygamber araması
        if "peygamber" in soru_lower or "nebî" in soru_lower or "resul" in soru_lower:
            peygamber_isimleri = ["musa", "ibrahim", "nuh", "isa", "yusuf", "davud", "süleyman", "yakub", "ishak", "ismail", "harun", "zekeriya", "yahya", "ilyas", "elyesa", "yunus", "lut", "salih", "hud", "şuayb", "eyyub", "zülkifl", "idris", "adem"]
            
            for i, sure_link in enumerate(sure_links[:10]):  # İlk 10 sureyi kontrol et
                try:
                    sure_resp = requests.get(sure_link["url"], timeout=10)
                    sure_resp.raise_for_status()
                    sure_soup = BeautifulSoup(sure_resp.text, "html.parser")
                    sure_text = sure_soup.get_text().lower()
                    
                    bulunan_peygamberler = []
                    for peygamber in peygamber_isimleri:
                        if peygamber in sure_text:
                            bulunan_peygamberler.append(peygamber.title())
                    
                    if bulunan_peygamberler:
                        arama_sonuclari.append({
                            "sure": sure_link["sure_adi"],
                            "bulunan": bulunan_peygamberler,
                            "url": sure_link["url"]
                        })
                except:
                    continue
        
        # Kelime araması (genel)
        elif any(word in soru_lower for word in ["hangi", "nerede", "kaç", "kim"]):
            # Soru içindeki anahtar kelimeleri çıkar
            anahtar_kelimeler = []
            import re
            kelimeler = re.findall(r'\b\w+\b', soru_lower)
            for kelime in kelimeler:
                if len(kelime) > 3 and kelime not in ["hangi", "nerede", "kaçtır", "kadar", "surelerde", "suresi", "kuranda"]:
                    anahtar_kelimeler.append(kelime)
            
            if anahtar_kelimeler:
                for i, sure_link in enumerate(sure_links[:8]):  # İlk 8 sureyi kontrol et
                    try:
                        sure_resp = requests.get(sure_link["url"], timeout=10)
                        sure_resp.raise_for_status()
                        sure_soup = BeautifulSoup(sure_resp.text, "html.parser")
                        sure_text = sure_soup.get_text().lower()
                        
                        bulunan_kelimeler = []
                        for kelime in anahtar_kelimeler:
                            if kelime in sure_text:
                                bulunan_kelimeler.append(kelime)
                        
                        if bulunan_kelimeler:
                            arama_sonuclari.append({
                                "sure": sure_link["sure_adi"],
                                "bulunan_kelimeler": bulunan_kelimeler,
                                "url": sure_link["url"]
                            })
                    except:
                        continue
        
        if not arama_sonuclari:
            result["error"] = f"'{soru}' ile ilgili sonuç bulunamadı. Farklı kelimeler deneyebilirsiniz."
            return result
        
        result["success"] = True
        result["data"] = {
            "soru": soru,
            "bulunan_sonuc_sayisi": len(arama_sonuclari),
            "sonuclar": arama_sonuclari
        }
        return result
        
    except Exception as e:
        result["error"] = f"Araştırma hatası: {str(e)}"
        return result