# schemas.py
from pydantic import BaseModel
from datetime import date

class LicenseRequest(BaseModel):
    license_key: str

class FeatureRequest(BaseModel):
    license_key: str
    feature: str

class LicenseStatusResponse(BaseModel):
    status: str
    expires_on: str | None = None
    features: list[str] = []

class FeaturePermissionResponse(BaseModel):
    authorized: bool

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class LicenseData(BaseModel):
    license_key: str
    tier: str
    expires_on: date
    user_id: str | None = None
    class Config: from_attributes = True

class PermissionData(BaseModel):
    feature_name: str

class TierPermissionResponse(BaseModel):
    tier: str
    permissions: list[str]

class CreateLicenseRequest(BaseModel):
    tier: str
    days: int
    user_id: str | None = None

class ExtendLicenseRequest(BaseModel):
    license_key: str
    days: int

class SavePermissionsRequest(BaseModel):
    tier: str
    features: list[str]