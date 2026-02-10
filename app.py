from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, send_file
)
from models import (
    db, User, Participant, Prediction, PredictionRank,
    PredictionAward, OfficialRank, OfficialAward,
    DuetParticipant, DuetPrediction, DuetPredictionRank,
    OfficialDuetRank, AppSettings, Message,
    calculate_user_score
)
from openpyxl import Workbook
from datetime import datetime
from sqlalchemy import func
import io
import os
import re
import unicodedata
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge



UPLOAD_FOLDER = os.path.join("static", "avatars")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


import pdb ### 

app = Flask(__name__)

# =====================================================
# CONFIG
# =====================================================
app.secret_key = "supersegreto"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(basedir, "app.db")
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# max upload: 1 MB
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    flash("❌ Avatar troppo grande. Dimensione massima: 4 MB. Operazione non effettuata.", "error")
    return redirect(request.referrer or url_for("dashboard"))

# =====================================================
# CONTEXT
# =====================================================
@app.context_processor
def inject_current_user():
    user = None
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
    return dict(current_user=user)

@app.context_processor
def inject_settings():
    return dict(app_settings=AppSettings.query.first())

# =====================================================
# HOME
# =====================================================
@app.route("/")
def index():
    return render_template("index.html")

# =====================================================
# REGISTER
# =====================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Email già registrata", "error")
            return redirect(url_for("register"))

        # 1️⃣ crea utente
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()  # 👈 necessario per avere user.id

        # 2️⃣ avatar (opzionale)
        file = request.files.get("avatar")
        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[1].lower()

            avatar_name = f"user_{user.id}.{ext}"
            avatar_path = os.path.join(UPLOAD_FOLDER, avatar_name)

            file.save(avatar_path)
            user.avatar = avatar_name
            db.session.commit()

        print("------------------ INFO ------------------")
        print("il fantafallito:", user.username, "", user.email, "si è appena iscritto al FFA2026")
        print("------------------ INFO ------------------")

        flash("Registrazione completata", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# =====================================================
# LOGIN / LOGOUT
# =====================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and user.check_password(request.form["password"]):
            session["user_id"] = user.id
            print("------------------ INFO ------------------")
            print("il fantafallito:", user.username,"ha effettuato il LOGIN") ### OK
            print("------------------ INFO ------------------")
            #pdb.set_trace()
            return redirect(
                url_for("admin_dashboard" if user.role == "admin" else "dashboard")
            )
        flash("Credenziali errate", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))

# =====================================================
# avoid strange artists' names and borken links (error 404)

def normalize_image_name(name):
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")

def safe_artist_image(name):
    filename = f"{normalize_image_name(name)}.jpeg"
    path = os.path.join("static", "images", "artists", filename)
    if not os.path.exists(path):
        return "placeholder.jpeg"
    return filename

def safe_duet_image(duet_name):
    filename = f"{normalize_image_name(duet_name)}.jpeg"
    path = os.path.join("static", "images", "duets", filename)
    if not os.path.exists(path):
        return "placeholder.jpeg"
    return filename



# =====================================================
# DASHBOARD
# =====================================================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    # update profilo
    if request.method == "POST":
        user.username = request.form["username"]
        user.email = request.form["email"]
        if request.form.get("password"):
            user.set_password(request.form["password"])
        db.session.commit()
        flash("Profilo aggiornato", "success")
        return redirect(url_for("dashboard"))
    players = User.query.filter(User.role != "admin").all()

    # update messages
    last_message_time = db.session.query(
        func.max(Message.created_at)
    ).scalar()

    has_new_messages = (
        last_message_time
        and (
            not user.last_seen_messages
            or last_message_time > user.last_seen_messages
        )
    )
    return render_template(
        "dashboard.html",
        current_user=user,
        players=players,
        has_new_messages=has_new_messages
    )


# =====================================================
# MODIFY PROFILE
# =====================================================
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        # aggiorna dati base
        user.username = request.form["username"]
        user.email = request.form["email"]

        if request.form.get("password"):
            user.set_password(request.form["password"])

        # ---- AVATAR UPLOAD ----
        file = request.files.get("avatar")

        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[1].lower()

            avatar_name = f"user_{user.id}.{ext}"
            avatar_path = os.path.join(UPLOAD_FOLDER, avatar_name)

            file.save(avatar_path)
            user.avatar = avatar_name

        db.session.commit()
        flash("Profilo aggiornato con successo", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html")



# =====================================================
# PREDICTION (gara principale)
# =====================================================
@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    settings = AppSettings.query.first()
    closed = not settings.predictions_open if settings else False

    old = Prediction.query.filter_by(user_id=user.id).first()

    # -------------------------
    # POST: salva / aggiorna prediction
    # -------------------------
    if request.method == "POST" and not closed:
        if old:
            PredictionRank.query.filter_by(prediction_id=old.id).delete()
            PredictionAward.query.filter_by(prediction_id=old.id).delete()
            db.session.delete(old)
            db.session.commit()

        pred = Prediction(user_id=user.id)
        db.session.add(pred)
        db.session.commit()

        order = request.form.getlist("order[]")
        for i, pid in enumerate(order):
            db.session.add(
                PredictionRank(
                    prediction_id=pred.id,
                    participant_id=int(pid),
                    position=i + 1
                )
            )

        db.session.add(
            PredictionAward(
                prediction_id=pred.id,
                critica_id=int(request.form["critica"]),
                stampa_id=int(request.form["stampa"]),
                testo_id=int(request.form["testo"]),
                composizione_id=int(request.form["composizione"])
            )
        )

        db.session.commit()

        print("------------------ INFO ------------------")
        print("il fantafallito:", user.username, "ha aggiornato la classifica e/o i premi")
        print("------------------ INFO ------------------")

        return redirect(url_for("prediction"))

    # -------------------------
    # GET: prepara dati per il template
    # -------------------------
    if old:
        ranks = (
            PredictionRank.query
            .filter_by(prediction_id=old.id)
            .order_by(PredictionRank.position)
            .all()
        )

        participants = []
        for r in ranks:
            p = r.participant
            p.image = safe_artist_image(p.name)
            participants.append(p)

        awards = PredictionAward.query.filter_by(prediction_id=old.id).first()

    else:
        participants = Participant.query.order_by(Participant.name).all()
        for p in participants:
            p.image = safe_artist_image(p.name)

        awards = None

    return render_template(
        "prediction.html",
        participants=participants,
        awards=awards,
        closed=closed
    )

# =====================================================
# DUETS
# =====================================================
@app.route("/duets", methods=["GET", "POST"])
def duets():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if user.role == "admin":
        return redirect(url_for("admin_dashboard"))

    settings = AppSettings.query.first()
    closed = not settings.predictions_open if settings else False

    old = DuetPrediction.query.filter_by(user_id=user.id).first()

    # =====================================================
    # POST — salva previsione
    # =====================================================
    if request.method == "POST" and not closed:

        if old:
            (
                DuetPredictionRank.query
                .filter_by(duet_prediction_id=old.id)
                .delete()
            )
            db.session.delete(old)
            db.session.commit()

        pred = DuetPrediction(user_id=user.id)
        db.session.add(pred)
        db.session.commit()

        order = request.form.getlist("order[]")[:5]
        for i, did in enumerate(order):
            db.session.add(
                DuetPredictionRank(
                    duet_prediction_id=pred.id,
                    duet_participant_id=int(did),
                    position=i + 1
                )
            )

        db.session.commit()

        print("------------------ INFO ------------------")
        print("il fantafallito:", user.username, "ha aggiornato i duetti")
        print("------------------ INFO ------------------")

        return redirect(url_for("duets"))

    # =====================================================
    # GET — prepara lista duetti con immagini
    # =====================================================
    if old:
        ranks = (
            DuetPredictionRank.query
            .filter_by(duet_prediction_id=old.id)
            .order_by(DuetPredictionRank.position)
            .all()
        )

        top_ids = [r.duet_participant_id for r in ranks]

        top_duets = (
            DuetParticipant.query
            .filter(DuetParticipant.id.in_(top_ids))
            .all()
        )
        top_duets.sort(key=lambda d: top_ids.index(d.id))

        others = (
            DuetParticipant.query
            .filter(~DuetParticipant.id.in_(top_ids))
            .order_by(DuetParticipant.name)
            .all()
        )

        duets = top_duets + others

    else:
        duets = DuetParticipant.query.order_by(DuetParticipant.name).all()

    # 🔑 QUI la parte importante: immagine nel backend
    for d in duets:
        d.image = safe_duet_image(d.name)


    return render_template(
        "duets.html",
        duets=duets,
        closed=closed
    )


# =====================================================
# RANKING
# =====================================================
@app.route("/ranking")
def ranking():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])

    settings = AppSettings.query.first()
    closed = not settings.predictions_open if settings else False

    # ❌ blocco SOLO per utenti normali quando le previsioni sono APERTE
    if user.role != "admin" and not closed:
        flash(
            "Calma: hai letto qui sopra? Ti devi fare i fatti tuoi. "
            "Gioca sereno e non pensare ai fallimenti degli altri. "
            "Quando arriverà il tempo, allora il DA ti consentirà di vedere "
            "le giocate degli altri falliti.",
            "warning"
        )
        return redirect(url_for("dashboard"))

    ranking = []
    for u in User.query.all():
        if u.role == "admin":
            continue
        result = calculate_user_score(u.id)
        ranking.append({"user": u, "total": result["total"]})

    ranking.sort(key=lambda x: x["total"], reverse=True)
    return render_template("ranking.html", ranking=ranking)


# =====================================================
# SCORE DETAIL
# =====================================================
@app.route("/score/<int:user_id>")
def score_detail(user_id):
    user = User.query.get_or_404(user_id)
    result = calculate_user_score(user_id)
    #print("DEBUG SCORE:", result)   # 👈 AGGIUNGI QUESTO
    
    return render_template("score_detail.html", user=user, breakdown=result["breakdown"], total=result["total"])

# =====================================================
# ADMIN
# =====================================================
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if user.role != "admin":
        return redirect(url_for("dashboard"))

    return render_template("admin_dashboard.html", users=User.query.all())

@app.route("/admin/results", methods=["GET", "POST"])
def admin_results():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if user.role != "admin":
        return redirect(url_for("dashboard"))

    # =====================
    # SETTINGS
    # =====================
    settings = AppSettings.query.first()
    if not settings:
        settings = AppSettings(predictions_open=True)
        db.session.add(settings)
        db.session.commit()

    # =====================================================
    # POST — PUBBLICA RISULTATI (RESET + RISCRITTURA)
    # =====================================================
    if request.method == "POST":

        # ----- RESET TOTALE -----
        OfficialRank.query.delete()
        OfficialDuetRank.query.delete()

        old_award = OfficialAward.query.first()
        if old_award:
            db.session.delete(old_award)

        db.session.commit()

        # ----- CLASSIFICA PRINCIPALE -----
        main_order = request.form.getlist("main_order[]")

        for i, pid in enumerate(main_order):
            db.session.add(
                OfficialRank(
                    participant_id=int(pid),
                    position=i + 1
                )
            )

        # ----- PREMI -----
        award = OfficialAward(
            critica_id=int(request.form["critica"]),
            stampa_id=int(request.form["stampa"]),
            testo_id=int(request.form["testo"]),
            composizione_id=int(request.form["composizione"])
        )
        db.session.add(award)

        # ----- DUETTI (TOP 5) -----
        duet_order = request.form.getlist("duet_order[]")[:5]

        for i, did in enumerate(duet_order):
            db.session.add(
                OfficialDuetRank(
                    duet_participant_id=int(did),
                    position=i + 1
                )
            )

        db.session.commit()
        flash("Risultati ufficiali pubblicati", "success")
        return redirect(url_for("admin_results"))

    # =====================================================
    # GET — CARICAMENTO ORDINATO (POST-PUBBLICAZIONE)
    # =====================================================

    # ----- CANTANTI -----
    official_ranks = OfficialRank.query.order_by(OfficialRank.position).all()

    if official_ranks:
        ordered_ids = [r.participant_id for r in official_ranks]

        ranked = Participant.query.filter(
            Participant.id.in_(ordered_ids)
        ).all()
        ranked.sort(key=lambda p: ordered_ids.index(p.id))

        others = Participant.query.filter(
            ~Participant.id.in_(ordered_ids)
        ).order_by(Participant.name).all()

        participants = ranked + others
    else:
        participants = Participant.query.order_by(Participant.name).all()

    # ----- DUETTI -----
    official_duets = OfficialDuetRank.query.order_by(OfficialDuetRank.position).all()

    if official_duets:
        ordered_ids = [r.duet_participant_id for r in official_duets]

        ranked = DuetParticipant.query.filter(
            DuetParticipant.id.in_(ordered_ids)
        ).all()
        ranked.sort(key=lambda d: ordered_ids.index(d.id))

        others = DuetParticipant.query.filter(
            ~DuetParticipant.id.in_(ordered_ids)
        ).order_by(DuetParticipant.name).all()

        duets = ranked + others
    else:
        duets = DuetParticipant.query.order_by(DuetParticipant.name).all()

    award = OfficialAward.query.first()

    return render_template(
        "admin_results.html",
        participants=participants,
        duets=duets,
        award=award,
        settings=settings
    )

@app.route("/admin/toggle_predictions")
def toggle_predictions():
    settings = AppSettings.query.first()
    if not settings:
        settings = AppSettings(predictions_open=True)
        db.session.add(settings)

    settings.predictions_open = not settings.predictions_open
    db.session.commit()
    return redirect(url_for("admin_results"))

@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
def admin_edit_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    admin = db.session.get(User, session["user_id"])
    if admin.role != "admin":
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.username = request.form["username"]
        user.email = request.form["email"]
        user.role = request.form["role"]
        db.session.commit()
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_edit_user.html", user=user)


@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    admin = db.session.get(User, session["user_id"])
    if admin.role != "admin":
        return redirect(url_for("dashboard"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("admin_dashboard"))

# =====================================================
# ADMIN EXPORT
# =====================================================
@app.route("/admin/export")
def admin_export():
    if "user_id" not in session:
        return redirect(url_for("login"))

    admin = db.session.get(User, session["user_id"])
    if admin.role != "admin":
        return redirect(url_for("dashboard"))

    wb = Workbook()
    ws = wb.active
    ws.append(["Pos", "Username", "Email", "Score"])

    rows = []
    for u in User.query.all():
        result = calculate_user_score(u.id)
        rows.append((u, result["total"]))

    rows.sort(key=lambda x: x[1], reverse=True)

    for i, (u, score) in enumerate(rows, start=1):
        ws.append([i, u.username, u.email, score])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="classifica.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )





# =====================================================
# MESSAGES
# =====================================================
@app.route("/dashboard/messages", methods=["GET", "POST"])
def messages():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    user.last_seen_messages = datetime.utcnow()
    db.session.commit()

    if request.method == "POST":
        content = request.form["content"].strip()
        if content:
            msg = Message(
                content=content,
                user_id=user.id
            )
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for("messages"))

    messages = Message.query.order_by(Message.created_at.desc()).all()

    return render_template(
        "messages.html",
        messages=messages,
        current_user=user
    )


# =====================================================
# MESSAGES - Admin
# =====================================================
@app.route("/dashboard/messages/delete/<int:message_id>", methods=["POST"])
def delete_message(message_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = db.session.get(User, session["user_id"])
    if user.role != "admin":
        return "Non autorizzato", 403

    msg = Message.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()

    return redirect(url_for("messages"))


# =====================================================
# AVVIO
# =====================================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
