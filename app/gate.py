"""
Onay kapisi (consent gate).

Bu modul, projenin tum guvenlik/etik garantisinin dayandigi yerdir.
KURAL: call_engine.py, bu modulun disinda hicbir yoldan cagrilamaz.
Baska hicbir modul CallAttempt olusturma yetkisine sahip degildir.

Eger bu dosyayi degistiriyorsan: "onay kontrolunu atla" seklinde bir
parametre, bayrak veya debug modu EKLEME. Boyle bir kisayol projenin
tasarim ilkesini kirar.
"""
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models import AuthorizationScope, ConsentRecord, Employee, Campaign, AuditLogEntry


class GateDenied(Exception):
    """Onay kapisi bir cagri denemesini reddettiginde firlatilir."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


@dataclass
class GateResult:
    allowed: bool
    scope_id: int
    employee_id: int
    reason: str = "ok"


def _log(db: Session, actor: str, action: str, detail: str):
    db.add(AuditLogEntry(actor=actor, action=action, detail=detail))
    db.commit()


def check_can_call(db: Session, campaign_id: int, employee_id: int, actor: str = "system") -> GateResult:
    """
    Bir calisanin belirli bir kampanya kapsaminda aranip
    aranamayacagini denetler. Asagidaki kosullarin TAMAMI saglanmadan
    True donmez:

      1. Kampanya var ve 'active' durumunda
      2. Kampanyanin bagli oldugu AuthorizationScope gecerli
         (revoked degil, tarih araligi icinde)
      3. Calisan aktif ve kampanyanin scope'undaki departmanda
      4. Calisanin gecerli, geri cekilmemis bir ConsentRecord'u var
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if campaign is None:
        _log(db, actor, "gate_denied", f"campaign {campaign_id} not found")
        raise GateDenied("Kampanya bulunamadi")

    if campaign.status != "active":
        _log(db, actor, "gate_denied", f"campaign {campaign_id} status={campaign.status}")
        raise GateDenied("Kampanya aktif degil")

    scope = db.query(AuthorizationScope).filter(
        AuthorizationScope.id == campaign.scope_id
    ).first()

    now = datetime.utcnow()
    if scope is None or scope.revoked:
        _log(db, actor, "gate_denied", f"scope missing or revoked for campaign {campaign_id}")
        raise GateDenied("Yetki kaydi gecersiz veya iptal edilmis")

    if not (scope.valid_from <= now <= scope.valid_until):
        _log(db, actor, "gate_denied", f"scope {scope.id} outside valid date range")
        raise GateDenied("Yetki belgesinin tarih araligi disinda")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if employee is None or not employee.active:
        _log(db, actor, "gate_denied", f"employee {employee_id} inactive or missing")
        raise GateDenied("Calisan aktif degil veya bulunamadi")

    if employee.department != scope.department:
        _log(db, actor, "gate_denied",
             f"employee dept {employee.department} != scope dept {scope.department}")
        raise GateDenied("Calisan yetki kapsamindaki departmanda degil")

    consent = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.employee_id == employee_id)
        .order_by(ConsentRecord.consent_given_at.desc())
        .first()
    )
    if consent is None or not consent.opted_in or consent.consent_withdrawn_at is not None:
        _log(db, actor, "gate_denied", f"employee {employee_id} has no active consent")
        raise GateDenied("Calisanin gecerli onayi yok")

    _log(db, actor, "gate_allowed", f"campaign={campaign_id} employee={employee_id}")
    return GateResult(allowed=True, scope_id=scope.id, employee_id=employee_id)