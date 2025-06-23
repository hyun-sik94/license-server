# schemas.py (수정)
from pydantic import BaseModel
from datetime import date

# --- 클라이언트용 스키마 ---
class LicenseRequest(BaseModel):
    license_key: str

class LicenseStatusResponse(BaseModel):
    status: str
    expires_on: str | None = None
    features: list[str] = []

# --- 관리 도구용 스키마 ---
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class LicenseData(BaseModel):
    license_key: str
    expires_on: date
    user_id: str | None = None
    features: list[str] = []

    class Config:
        from_attributes = True

class CreateLicenseRequest(BaseModel):
    days: int
    user_id: str | None = None

class ExtendLicenseRequest(BaseModel):
    license_key: str
    days: int

class SavePermissionsRequest(BaseModel):
    features: list[str]

class SetExpiryRequest(BaseModel):
    license_key: str
    expires_on: date # 날짜 형식을 직접 받도록 설정