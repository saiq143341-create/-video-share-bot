import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tracker.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Device(Base):
    __tablename__ = "devices"
    imei = Column(String, primary_key=True, index=True)
    owner_id = Column(Integer, nullable=False)
    battery = Column(Integer, default=100)
    is_online = Column(Boolean, default=False)
    gps_enabled = Column(Boolean, default=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    gps_request_pending = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FastAPI App ---
app = FastAPI(title="Tablet Tracker API")
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "my_super_secret_key")

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Secret Key")

@app.post("/api/v1/update", dependencies=[Depends(verify_api_key)])
async def update_device_status(data: dict, db: Session = Depends(get_db)):
    imei = data.get("imei")
    if not imei:
        raise HTTPException(status_code=400, detail="IMEI is required")
    
    device = db.query(Device).filter(Device.imei == imei).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not registered via Bot yet")
    
    device.battery = data.get("battery", device.battery)
    device.is_online = True
    device.gps_enabled = data.get("gps_enabled", False)
    device.last_updated = datetime.utcnow()
    
    if device.gps_enabled:
        device.latitude = data.get("latitude")
        device.longitude = data.get("longitude")
        device.gps_request_pending = False
    
    db.commit()
    return {"status": "success", "gps_request_pending": device.gps_request_pending}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
