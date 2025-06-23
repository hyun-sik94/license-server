# main.py (MAC 주소 인증 기능 추가 버전)
import os, uuid
from datetime import date, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas, database

models.Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버가 시작되었습니다. 데이터베이스를 확인합니다.")
    db = database.SessionLocal()
    if db.query(models.License).count() == 0:
        print("테스트용 라이선스 데이터를 생성합니다.")
        new_key = "PRO-XXXX-YYYY-ZZZZ"
        pro_license = models.License(license_key=new_key, user_id="test_user", expires_on=date.today() + timedelta(days=365))
        db.add(pro_license)
        features = ['like', 'comment', 'reply', 'ai_comment', 'add_neighbor']
        pro_permissions = [models.Permission(license_key=new_key, feature_name=f) for f in features]
        db.add_all(pro_permissions)
        db.commit()
    db.close()
    yield
    print("서버가 종료됩니다.")

app = FastAPI(lifespan=lifespan)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = database.SessionLocal()
    try: yield db
    finally: db.close()

async def verify_admin_secret(x_admin_secret: str = Header(None)):
    admin_secret = os.getenv("ADMIN_SECRET_KEY")
    if not admin_secret or x_admin_secret != admin_secret:
        raise HTTPException(status_code=403, detail="관리자 인증에 실패했습니다.")
    return True

# --- 클라이언트용 API ---
@app.post("/api/validate_license", response_model=schemas.LicenseStatusResponse)
def validate_license(request: schemas.LicenseRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()
    if not license: return {"status": "invalid", "features": []}
    if license.expires_on < date.today(): return {"status": "expired", "expires_on": str(license.expires_on), "features": []}
    
    # <<<< 핵심: MAC 주소 검증 로직 >>>>
    if license.registered_mac is None or license.registered_mac == "":
        # 1. 최초 사용: DB에 MAC 주소 등록
        license.registered_mac = request.mac_address
        db.commit()
    elif license.registered_mac != request.mac_address:
        # 2. 등록된 MAC과 불일치: 오류 반환
        return {"status": "mismatch", "features": []}
    
    # 3. 일치하거나, 방금 등록됨: 성공 처리
    allowed_features = [p.feature_name for p in license.permissions]
    return {"status": "valid", "expires_on": str(license.expires_on), "features": allowed_features}

# --- 관리 도구용 API ---
@app.post("/api/admin_login")
def admin_login(request: schemas.AdminLoginRequest):
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    hashed_password = os.getenv("ADMIN_PASSWORD_HASH")
    if not hashed_password: raise HTTPException(status_code=500, detail="서버에 관리자 비밀번호가 설정되지 않았습니다.")
    if request.username == admin_username and pwd_context.verify(request.password, hashed_password): return {"authenticated": True}
    return {"authenticated": False}

@app.get("/api/admin/licenses", response_model=list[schemas.LicenseData], dependencies=[Depends(verify_admin_secret)])
def list_all_licenses(db: Session = Depends(get_db)):
    licenses = db.query(models.License).all()
    results = []
    for lic in licenses:
        features = [p.feature_name for p in lic.permissions]
        results.append(schemas.LicenseData(license_key=lic.license_key, expires_on=lic.expires_on, user_id=lic.user_id, features=features, registered_mac=lic.registered_mac))
    return results

# ... (create_new_license, extend_existing_license, delete_license, set_license_expiry, save_permissions_for_license 함수들은 기존과 동일) ...
@app.post("/api/admin/create_license", response_model=schemas.LicenseData, dependencies=[Depends(verify_admin_secret)])
def create_new_license(request: schemas.CreateLicenseRequest, db: Session = Depends(get_db)):
    new_key = "NEW-" + str(uuid.uuid4()).split('-')[0].upper()
    expires_on = date.today() + timedelta(days=request.days)
    new_license = models.License(license_key=new_key, expires_on=expires_on, user_id=request.user_id)
    db.add(new_license)
    db.commit(); db.refresh(new_license)
    features = [p.feature_name for p in new_license.permissions]
    return schemas.LicenseData(license_key=new_license.license_key, expires_on=new_license.expires_on, user_id=new_license.user_id, features=features, registered_mac=new_license.registered_mac)

@app.post("/api/admin/extend_license", response_model=schemas.LicenseData, dependencies=[Depends(verify_admin_secret)])
def extend_existing_license(request: schemas.ExtendLicenseRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()
    if not license: raise HTTPException(status_code=404, detail="라이선스 키를 찾을 수 없습니다.")
    license.expires_on += timedelta(days=request.days)
    db.commit(); db.refresh(license)
    features = [p.feature_name for p in license.permissions]
    return schemas.LicenseData(license_key=license.license_key, expires_on=license.expires_on, user_id=license.user_id, features=features, registered_mac=license.registered_mac)

@app.post("/api/admin/set_expiry", response_model=schemas.LicenseData, dependencies=[Depends(verify_admin_secret)])
def set_license_expiry(request: schemas.SetExpiryRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()
    if not license: raise HTTPException(status_code=404, detail="라이선스 키를 찾을 수 없습니다.")
    license.expires_on = request.expires_on
    db.commit(); db.refresh(license)
    features = [p.feature_name for p in license.permissions]
    return schemas.LicenseData(license_key=license.license_key, expires_on=license.expires_on, user_id=license.user_id, features=features, registered_mac=license.registered_mac)

@app.delete("/api/admin/licenses/{license_key}", status_code=204, dependencies=[Depends(verify_admin_secret)])
def delete_license(license_key: str, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == license_key).first()
    if not license: raise HTTPException(status_code=404, detail="삭제할 라이선스 키를 찾을 수 없습니다.")
    db.query(models.Permission).filter(models.Permission.license_key == license_key).delete(synchronize_session=False)
    db.delete(license)
    db.commit()
    return

@app.post("/api/admin/permissions/{license_key}", response_model=list[str], dependencies=[Depends(verify_admin_secret)])
def save_permissions_for_license(license_key: str, request: schemas.SavePermissionsRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == license_key).first()
    if not license: raise HTTPException(status_code=404, detail="라이선스 키를 찾을 수 없습니다.")
    db.query(models.Permission).filter(models.Permission.license_key == license_key).delete()
    for feature in request.features: db.add(models.Permission(license_key=license_key, feature_name=feature))
    db.commit()
    return request.features

# <<<< 새로 추가된 MAC 주소 초기화 API >>>>
@app.post("/api/admin/reset_mac", response_model=schemas.LicenseData, dependencies=[Depends(verify_admin_secret)])
def reset_mac_address(request: schemas.ResetMacRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()
    if not license: raise HTTPException(status_code=404, detail="라이선스 키를 찾을 수 없습니다.")
    
    license.registered_mac = None # MAC 주소를 비움
    db.commit()
    db.refresh(license)
    
    features = [p.feature_name for p in license.permissions]
    return schemas.LicenseData(license_key=license.license_key, expires_on=license.expires_on, user_id=license.user_id, features=features, registered_mac=license.registered_mac)