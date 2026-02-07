import os
import re
import unicodedata
from data.artists import ARTISTS
from data.duets import DUETS

# =========================
# CONFIG
# =========================
ARTISTS_DIR = "static/images/artists"
DUETS_DIR = "static/images/duets"


# =========================
# NORMALIZZAZIONE (identica al backend)
# =========================
def image_filename(name):
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = name.strip("_")
    return f"{name}.jpeg"


# =========================
# CHECK ARTISTI
# =========================
def check_artists():
    print("\n🎤 ARTISTI")
    missing = []

    for artist in ARTISTS:
        filename = image_filename(artist)
        path = os.path.join(ARTISTS_DIR, filename)

        if not os.path.exists(path):
            print(f"❌ MANCA: {filename}  ({artist})")
            missing.append(filename)
        else:
            print(f"✅ OK   : {filename}")

    return missing


# =========================
# CHECK DUETTI
# =========================
def check_duets():
    print("\n🎶 DUETTI")
    missing = []

    for duet in DUETS:
        filename = image_filename(duet)
        path = os.path.join(DUETS_DIR, filename)

        if not os.path.exists(path):
            print(f"❌ MANCA: {filename}  ({duet})")
            missing.append(filename)
        else:
            print(f"✅ OK   : {filename}")

    return missing


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    print("\n🔍 CONTROLLO IMMAGINI\n")

    missing_artists = check_artists()
    missing_duets = check_duets()

    print("\n=========================")
    print("📊 RIEPILOGO")
    print("=========================")
    print(f"Artisti mancanti: {len(missing_artists)}")
    print(f"Duetti mancanti : {len(missing_duets)}")

    if not missing_artists and not missing_duets:
        print("\n🎉 Tutte le immagini sono presenti!")
    else:
        print("\n⚠️  Alcune immagini mancano.")
