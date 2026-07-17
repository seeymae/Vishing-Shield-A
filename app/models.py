"""
Veritabani modelleri.

Tasarim ilkesi: onay (consent) ve yetki (authorization) kayitlari,
kampanya ve cagri denemelerinden ayri, bagimsiz tablolardir. Bir cagri
denemesi asla dogrudan olusturulamaz -- once AuthorizationScope ve
ConsentRecord kontrol edilir (bkz. app/gate.py). Bu ayrim, "onay
kontrolunu atla" seklinde bir kisayolun kod tabaninda var olmasini
mimari olarak imkansiz kilar.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class AuthorizationScope(Base):
    """
    Kurumsal yetki kaydi. Ust yonetim / guvenlik ekibi tarafindan
    imzalanmis yetki belgesinin sisteme girisidir. Bir kampanya,
    gecerli ve suresi dolmamis bir scope'a bagli olmadan calisamaz.
    """
    __tablename__ = "authorization_scopes"

    id = Column(Integer, primary_key=True)
    organization_name = Column(String, nullable=False)
    authorized_by = Column(String, nullable=False)          # yetkiyi veren kisi
    authorization_document_ref = Column(String, nullable=False)  # imzali belge referansi / hash
    department = Column(String, nullable=False)             # hedeflenebilecek departman
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    campaigns = relationship("Campaign", back_populates="scope")


class Employee(Base):
    """Sisteme kayitli calisan. Kendisi opt-in vermeden hedef olamaz."""
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    contact_reference = Column(String, nullable=False)  # dahili sistemdeki referans, ham telefon numarasi degil
    active = Column(Boolean, default=True)

    consents = relationship("ConsentRecord", back_populates="employee")


class ConsentRecord(Base):
    """
    Calisanin bireysel opt-in kaydi. IK politikasi geregi tum
    calisanlar bilgilendirilir; ancak fiilen aranabilmek icin bu
    kayit gereklidir ve calisan istedigi an geri cekebilir.
    """
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    opted_in = Column(Boolean, default=True)
    consent_given_at = Column(DateTime, default=datetime.utcnow)
    consent_withdrawn_at = Column(DateTime, nullable=True)
    policy_version = Column(String, nullable=False)

    employee = relationship("Employee", back_populates="consents")


class Campaign(Base):
    """Bir simulasyon kampanyasi. Daima gecerli bir scope'a baglidir."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True)
    scope_id = Column(Integer, ForeignKey("authorization_scopes.id"), nullable=False)
    name = Column(String, nullable=False)
    scenario_template = Column(String, nullable=False)  # config/scenarios/*.json referansi
    status = Column(String, default="draft")  # draft, active, completed, aborted
    created_at = Column(DateTime, default=datetime.utcnow)

    scope = relationship("AuthorizationScope", back_populates="campaigns")
    attempts = relationship("CallAttempt", back_populates="campaign")


class CallAttempt(Base):
    """
    Tek bir simule cagri denemesinin SONUCU.

    KRITIK: burada hicbir gercek OTP/dogrulama kodu, ham konusma
    metni veya telefon numarasi SAKLANMAZ. Sadece davranissal
    meta-etiketler tutulur.
    """
    __tablename__ = "call_attempts"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    outcome = Column(String, nullable=False, default="pending")
    # pending | reported_suspicious | hung_up | no_answer | code_shared

    digits_detected = Column(Boolean, default=False)   # sadece evet/hayir
    digit_count = Column(Integer, nullable=True)        # sadece uzunluk, deger degil
    time_to_outcome_seconds = Column(Integer, nullable=True)

    campaign = relationship("Campaign", back_populates="attempts")


class AuditLogEntry(Base):
    """Her onay/yetki/cagri kararinin degistirilemez izi."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    detail = Column(Text, nullable=True)