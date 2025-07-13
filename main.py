from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd

app = FastAPI()

# إعداد قاعدة البيانات SQLite
DATABASE_URL = "sqlite:///./attendance.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee = Column(String, index=True)
    member_name = Column(String)
    barcode = Column(String)
    time = Column(DateTime)
    status = Column(String)
    game_type = Column(String)
    game_date = Column(String)

Base.metadata.create_all(bind=engine)

class AttendanceRequest(BaseModel):
    employee: str
    barcode: str

class AttendanceRecord(BaseModel):
    employee: str
    member_name: str
    barcode: str
    time: str
    status: str
    game_type: str
    game_date: str

@app.post("/register", response_model=AttendanceRecord)
def register_attendance(req: AttendanceRequest):
    db = SessionLocal()
    member_name = "عضو افتراضي"
    is_reserved = hash(req.barcode) % 2 == 0
    game_type = "كرة قدم" if is_reserved else "-"
    game_date = datetime.now().strftime("%Y-%m-%d") if is_reserved else "-"
    now = datetime.now()

    record = Attendance(
        employee=req.employee,
        member_name=member_name,
        barcode=req.barcode,
        time=now,
        status="حاجز" if is_reserved else "غير حاجز",
        game_type=game_type,
        game_date=game_date
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return AttendanceRecord(
        employee=record.employee,
        member_name=record.member_name,
        barcode=record.barcode,
        time=record.time.strftime("%Y-%m-%d %H:%M:%S"),
        status=record.status,
        game_type=record.game_type,
        game_date=record.game_date
    )

@app.get("/records", response_model=List[AttendanceRecord])
def get_records():
    db = SessionLocal()
    records = db.query(Attendance).order_by(Attendance.time.desc()).all()
    return [
        AttendanceRecord(
            employee=r.employee,
            member_name=r.member_name,
            barcode=r.barcode,
            time=r.time.strftime("%Y-%m-%d %H:%M:%S"),
            status=r.status,
            game_type=r.game_type,
            game_date=r.game_date
        ) for r in records
    ]

@app.get("/export")
def export_excel():
    db = SessionLocal()
    records = db.query(Attendance).all()
    df = pd.DataFrame([
        {
            "الموظف": r.employee,
            "العضو": r.member_name,
            "الباركود": r.barcode,
            "الوقت": r.time.strftime("%Y-%m-%d %H:%M:%S"),
            "الحالة": r.status,
            "نوع اللعبة": r.game_type,
            "تاريخ المباراة": r.game_date
        } for r in records
    ])
    file_path = "attendance_export.xlsx"
    df.to_excel(file_path, index=False)
    return {"message": "تم تصدير التقرير بنجاح", "file": file_path}
