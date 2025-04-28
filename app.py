from flask import Flask, render_template, request, redirect, session, url_for
import random
import time

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Admin und Test-Accounts
ADMIN_EMAIL = "admin@worldjackpot.com"
TEST_USERS = [f"test{i}@worldjackpot.com" for i in range(1, 11)]

# Globale State-Variablen
simulierter_jackpot_text = "10 Millionen Jackpot"
scheine = []
alte_scheine = []
ziehung = None
freigabe_klasse1 = False
zeige_sim_jackpot = True
fake_gewinner = []
naechste_ziehung_ts = time.time() + 7*24*3600

def klassifizieren(r, w):
    mapping = {
        (5, 2): 1, (5, 1): 2, (5, 0): 3,
        (4, 2): 4, (4, 1): 5, (4, 0): 6,
        (3, 2): 7, (2, 2): 8, (3, 1): 9,
        (3, 0):10, (1, 2):11, (2, 1):12
    }
    return mapping.get((r, w))

def ziehung_durchfuehren():
    counts_main = {i:0 for i in range(1,51)}
    counts_world = {i:0 for i in range(1,11)}
    for s in scheine:
        for z in s["zahlen"]: counts_main[z]+=1
        for w in s["world"]: counts_world[w]+=1
    selten_main = sorted(range(1,51), key=lambda x: counts_main[x])
    selten_world = sorted(range(1,11), key=lambda x: counts_world[x])
    return {
        "zahlen": sorted(selten_main[:5]),
        "world": sorted(selten_world[:2])
    }

@app.route("/", methods=["GET","POST"])
def index():
    global ziehung, naechste_ziehung_ts, simulierter_jackpot_text, freigabe_klasse1, zeige_sim_jackpot

    if "email" not in session:
        return redirect(url_for("login"))
    email = session["email"]
    is_admin = session.get("admin", False)

    user_new = [s for s in scheine if s["email"] == email]
    user_old = [s for s in alte_scheine if s["email"] == email]
    message = ""

    now = time.time()
    if request.method=="POST":
        if is_admin:
            if "bearbeiten_jackpot_text" in request.form:
                t = request.form.get("jackpot_text","").strip()
                if t: simulierter_jackpot_text = t
            if "ziehen" in request.form and now>=naechste_ziehung_ts:
                alte_scheine.extend(scheine)
                scheine.clear()
                ziehung = ziehung_durchfuehren()
                naechste_ziehung_ts = now + 7*24*3600
            if "freigeben" in request.form:
                freigabe_klasse1 = not freigabe_klasse1
            if "toggle_sim" in request.form:
                zeige_sim_jackpot = not zeige_sim_jackpot
        else:
            zs = list(map(int, request.form.getlist("zahlen")))
            ws = list(map(int, request.form.getlist("worldzahlen")))
            if len(zs)==5 and len(ws)==2:
                scheine.append({"email":email,"zahlen":sorted(zs),"world":sorted(ws)})
            else:
                message="Ungültige Anzahl Zahlen!"

    countdown = max(0, int(naechste_ziehung_ts - now))

    return render_template("index.html",
        is_admin=is_admin,
        email=email,
        logo_text=simulierter_jackpot_text,
        ziehung=ziehung,
        countdown=countdown,
        scheine_new=user_new,
        scheine_old=user_old,
        freigabe=freigabe_klasse1,
        zeige_sim=zeige_sim_jackpot,
        fake_gewinner=fake_gewinner,
        message=message
    )

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        e = request.form["email"].strip()
        if e==ADMIN_EMAIL or e in TEST_USERS:
            session["email"], session["admin"] = e, (e==ADMIN_EMAIL)
            return redirect(url_for("index"))
        return "Zugang verweigert",403
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)
