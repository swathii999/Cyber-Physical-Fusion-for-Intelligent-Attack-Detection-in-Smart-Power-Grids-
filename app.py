
from flask import Flask, render_template, request, redirect, flash, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)
app.secret_key = 'admin_secret_key_please_change_this'

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'port': 3306,
    'database': 'db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def retrieve_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def execute_query(query, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params or ())
    conn.commit()
    cursor.close()
    conn.close()

# ------------------ Routes ------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/index2')
def index2():
    return render_template('index2.html')

@app.route('/about')
def about():
    return render_template('about.html')

# ------------------ Registration ------------------
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email'].strip()
        password = request.form['password']
        c_password = request.form['conformpassword']

        if password != c_password:
            return render_template('register.html', message="Confirm password does not match!")

        query = "SELECT email FROM user3 WHERE UPPER(email) = %s"
        email_upper = email.upper()
        email_data = retrieve_query(query, (email_upper,))

        if not email_data:
            hashed_password = generate_password_hash(password)
            query = "INSERT INTO user3 (name, email, password) VALUES (%s, %s, %s)"
            try:
                execute_query(query, (name, email, hashed_password))
            except Exception as e:
                print(f"DB Insert Error: {e}")
                return render_template('register.html', message="Registration failed due to database error.")
            
            flash("Registration successful!", "success")
            return render_template('login.html', message="Successfully Registered!")
        else:
            return render_template('register.html', message="This email ID already exists!")

    return render_template('register.html')

# ------------------ Login ------------------
@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        query = "SELECT id, password FROM user3 WHERE email = %s"
        result = retrieve_query(query, (email,))
        if result:
            user_id, hashed_password = result[0]
            if check_password_hash(hashed_password, password):
                flash("Login successful!", "success")
                return redirect(url_for('home'))
            else:
                flash("Incorrect password!", "danger")
        else:
            flash("Email not registered!", "danger")
    return render_template('login.html')

# ------------------ Logout ------------------
@app.route('/logout')
def logout():
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ------------------ Home Page ------------------
@app.route('/home')
def home():
    return render_template('home.html')

# ------------------ Upload CSV ------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('upload.html', msg="No file part")
        
        file = request.files['file']
        if file.filename == '':
            return render_template('upload.html', msg="No selected file")
        
        try:
            df = pd.read_csv(file)
            dataset = df.head(500)
            columns = dataset.columns.values
            rows = dataset.values.tolist()
            return render_template('upload.html', columns=columns, rows=rows, msg="✅ Dataset Uploaded Successfully")
        except Exception as e:
            return render_template('upload.html', msg=f"Error: {str(e)}")

    return render_template('upload.html')
# ------------------ Model Selection ------------------
@app.route('/model', methods=['POST', 'GET'])
def model():
    model_scores = {
        'random_forest': 0.9422797676669894,
        'lightgbm': 0.9476040658276863,
        'mlp': 0.688891577928364,
        'gnn': 0.816,
        'catboost': 0.9461519845111326
      
    }

    model_names = {
        'random_forest': 'Random Forest',
        'lightgbm': 'LightGBM',
        'mlp': 'MLP (Multi-Layer Perceptron)',
        'gnn': 'GNN (Graph Neural Network)',
        'catboost': 'CatBoost',
    }

    msg = ""
    msg1 = ""

    if request.method == "POST":
        selected_model = request.form['model']
        if selected_model in model_scores:
            accuracy = model_scores[selected_model]
            msg = f"The accuracy obtained by the {model_names[selected_model]} Classifier is: {accuracy:.4f}"
            msg1 = f"{model_names[selected_model]} Accuracy: {accuracy * 100:.2f}%"
        else:
            msg = "Invalid Model Selection"
            msg1 = ""

    return render_template('model.html', msg=msg, msg1=msg1)


# ------------------ Prediction ------------------
from sklearn.preprocessing import LabelEncoder
import numpy as np
import joblib

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == 'POST':
        try:
            # Helper functions
            def get_str(key): return request.form.get(key, '').strip()
            def get_num(key):
                try:
                    return float(request.form.get(key, 0))
                except:
                    return 0.0

            # --- Get Inputs from Form ---
            year = get_num("year")
            actor = get_str("actor")
            industry_code = get_str("industry_code")
            motive = get_str("motive")
            event_subtype = get_str("event_subtype")
            description = get_str("description")
            country = get_str("country")
            actor_country = get_str("actor_country")

            # --- Load LabelEncoders for all text fields ---
            encoders = {}
            text_fields = ['actor', 'industry_code', 'motive', 'event_subtype',
                           'description', 'country', 'actor_country']
            for field in text_fields:
                encoders[field] = joblib.load("description_encoder.joblib")  # you need to save these during training

            # --- Encode text fields safely ---
            def safe_encode(value, le):
                if value in le.classes_:
                    return le.transform([value])[0]
                else:
                    return -1  # default for unseen values

            encoded_features = [
                year,
                safe_encode(actor, encoders['actor']),
                safe_encode(industry_code, encoders['industry_code']),
                safe_encode(motive, encoders['motive']),
                safe_encode(event_subtype, encoders['event_subtype']),
                safe_encode(description, encoders['description']),
                safe_encode(country, encoders['country']),
                safe_encode(actor_country, encoders['actor_country'])
            ]

            input_array = np.array(encoded_features).reshape(1, -1)

            # --- Load Model & Predict ---
            model = joblib.load("lG.joblib")
            prediction_val = model.predict(input_array)
            pred = prediction_val[0]

            # --- Labels & Suggestions ---
            labels = {
                0: "Normal",
                1: "Frequent Attack",
                2: "Medium Severity Attack",
                3: "Critical Attack"
            }

            suggestions = {
                0: "✅ Normal or benign event detected. Continue routine monitoring.",
                1: "🔐 Frequent attack pattern (e.g., breaches, ransomware). Investigate logs and apply mitigations.",
                2: "⚠️ Medium severity cyber-physical attack. Check data integrity and system inputs.",
                3: "🚨 Critical attack detected (e.g., DoS, backdoor). Isolate affected systems immediately."
            }

            label_text = labels.get(pred, "Unknown")
            suggestion_text = suggestions.get(pred, "❓ Unknown event type. Please verify input or retrain the model.")

            # --- Render Result ---
            result_msg = f"""<p><strong>Prediction:</strong> {label_text}</p>
                             <p><strong>Action:</strong> {suggestion_text}</p>"""

            return render_template("prediction.html", prediction=result_msg)

        except Exception as e:
            print("❌ Prediction error:", e)
            return render_template("prediction.html", prediction="❌ Invalid input or model error.")

    return render_template("prediction.html")



if __name__=="__main__":
    app.run(debug=True)
