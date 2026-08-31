from app.db.session import SessionLocal
from app.tasks.verifiers import verify_billing_escalation

db = SessionLocal()

try:
    result = verify_billing_escalation(db)
    print("Verification result:", result)
finally:
    db.close()