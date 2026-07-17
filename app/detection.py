"""
Tespit motoru.

KRITIK GUVENLIK KURALI: Bu modul konusma metnini SADECE bellekte,
tek bir fonksiyon cagrisi suresince tutar. Herhangi bir rakam dizisi
(simule OTP kodu) tespit edildiginde, DEGERI DEGIL, sadece varligini
ve uzunlugunu iceren bir DetectionResult uretilir. Ham metin bu
fonksiyonun disina asla cikarilmaz -- cagiran kod (call_engine.py)
sadece donen DetectionResult'i loglar.

Eger bu dosyayi genisletiyorsan: raw_text alanini bir donus degerine,
log kaydina veya veritabani sutununa EKLEME.
"""
import re
from dataclasses import dataclass

DIGIT_SEQUENCE_PATTERN = re.compile(r"\d{3,8}")  # tipik OTP uzunluk araligi


@dataclass
class DetectionResult:
    digits_detected: bool
    digit_count: int | None  # sadece uzunluk, deger degil
    category: str            # "code_shared" | "no_sensitive_data" | "refused"


REFUSAL_MARKERS = (
    "vermiyorum", "paylasmiyorum", "kapatiyorum", "guvenmiyorum", "sahtekarlik",
)


def analyze_transcript(raw_text: str) -> DetectionResult:
    """
    raw_text: Speech-to-Text ciktisi, sadece bu fonksiyon icinde yasar.
    Donen DetectionResult disinda hicbir sey saklanmamalidir.
    """
    lowered = raw_text.lower()

    if any(marker in lowered for marker in REFUSAL_MARKERS):
        return DetectionResult(digits_detected=False, digit_count=None, category="refused")

    match = DIGIT_SEQUENCE_PATTERN.search(raw_text)
    if match:
        # SADECE uzunluk aliniyor -- match.group() (gercek deger) hicbir yere yazilmiyor
        return DetectionResult(
            digits_detected=True,
            digit_count=len(match.group()),
            category="code_shared",
        )

    return DetectionResult(digits_detected=False, digit_count=None, category="no_sensitive_data")