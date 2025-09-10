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
        
        # Sure adlarını ve bilgilerini sadece bu sayfadan al
        sure_found = False
        sure_details = {
            "sure_adi": sure_name,
            "kaynak_url": url
        }
        
        # Sayfadaki tüm linkleri ve metinleri tara
        sure_link = None
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if text.lower() == sure_name.lower() or text.lower() == sure_name.lower().replace(" suresi",""):
                sure_found = True
                sure_link = a["href"]
                sure_details["sure_linki"] = sure_link
                
                # Aynı satırdaki bilgileri al (numarası, ayet sayısı vs.)
                parent = a.parent
                if parent:
                    parent_text = parent.get_text(strip=True)
                    
                    # Sure numarası ve ayet sayısı çıkar
                    import re
                    # Örnek: "1 Fâtiha 7 Ayet" veya "2 Bakara 286 Ayet"
                    match = re.search(r'(\d+)\s*' + re.escape(text) + r'\s*(\d+)\s*Ayet', parent_text, re.IGNORECASE)
                    if match:
                        sure_details["sure_numarasi"] = int(match.group(1))
                        sure_details["ayet_sayisi"] = int(match.group(2))
                
                # Çevre metinden ek bilgi al
                siblings = parent.find_next_siblings() if parent else []
                for sibling in siblings[:3]:  # Yakındaki 3 elementi kontrol et
                    sibling_text = sibling.get_text(strip=True) if hasattr(sibling, 'get_text') else str(sibling).strip()
                    if sibling_text and len(sibling_text) > 10:
                        if "Mekkî" in sibling_text or "Medenî" in sibling_text:
                            sure_details["iniş_yeri"] = "Mekke" if "Mekkî" in sibling_text else "Medine"
                        if len(sibling_text) > 50:  # Uzun metin açıklama olabilir
                            sure_details["liste_sayfasi_aciklamasi"] = sibling_text[:200] + "..." if len(sibling_text) > 200 else sibling_text
                
                break
        
        if not sure_found:
            result["error"] = f"'{sure_name}' adlı sure bulunamadı."
            return result
            
        # Sayfa içindeki genel açıklamalardan sure ile ilgili bilgi bul
        all_text = soup.get_text()
        if sure_name.lower() in all_text.lower():
            # Sure adının geçtiği paragrafları bul
            paragraphs = soup.find_all("p")
            for p in paragraphs:
                p_text = p.get_text(strip=True)
                if sure_name.lower() in p_text.lower() and len(p_text) > 30:
                    sure_details["sayfa_aciklamasi"] = p_text
                    break
        
        # Şimdi sure detay sayfasından açıklama ve ayetleri al
        if sure_link:
            sure_url = sure_link if sure_link.startswith("http") else f"https://www.kuranokuyan.com{sure_link}"
            try:
                sure_resp = requests.get(sure_url, timeout=15)
                sure_resp.raise_for_status()
                sure_soup = BeautifulSoup(sure_resp.text, "html.parser")
                
                # Sure açıklamasını bul
                sure_aciklama = None
                
                # Farklı class isimleri dene
                for class_name in ["sure-aciklama", "aciklama", "sure-tanitim", "meal", "sure-meal"]:
                    aciklama_div = sure_soup.find("div", class_=class_name)
                    if aciklama_div:
                        sure_aciklama = aciklama_div.get_text(strip=True)
                        break
                
                # Alternatif: title altındaki ilk paragraf
                if not sure_aciklama:
                    title = sure_soup.find("title")
                    if title:
                        title_parent = title.parent
                        if title_parent:
                            next_p = title_parent.find_next("p")
                            if next_p:
                                sure_aciklama = next_p.get_text(strip=True)
                
                # Alternatif: h1 altındaki ilk div veya p
                if not sure_aciklama:
                    h1 = sure_soup.find("h1")
                    if h1:
                        next_element = h1.find_next(["div", "p"])
                        if next_element and len(next_element.get_text(strip=True)) > 50:
                            sure_aciklama = next_element.get_text(strip=True)
                
                if sure_aciklama:
                    sure_details["siteden_aciklama"] = sure_aciklama
                
                # Ayetleri bul
                ayetler = []
                
                # Ayet class'larını dene
                for ayet_class in ["ayet", "verse", "ayah", "ayet-metin"]:
                    ayet_divs = sure_soup.find_all("div", class_=ayet_class)
                    if ayet_divs:
                        for i, ayet_div in enumerate(ayet_divs[:10], 1):  # İlk 10 ayeti al
                            ayet_text = ayet_div.get_text(strip=True)
                            if len(ayet_text) > 10:  # Çok kısa metinleri atla
                                ayetler.append({
                                    "ayet_no": i,
                                    "metin": ayet_text
                                })
                        break
                
                # Alternatif: p tag'leri içinde ayet ara
                if not ayetler:
                    p_tags = sure_soup.find_all("p")
                    ayet_no = 1
                    for p in p_tags:
                        p_text = p.get_text(strip=True)
                        # Ayet benzeri uzun metinleri al (en az 20 karakter)
                        if len(p_text) > 20 and ayet_no <= 10:
                            ayetler.append({
                                "ayet_no": ayet_no,
                                "metin": p_text
                            })
                            ayet_no += 1
                
                if ayetler:
                    sure_details["ayetler"] = ayetler
                    sure_details["gosterilen_ayet_sayisi"] = len(ayetler)
                
            except Exception as e:
                sure_details["ayet_hatasi"] = f"Ayetler alınamadı: {str(e)}"
            
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