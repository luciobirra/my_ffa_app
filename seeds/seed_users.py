from app import app
from models import db, User
from data.users import USERS, ADMIN_USER

inserted_users = 0
inserted_admin = False

# python3 -m seeds.seed_users 


with app.app_context():

    # -------------------------
    # Utenti normali
    # -------------------------
    for username, email, pwd in USERS:
        if not User.query.filter_by(email=email).first():
            u = User(username=username, email=email,avatar=None)
            u.set_password(pwd)
            db.session.add(u)
            inserted_users += 1

    # -------------------------
    # Admin user (automatico)
    # -------------------------
    admin = User.query.filter_by(email=ADMIN_USER["email"]).first()
    if not admin:
        admin = User(
            username=ADMIN_USER["username"],
            email=ADMIN_USER["email"],
            role="admin",
            avatar=None
        )
        admin.set_password(ADMIN_USER["password"])
        db.session.add(admin)
        inserted_admin = True

    db.session.commit()

    # -------------------------
    # Output
    # -------------------------
    print("\n👤 SEED USERS")
    print(f"Utenti inseriti: {inserted_users}")
    print(f"Admin creato   : {'sì' if inserted_admin else 'no'}\n")

    users = User.query.order_by(User.role.desc(), User.username).all()

    print("📋 UTENTI NEL DB:")
    for u in users:
        role = u.role if u.role else "user"
        print(f" - [{u.id}] {u.username} <{u.email}> ({role})")

    print(f"\nTotale utenti: {len(users)}")


