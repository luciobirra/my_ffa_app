from app import app
from models import db, Message

with app.app_context():
    deleted = Message.query.delete()
    db.session.commit()
    print(f"🧹 Cancellati {deleted} messaggi dalla bacheca")