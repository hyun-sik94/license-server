# schemas.py
from pydantic import BaseModel

# 라이선스 검증 요청 시 Body 형식
class LicenseRequest(BaseModel):
    license_key: str

# 기능 권한 확인 요청 시 Body 형식
class FeatureRequest(BaseModel):
    license_key: str
    feature: str

# 라이선스 상태 응답 형식
class LicenseStatusResponse(BaseModel):
    status: str
    expires_on: str | None = None

# 기능 권한 응답 형식
class FeaturePermissionResponse(BaseModel):
    authorized: bool

class AdminLoginRequest(BaseModel):
    username: str
    password: str