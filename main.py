# main.py
import os
from datetime import date, timedelta
import uuid

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models, schemas, database

models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def verify_admin_secret(x_admin_secret: str = Header(None)):
    admin_secret = os.getenv("ADMIN_SECRET_KEY")
    if not admin_secret or x_admin_secret != admin_secret:
        raise HTTPException(status_code=403, detail="관리자 인증에 실패했습니다.")
    return True

@app.on_event("startup")
def create_test_data():
    db = database.SessionLocal()
    if db.query(models.License).count() == 0:
        print("테스트용 라이선스 데이터를 생성합니다.")
        pro_license = models.License(license_key="PRO-XXXX-YYYY-ZZZZ", user_id="test_user", tier="pro", expires_on=date.today() + timedelta(days=365))
        db.add(pro_license)
        pro_permissions = [models.Permission(tier="pro", feature_name=f) for f in ['like', 'comment', 'reply', 'ai_comment', 'add_neighbor']]
        db.add_all(pro_permissions)
        db.commit()
    db.close()

@app.post("/api/validate_license", response_model=schemas.LicenseStatusResponse)
def validate_license(request: schemas.LicenseRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()
    if not license: return {"status": "invalid", "expires_on": None, "features": []}
    if license.expires_on < date.today(): return {"status": "expired", "expires_on": str(license.expires_on), "features": []}
    permissions = db.query(models.Permission).filter(models.Permission.tier == license.tier).all()
    allowed_features = [p.feature_name for p in permissions]
    return {"status": "valid", "expires_on": str(license.expires_on), "features": allowed_features}

@app.post("/api/admin_login")
def admin_login(request: schemas.AdminLoginRequest):
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    hashed_password = os.getenv("ADMIN_PASSWORD_HASH")
    if not hashed_password: raise HTTPException(status_code=500, detail="서버에 관리자 비밀번호가 설정되지 않았습니다.")
    if request.username == admin_username and pwd_context.verify(request.password, hashed_password): return {"authenticated": True}
    return {"authenticated": False}

@app.get("/api/admin/licenses", response_model=list[schemas.LicenseData], dependencies=[Depends(verify_admin_secret)])
def list_all_licenses(db: Session = Depends(get_db)):
    return db.query(models.License).all()

@app.post("/api/admin/create_license", response_model=schemas.LicenseData, dependencies=[Depends(verify_admin_secret)])
def create_new_license(request: schemas.CreateLicenseRequest, db: Session = Depends(get_db)):
    new_key = "NEW-" + str(uuid.uuid4()).split('-')[0].upper()
    expires_on = date.today() + timedelta(days=request.days)
    new_license = models.License(license_key=new_key, tier=request.tier, expires_on=expires_on, user_id=request.user_id)
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return new_license

@app.post("/api/admin/extend_license", response_model=schemas.LicenseData, dependencies=[Depends(verify_admin_secret)])
def extend_existing_license(request: schemas.ExtendLicenseRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()
    if not license: raise HTTPException(status_code=404, detail="라이선스 키를 찾을 수 없습니다.")
    license.expires_on += timedelta(days=request.days)
    db.commit()
    db.refresh(license)
    return license

@app.get("/api/admin/permissions/{tier}", response_model=schemas.TierPermissionResponse, dependencies=[Depends(verify_admin_secret)])
def get_permissions_for_tier(tier: str, db: Session = Depends(get_db)):
    permissions = db.query(models.Permission).filter(models.Permission.tier == tier).all()
    return {"tier": tier, "permissions": [p.feature_name for p in permissions]}

@app.post("/api/admin/save_permissions", response_model=schemas.TierPermissionResponse, dependencies=[Depends(verify_admin_secret)])
def save_permissions_for_tier(request: schemas.SavePermissionsRequest, db: Session = Depends(get_db)):
    db.query(models.Permission).filter(models.Permission.tier == request.tier).delete()
    db.commit()
    for feature in request.features:
        db.add(models.Permission(tier=request.tier, feature_name=feature))
    db.commit()
    return {"tier": request.tier, "permissions": request.features}