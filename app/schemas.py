from datetime import datetime
from pydantic import BaseModel


class AuthorizationScopeCreate(BaseModel):
    organization_name: str
    authorized_by: str
    authorization_document_ref: str
    department: str
    valid_from: datetime
    valid_until: datetime


class AuthorizationScopeOut(AuthorizationScopeCreate):
    id: int
    revoked: bool

    class Config:
        from_attributes = True


class EmployeeCreate(BaseModel):
    full_name: str
    department: str
    contact_reference: str


class EmployeeOut(EmployeeCreate):
    id: int
    active: bool

    class Config:
        from_attributes = True


class ConsentCreate(BaseModel):
    employee_id: int
    policy_version: str


class ConsentOut(BaseModel):
    id: int
    employee_id: int
    opted_in: bool
    consent_given_at: datetime
    consent_withdrawn_at: datetime | None

    class Config:
        from_attributes = True


class CampaignCreate(BaseModel):
    scope_id: int
    name: str
    scenario_template: str


class CampaignOut(CampaignCreate):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CallAttemptOut(BaseModel):
    id: int
    campaign_id: int
    employee_id: int
    outcome: str
    digits_detected: bool
    digit_count: int | None
    time_to_outcome_seconds: int | None

    class Config:
        from_attributes = True