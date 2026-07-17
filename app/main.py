from datetime import datetime
from typing import Optional # Bunu ekle
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form # Bunları ekle
from sqlalchemy.orm import Session
from app.services.stt_service import transcribe_audio # Bunu mutlaka ekle

# ... geri kalan importların ...
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import init_db, get_db
from app import models, schemas, reporting
from app.gate import GateDenied
from app.call_engine import run_simulated_call, keyboard_transcript_source

app = FastAPI(
    title="Vishing-Shield AI",
    description="Onay tabanli (consent-first) vishing simulasyon ve egitim platformu",
    version="0.1.0",
)


@app.on_event("startup")
def on_startup():
    init_db()


# ---------- Yetki (scope) ----------

@app.post("/scopes", response_model=schemas.AuthorizationScopeOut)
def create_scope(scope: schemas.AuthorizationScopeCreate, db: Session = Depends(get_db)):
    obj = models.AuthorizationScope(**scope.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.post("/scopes/{scope_id}/revoke")
def revoke_scope(scope_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.AuthorizationScope).get(scope_id)
    if not obj:
        raise HTTPException(404, "Scope bulunamadi")
    obj.revoked = True
    db.commit()
    return {"status": "revoked"}


# ---------- Calisanlar ve onay ----------

@app.post("/employees", response_model=schemas.EmployeeOut)
def create_employee(emp: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    obj = models.Employee(**emp.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.post("/consent", response_model=schemas.ConsentOut)
def give_consent(consent: schemas.ConsentCreate, db: Session = Depends(get_db)):
    obj = models.ConsentRecord(opted_in=True, **consent.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.post("/consent/{consent_id}/withdraw")
def withdraw_consent(consent_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.ConsentRecord).get(consent_id)
    if not obj:
        raise HTTPException(404, "Onay kaydi bulunamadi")
    obj.consent_withdrawn_at = datetime.utcnow()
    obj.opted_in = False
    db.commit()
    return {"status": "withdrawn"}


# ---------- Kampanyalar ----------

@app.post("/campaigns", response_model=schemas.CampaignOut)
def create_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    scope = db.query(models.AuthorizationScope).get(campaign.scope_id)
    if not scope or scope.revoked:
        raise HTTPException(400, "Gecerli bir yetki kaydi (scope) olmadan kampanya olusturulamaz")
    obj = models.Campaign(status="draft", **campaign.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@app.post("/campaigns/{campaign_id}/activate")
def activate_campaign(campaign_id: int, db: Session = Depends(get_db)):
    obj = db.query(models.Campaign).get(campaign_id)
    if not obj:
        raise HTTPException(404, "Kampanya bulunamadi")
    obj.status = "active"
    db.commit()
    return {"status": "active"}


# ---------- Simule cagri tetikleme (demo amacli, klavye girdili) ----------

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from typing import Optional
import os

# Kendi servislerini import et
from app.services.stt_service import transcribe_audio
from app.services.fraud_detection_service import analyze_text_for_fraud

# ... (diğer importların buraya gelecek)

@app.post("/campaigns/{campaign_id}/simulate-call/{employee_id}")
async def simulate_call(
    campaign_id: int,
    employee_id: int,
    text_input: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None)
):
    user_input = ""

    # 1. Eğer ses dosyası yüklendiyse, onu metne çevir
    if audio_file:
        temp_path = f"temp_{audio_file.filename}"
        with open(temp_path, "wb") as buffer:
            buffer.write(await audio_file.read())
        
        # Whisper ile metne çevir
        user_input = transcribe_audio(temp_path)
        
        # İşlem bitince geçici dosyayı temizle (Opsiyonel ama iyi bir pratik!)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    # 2. Eğer metin girildiyse, onu kullan
    elif text_input:
        user_input = text_input
    
    else:
        raise HTTPException(status_code=400, detail="Lütfen metin veya ses dosyası gönderin.")

    # 3. ANALİZ: Gelen metni fraud servisimize gönder
    fraud_result = analyze_text_for_fraud(user_input)
    
    # 4. SONUÇ: Hem metni hem de analiz raporunu döndür
    return {
        "received_input": user_input,
        "fraud_analysis": fraud_result,
        "status": "processed"
    }

# ---------- Raporlama ----------

@app.get("/reports/campaigns/{campaign_id}")
def campaign_report(campaign_id: int, db: Session = Depends(get_db)):
    return reporting.campaign_summary(db, campaign_id)


@app.get("/reports/departments")
def department_report(db: Session = Depends(get_db)):
    return reporting.department_risk_breakdown(db)