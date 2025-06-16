# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
import models, schemas, database

# models.py에 정의된 테이블들을 실제 데이터베이스 파일에 생성합니다.
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

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
    if db.query(models.License).count() == 0:
        print("테스트용 라이선스 데이터를 생성합니다.")
        
        pro_license = models.License(
            license_key="PRO-XXXX-YYYY-ZZZZ",
            user_id="test_user",
            tier="pro",
            expires_on=date.today() + timedelta(days=365) # 1년 뒤 만료
        )
        db.add(pro_license)

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