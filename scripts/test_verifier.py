from app.db.session import SessionLocal
from app.tasks.verifiers import verify_billing_escalation


CUSTOMER_ID = 31


db = SessionLocal()

try:
    result = verify_billing_escalation(
        db,
        customer_id=CUSTOMER_ID,
    )

    print(result)

finally:
    db.close()