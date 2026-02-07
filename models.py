from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# =====================
# USER
# =====================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="user")
    avatar = db.Column(db.String(120), nullable=True)  # 👈 NUOVO CAMPO
    last_seen_messages = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# =====================
# SETTINGS
# =====================
class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    predictions_open = db.Column(db.Boolean, default=True)


# =====================
# GARA PRINCIPALE
# =====================
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        return self.name


class Prediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    user = db.relationship("User", backref="prediction", uselist=False)


class PredictionRank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("prediction.id"))
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    position = db.Column(db.Integer)
    participant = db.relationship("Participant")


class PredictionAward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prediction_id = db.Column(db.Integer, db.ForeignKey("prediction.id"))

    critica_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    stampa_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    testo_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    composizione_id = db.Column(db.Integer, db.ForeignKey("participant.id"))

class OfficialRank(db.Model):
    __table_args__ = (
        db.UniqueConstraint("position", name="uq_official_rank_position"),
    )

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    position = db.Column(db.Integer, nullable=False)



class OfficialAward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    critica_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    stampa_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    testo_id = db.Column(db.Integer, db.ForeignKey("participant.id"))
    composizione_id = db.Column(db.Integer, db.ForeignKey("participant.id"))


# =====================
# DUETTI
# =====================
class DuetParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class DuetPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)


class DuetPredictionRank(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    duet_prediction_id = db.Column(db.Integer, db.ForeignKey("duet_prediction.id"))
    duet_participant_id = db.Column(db.Integer, db.ForeignKey("duet_participant.id"))
    position = db.Column(db.Integer)


class OfficialDuetRank(db.Model):
    __table_args__ = (
        db.UniqueConstraint("position", name="uq_official_duet_position"),
    )

    id = db.Column(db.Integer, primary_key=True)
    duet_participant_id = db.Column(db.Integer, db.ForeignKey("duet_participant.id"))
    position = db.Column(db.Integer, nullable=False)



# =====================
# SCORE (legacy, non usato)
# =====================
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True)
    total = db.Column(db.Float)
    user = db.relationship("User")


# =====================================================
# ✅ SINGLE SOURCE OF TRUTH
# =====================================================
def calculate_user_score(user_id):
    """
    Calcola il punteggio utente.
    UNICA FONTE DI VERITÀ per ranking, score, export.
    """

    # ===== DATI UFFICIALI =====
    official = {r.participant_id: r.position for r in OfficialRank.query.all()}
    official_top5 = {pid for pid, pos in official.items() if pos <= 5}
    official_bottom5 = {pid for pid, pos in official.items() if pos > 25}

    # ===== PREVISIONE UTENTE =====
    pred = Prediction.query.filter_by(user_id=user_id).first()
    if not pred:
        return {"total": 0, "breakdown": {}}

    ranks = PredictionRank.query.filter_by(prediction_id=pred.id).all()
    user_map = {r.participant_id: r.position for r in ranks}

    table = {1: 40, 2: 30, 3: 25, 4: 16, 5: 8}

    # ===== CLASSIFICA (DETTAGLIATA) =====
    total_classifica = 0
    classifica_details = []

    for pid, pos in user_map.items():
        points = 0
        if pid in official and official[pid] == pos:
            points = table.get(pos, 2.5)

        total_classifica += points
        participant = Participant.query.get(pid)

        classifica_details.append({
            "name": participant.name if participant else "—",
            "predicted": pos,
            "official": official.get(pid),
            "points": points
        })

    # ===== BONUS / MALUS =====
    user_top5 = {pid for pid, pos in user_map.items() if pos <= 5}
    bonus = 25 if len(user_top5 & official_top5) >= 3 else 0

    user_bottom5 = {pid for pid, pos in user_map.items() if pos > 25}
    malus = -20 if len(user_bottom5 & official_bottom5) < 3 else 0

    # ===== PREMI (DETTAGLIATI) =====
    premi_total = 0
    premi_details = []

    pred_award = PredictionAward.query.filter_by(prediction_id=pred.id).first()
    awards = OfficialAward.query.first()

    if pred_award and awards:
        premi_map = [
            ("Critica", "critica_id"),
            ("Sala Stampa", "stampa_id"),
            ("Testo", "testo_id"),
            ("Composizione", "composizione_id")
        ]

        for label, field in premi_map:
            user_pick = getattr(pred_award, field)
            official_pick = getattr(awards, field)

            user_name = Participant.query.get(user_pick).name if user_pick else "—"
            official_name = Participant.query.get(official_pick).name if official_pick else "—"

            points = 14 if user_pick == official_pick else 0
            premi_total += points

            premi_details.append({
                "label": label,
                "user": user_name,
                "official": official_name,
                "points": points
            })

    # ===== DUETTI (DETTAGLIATI) =====
    duetti_total = 0
    duetti_details = []

    duet_pred = DuetPrediction.query.filter_by(user_id=user_id).first()
    official_duets = (
        OfficialDuetRank.query
        .order_by(OfficialDuetRank.position, OfficialDuetRank.id)
        .limit(5)
        .all()
    )

    # posizione CALCOLATA, non fidata dal DB
    duet_off_map = {
        r.duet_participant_id: idx + 1
        for idx, r in enumerate(official_duets)
    }


    duet_off_map = {
        r.duet_participant_id: r.position
        for r in official_duets
    }

    if duet_pred:
        ranks = DuetPredictionRank.query.filter_by(
            duet_prediction_id=duet_pred.id
        ).all()

        for r in ranks:
            name = DuetParticipant.query.get(r.duet_participant_id).name
            official_pos = duet_off_map.get(r.duet_participant_id)

            if official_pos is None:
                official_label = "non top 5"
                points = 0
            else:
                official_label = official_pos
                points = [25, 20, 16, 11, 8][r.position - 1] if r.position == official_pos else 0

            duetti_total += points

            duetti_details.append({
                "name": name,
                "predicted": r.position,
                "official": official_label,
                "points": points
            })

    # ===== TOTALE =====
    total = total_classifica + bonus + malus + premi_total + duetti_total

    return {
        "total": round(total, 2),
        "breakdown": {
            "classifica": {
                "total": total_classifica,
                "details": classifica_details
            },
            "bonus": bonus,
            "malus": malus,
            "premi": {
                "total": premi_total,
                "details": premi_details
            },
            "duetti": {
                "total": duetti_total,
                "details": duetti_details
            }
        }
    }


  # ===== BACHECA =====
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # opzionale ma utile
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    user = db.relationship("User")