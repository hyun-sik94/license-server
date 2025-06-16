# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, timedelta
import os
from passlib.context import CryptContext

import models, schemas, database

# models.py에 정의된 테이블들을 실제 데이터베이스 파일에 생성합니다.
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# 비밀번호 암호화 컨텍스트 생성
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB 세션을 가져오는 함수
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 서버가 처음 시작될 때 테스트용 데이터를 생성하는 함수
@app.on_event("startup")
def create_test_data():
    db = database.SessionLocal()
    # 라이선스가 하나도 없으면 테스트 데이터 생성
    if db.query(models.License).count() == 0:
        print("테스트용 라이선스 데이터를 생성합니다.")
        
        # 1년 뒤에 만료되는 'pro' 등급 라이선스 생성
        pro_license = models.License(
            license_key="PRO-XXXX-YYYY-ZZZZ",
            user_id="test_user",
            tier="pro",
            expires_on=date.today() + timedelta(days=365)
        )
        db.add(pro_license)

        # 'pro' 등급에 모든 기능 권한 부여
        pro_permissions = [
            models.Permission(tier="pro", feature_name="like"),
            models.Permission(tier="pro", feature_name="comment"),
            models.Permission(tier="pro", feature_name="reply"),
            models.Permission(tier="pro", feature_name="ai_comment"),
            models.Permission(tier="pro", feature_name="add_neighbor"),
        ]
        db.add_all(pro_permissions)
        db.commit()
    db.close()

# API 1: 라이선스 초기 검증
@app.post("/api/validate_license", response_model=schemas.LicenseStatusResponse)
def validate_license(request: schemas.LicenseRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()

    if not license:
        return {"status": "invalid", "expires_on": None}

    if license.expires_on < date.today():
        return {"status": "expired", "expires_on": str(license.expires_on)}

    return {"status": "valid", "expires_on": str(license.expires_on)}

# API 2: 기능별 권한 확인
@app.post("/api/check_feature", response_model=schemas.FeaturePermissionResponse)
def check_feature(request: schemas.FeatureRequest, db: Session = Depends(get_db)):
    license = db.query(models.License).filter(models.License.license_key == request.license_key).first()
    if not license or license.expires_on < date.today():
        return {"authorized": False}

    permission = db.query(models.Permission).filter(
        models.Permission.tier == license.tier,
        models.Permission.feature_name == request.feature
    ).first()
    
    return {"authorized": bool(permission)}

# API 3: 관리자 로그인 검증
@app.post("/api/admin_login")
def admin_login(request: schemas.AdminLoginRequest):
    # Render 서버에 설정된 환경 변수에서 관리자 정보를 가져옴
    admin_username = os.getenv("ADMIN_USERNAME", "admin") # 없으면 기본값 'admin'
    hashed_password = os.getenv("ADMIN_PASSWORD_HASH") # 반드시 설정해야 함

    if not hashed_password:
        raise HTTPException(status_code=500, detail="서버에 관리자 비밀번호가 설정되지 않았습니다.")

    # 아이디가 일치하고, 비밀번호가 암호화된 값과 일치하는지 확인
    if request.username == admin_username and pwd_context.verify(request.password, hashed_password):
        return {"authenticated": True}
    
    return {"authenticated": False}