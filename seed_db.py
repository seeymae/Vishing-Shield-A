from app.database import engine, Base, SessionLocal
from app.models import ConsentRecord, Employee

def seed_database():
    print("Veritabanı tabloları oluşturuluyor...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Önce örnek bir çalışan ekleyelim
        admin_employee = Employee(
            full_name="Sistem Admin",
            department="IT",
            contact_reference="admin_01"
        )
        db.add(admin_employee)
        db.commit() # ID'nin oluşması için commit
        
        # 2. Şimdi bu çalışana onay (consent) kaydı ekleyelim
        admin_consent = ConsentRecord(
            employee_id=admin_employee.id,
            opted_in=True,
            policy_version="1.0"
        )
        db.add(admin_consent)
        db.commit()
        
        print("Başarıyla örnek çalışan ve onay kaydı oluşturuldu.")
            
    except Exception as e:
        db.rollback()
        print(f"Hata oluştu: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()