import re

def analyze_text_for_fraud(text: str):
    # Tespit edilecek hassas anahtar kelimeler
    keywords = ["şifre", "kod", "kart", "numara", "doğrulama", "cvv", "hesap"]
    
    # Metin içinde 4 veya daha fazla ardışık sayı var mı? (Örn: Kart veya SMS kodu)
    # Bu regex, 4 ile 16 hane arasındaki sayıları yakalar.
    sensitive_number_pattern = r'\b\d{4,16}\b'
    
    found_keywords = [word for word in keywords if word in text.lower()]
    found_numbers = re.findall(sensitive_number_pattern, text)
    
    risk_level = "Low"
    alert = False
    
    # Eğer hem bir anahtar kelime hem de sayı tespit edilirse risk yüksek!
    if found_keywords and found_numbers:
        risk_level = "Critical"
        alert = True
    elif found_keywords:
        risk_level = "Medium"
        alert = True
        
    return {
        "alert": alert,
        "risk_level": risk_level,
        "detected_keywords": found_keywords,
        "detected_sensitive_data": found_numbers
    }