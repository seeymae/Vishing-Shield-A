from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import CallAttempt


def campaign_summary(db: Session, campaign_id: int) -> dict:
    attempts = db.query(CallAttempt).filter(CallAttempt.campaign_id == campaign_id).all()
    total = len(attempts)
    if total == 0:
        return {"campaign_id": campaign_id, "total_attempts": 0}

    code_shared = sum(1 for a in attempts if a.outcome == "code_shared")
    reported = sum(1 for a in attempts if a.outcome == "reported_suspicious")
    hung_up = sum(1 for a in attempts if a.outcome == "hung_up")

    avg_time = (
        sum(a.time_to_outcome_seconds or 0 for a in attempts) / total
        if total else 0
    )

    return {
        "campaign_id": campaign_id,
        "total_attempts": total,
        "code_shared_rate": round(code_shared / total, 3),
        "reported_suspicious_rate": round(reported / total, 3),
        "hung_up_rate": round(hung_up / total, 3),
        "avg_time_to_outcome_seconds": round(avg_time, 1),
    }


def department_risk_breakdown(db: Session) -> list[dict]:
    """Departman bazinda risk orani -- bireysel calisan ifsa etmez."""
    from app.models import Employee

    rows = (
        db.query(Employee.department, CallAttempt.outcome, func.count(CallAttempt.id))
        .join(CallAttempt, CallAttempt.employee_id == Employee.id)
        .group_by(Employee.department, CallAttempt.outcome)
        .all()
    )

    breakdown: dict[str, dict[str, int]] = {}
    for department, outcome, count in rows:
        breakdown.setdefault(department, {}).setdefault(outcome, 0)
        breakdown[department][outcome] += count

    result = []
    for department, outcomes in breakdown.items():
        total = sum(outcomes.values())
        code_shared = outcomes.get("code_shared", 0)
        result.append({
            "department": department,
            "total_attempts": total,
            "code_shared_rate": round(code_shared / total, 3) if total else 0,
        })
    return result