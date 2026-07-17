"""
Cagri motoru.

Bu modulun tek public fonksiyonu run_simulated_call() DAIMA once
app.gate.check_can_call() cagirir. Bu kontrolden gecmeden
CallAttempt olusturulamaz.

Iki calisma modu:
  - "local"  : ses dosyasi bilgisayarda calinir, kullanicidan (test
               amacli) klavye ile yanit alinir. Gelistirme/demo icin.
  - "twilio" : gercek telefon aramasi icin adaptor. Bu repo Twilio
               kimlik bilgisi icermez; production'a alirken kendi
               Twilio hesabinizi TWILIO_* ortam degiskenleriyle
               baglamaniz gerekir. Bkz. README "Telefon entegrasyonu".
"""
import os
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.gate import check_can_call, GateDenied
from app.detection import analyze_transcript
from app.models import CallAttempt, Campaign

SCENARIO_DIR = os.path.join(os.path.dirname(__file__), "..", "config", "scenarios")


def _load_scenario(name: str) -> dict:
    path = os.path.join(SCENARIO_DIR, f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_simulated_call(db: Session, campaign_id: int, employee_id: int, transcript_source) -> CallAttempt:
    """
    transcript_source: cagrilabilir bir fonksiyon, str dondurur.
    Local modda input() ile klavyeden, Twilio modunda Speech-to-Text
    servisinden gelen metni saglar. Bu fonksiyon disinda ham metin
    hicbir yere yazilmaz.
    """
    # 1) ONAY KAPISI -- bypass edilemez
    gate_result = check_can_call(db, campaign_id=campaign_id, employee_id=employee_id, actor="call_engine")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    scenario = _load_scenario(campaign.scenario_template)

    attempt = CallAttempt(
        campaign_id=campaign_id,
        employee_id=employee_id,
        started_at=datetime.utcnow(),
        outcome="pending",
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    print(f"[senaryo] {scenario['prompt_text']}")

    raw_text = transcript_source()  # yalnizca bu satirin kapsaminda yasar
    result = analyze_transcript(raw_text)
    del raw_text  # acik referans temizligi

    attempt.ended_at = datetime.utcnow()
    attempt.digits_detected = result.digits_detected
    attempt.digit_count = result.digit_count
    attempt.time_to_outcome_seconds = int((attempt.ended_at - attempt.started_at).total_seconds())

    if result.category == "code_shared":
        attempt.outcome = "code_shared"
    elif result.category == "refused":
        attempt.outcome = "reported_suspicious"
    else:
        attempt.outcome = "hung_up"

    db.commit()
    db.refresh(attempt)
    return attempt


def keyboard_transcript_source():
    """Yerel demo icin: gercek konusma yerine klavyeden metin alir."""
    return input("Simule yanit girin (STT ciktisi yerine): ")