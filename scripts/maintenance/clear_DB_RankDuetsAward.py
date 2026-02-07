from app import app
from models import db, OfficialRank, OfficialDuetRank, OfficialAward


with app.app_context():

    deleted_ranks = OfficialRank.query.delete()
    print(f"🗑️ OfficialRank cancellati: {deleted_ranks}")

    deleted_duets = OfficialDuetRank.query.delete()
    print(f"🗑️ OfficialDuetRank cancellati: {deleted_duets}")

    deleted_awards = OfficialAward.query.delete()
    print(f"🗑️ OfficialAward cancellati: {deleted_awards}")

    db.session.commit()

    print("\n✅ DB ufficiale pulito")


