from flask import Flask, render_template, request, redirect, session
from joblib import load
import numpy as np
import requests
import sqlite3
import traceback

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("farmers.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- LOAD CROP MODEL ----------------
try:
    model = load("model.pkl")
    le = load("label_encoder.pkl")
except:
    model, le = None, None

API_KEY = "f9b3ac6cbb182640a1c42cde4c7c8953"

fertilizer_tips = {
    "rice": "Use Urea, DAP and MOP for better yield.",
    "wheat": "Use NPK 10:26:26 and Urea fertilizers.",
    "maize": "Apply Nitrogen, Phosphorus and Potassium mix.",
    "cotton": "Use DAP and Urea with proper irrigation.",
    "sugarcane": "Use NPK 18:18:18 and compost manure.",
    "barley": "Use balanced NPK fertilizer with zinc supplement."
}

@app.route("/")
def home():
    return render_template("index.html")

# ---------------------- ABOUT US ----------------------
@app.route("/about")
def about():
    return render_template("about.html")

# ---------------------- REGISTER ----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = sqlite3.connect("farmers.db")
            cur = conn.cursor()
            cur.execute("INSERT INTO farmers (name, email, password) VALUES (?,?,?)",
                        (name, email, password))
            conn.commit()
            conn.close()
            return render_template("register.html", success="Successfully Registered! Please Login.")
        except:
            return render_template("register.html", error="Email already exists!")

    return render_template("register.html")

# ---------------------- LOGIN ----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("farmers.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM farmers WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid Email or Password!")

    return render_template("login.html")

# ---------------------- DASHBOARD ----------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["user"])

# ---------------------- LOGOUT ----------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------------- WEATHER ----------------------
@app.route("/get_weather", methods=["POST"])
def get_weather():
    city = request.form["city"]
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url).json()

        if response.get("main"):
            temperature = response["main"]["temp"]
            humidity = response["main"]["humidity"]

            # Rainfall handling
            rainfall = 0
            if "rain" in response:
                if "1h" in response["rain"]:
                    rainfall = response["rain"]["1h"]
                elif "3h" in response["rain"]:
                    rainfall = response["rain"]["3h"]

            return render_template(
                "index.html",
                weather_text=(
                    f"🌤️ {city.title()} — Temp: {temperature}°C, "
                    f"Humidity: {humidity}%, Rainfall: {rainfall}mm"
                ),
                temperature=temperature,
                humidity=humidity,
                rainfall=rainfall
            )
        else:
            return render_template("index.html", weather_text="❌ City not found. Try again.")

    except Exception as e:
        traceback.print_exc()
        return render_template("index.html", weather_text=f"❌ Error fetching weather: {e}")

# ---------------------- PREDICTION ----------------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        N = float(request.form["N"])
        P = float(request.form["P"])
        K = float(request.form["K"])
        temperature = float(request.form["temperature"])
        humidity = float(request.form["humidity"])
        ph = float(request.form["ph"])
        rainfall = float(request.form["rainfall"])

        features = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        pred = model.predict(features)[0]
        crop = le.inverse_transform([pred])[0]

        fertilizer = fertilizer_tips.get(crop.lower(), "Use balanced NPK fertilizer.")

        return render_template("index.html",
                               prediction_text=f"Recommended Crop: {crop}",
                               fertilizer_text=f"Fertilizer: {fertilizer}")
    except Exception as e:
        return render_template("index.html", prediction_text=f"Error: {e}")

if __name__ == "__main__":
    app.run(debug=True, port=8080)
