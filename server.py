from flask import Flask
from flask import render_template,session, request, redirect, url_for, flash 
import sklearn
import sqlite3
import joblib
import pickle
import random
import smtplib 
from datetime import datetime
from email.message import EmailMessage
import sqlite3
from flask_mail import Message
from flask_mail import Mail

app = Flask(__name__)
app.secret_key = '1234'
def connect_db():
    conn = sqlite3.connect('database.db')
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        );
    ''')
    conn.commit()
    conn.close()


create_table()

app.static_folder = 'static'
model = joblib.load('notebook/crop_recommendation_model.joblib')
model1 = joblib.load('notebook/fertlizer_recommendation_model.joblib')
model2 = joblib.load('notebook/crop_2_recommendation_model.joblib')

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'frmspprt123@gmail.com'
app.config['MAIL_PASSWORD'] = 'sysu rgne emzz alcf'
app.config['MAIL_DEFAULT_SENDER'] = 'frmspprt123@gmail.com'
mail = Mail(app)

def generate():
    return random.randint(5000,9999)
def generate_otp():
    return random.randint(1000, 9999)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/preregister')
def preregister():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        session['email'] = email
        password = request.form['password']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', alert_message="Invalid username or password.")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            conn.close()
            return render_template('register.html', alert_message="Email already exists. Please choose a different one or login.")
        
        session['username'] = username
        session['password'] = password
        session['email'] = email

        otp = generate_otp() 
        msg = Message(subject='OTP', sender='frmspprt123@gmail.com', recipients=[email])
        msg.body = str(otp)
        mail.send(msg)
        session['otp'] = otp

        conn.close()
        return redirect(url_for('registration'))
    return render_template('register.html')

@app.route('/registration')
def registration():
    return render_template('registration.html')

@app.route('/verify2', methods=['POST'])
def verify2():
    user_otp = request.form['otp']
    if 'otp' in session and int(session['otp']) == int(user_otp):
        conn = connect_db()
        cursor = conn.cursor()
        username = session.pop('username')
        password = session.pop('password')
        email = session.pop('email')
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, password))
        conn.commit()
        conn.close()
        return render_template('login.html')
    else:
        return render_template('registration.html', alert_message="Please try again")


@app.route('/dashboard')
def dashboard():
    return render_template('main.html')

@app.route('/forgot')
def forgot():
    return render_template('forgot.html')

@app.route('/verify',methods=["POST"])
def verify():
    email=request.form['email']
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    existing_user = cursor.fetchone()
    otp = generate() 
    if existing_user:
        conn.close()
        msg=Message(subject='OTP',sender='frmspprt123@gmail.com',recipients=[email])
        msg.body=str(otp)
        mail.send(msg)
        session['otp'] = otp
        return render_template('otp.html')
        

@app.route('/validate',methods=['POST'])
def validate():
    user_otp=request.form['otp']
    if 'otp' in session and int(session['otp']) == int(user_otp):
        return render_template('reset.html')
    return "<h3>Please Try Again</h3>"

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        email = session.get('email')
        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.')
            return redirect(url_for('reset_password'))
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
        conn.commit()
        conn.close()

        flash('Password reset successfully. You can now login with your new password.')
        return redirect(url_for('login'))

    return render_template('reset.html')

@app.route('/north')
def north():
    return render_template('northsouth.html')

@app.route('/crop')
def crop():
    return render_template('index.html')

@app.route('/crop2')
def crop2():
    return render_template('crop2.html')

@app.route('/fertlizer')
def fertilizer():
    return render_template('index1.html')

@app.route('/detail')
def detail():
    return render_template('details.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        N = float(request.form['N'])
        P = float(request.form['P'])
        K = float(request.form['K'])
        temperature = float(request.form['temperature'])
        humidity = float(request.form['humidity'])
        rainfall = float(request.form['rainfall'])
        ph = float(request.form['ph'])
        email = session.get('email')
        input_data = [[N, P, K, temperature, humidity, ph, rainfall]]
        predict1 = model.predict(input_data)[0]

        try:
            html_content = render_template('mail.html',N=N, P=P, K=K, temperature=temperature, humidity=humidity, rainfall=rainfall, ph=ph, predict1=predict1)
            msg = Message(subject='Crop Recommendation Result',
                  recipients=[email],
                  html=html_content)
            mail.send(msg)
        except Exception as e:
            print(e)

        return render_template('result.html', prediction=predict1)

    else:
        return render_template("index.html")

@app.route('/Crop1_predict', methods=['GET','POST'])
def Crop1_predict():
    if request.method == 'POST':
        N = float(request.form['N'])
        P = float(request.form['P'])
        K = float(request.form['K'])
        temperature = float(request.form['temperature'])
        humidity = float(request.form['humidity'])
        rainfall = float(request.form['rainfall'])
        ph = float(request.form['ph'])
        email = session.get('email')
        input_data = [[N, P, K, temperature, humidity, ph, rainfall]]
        predict2 = model2.predict(input_data)[0]
        try:
            html_content = render_template('mail.html',N=N, P=P, K=K, temperature=temperature, humidity=humidity, rainfall=rainfall, ph=ph, predict1=predict2)
            msg = Message(subject='Crop Recommendation Result',
                  recipients=[email],
                  html=html_content)
            mail.send(msg)
        except Exception as e:
            print(e)

        return render_template('result.html', prediction=predict2)

    else:
        return render_template("crop2.html")

@app.route('/fertilizer_predict', methods=['POST'])
def fertilizer_predict():
    crop_dict = {'Cotton': 1, 'Rice': 2, 'Groundnut': 3, 'Maize': 4, 'Soyabean': 5, 'Grapes': 6, 'chickpea': 7,
                 'kidneybeans': 8, 'pigeonpeas': 9, 'mothbeans': 10, 'mungbean': 11, 'blackgram': 12, 'lentil': 13,
                 'pomegranate': 14, 'banana': 15, 'mango': 16, 'watermelon': 17, 'muskmelon': 18, 'apple': 19,
                 'orange': 20, 'papaya': 21, 'coconut': 22, 'jute': 23, 'coffee': 24, 'Soyabeans': 25, 'beans': 26,
                 'peas': 27, 'cowpeas': 28}

    if request.method == 'POST':
        N = float(request.form['N'])
        P = float(request.form['P'])
        K = float(request.form['K'])
        Temperature = float(request.form['temperature'])
        Rainfall = float(request.form['rainfall'])
        Ph = float(request.form['ph'])
        crop_name = request.form['crop']
        email = session.get('email')

        if crop_name in crop_dict:
            crop = crop_dict[crop_name] 
        else:
            return "Invalid crop name"

        input_data = [[N, P, K,Temperature,Rainfall,Ph,crop]]
        predict3 = model1.predict(input_data)[0]

        try:
            html_content = render_template('mail1.html',N=N, P=P, K=K, Temperature=Temperature,Rainfall=Rainfall,Ph=Ph,crop=crop_name, predict=predict3)
            msg = Message(subject='Fertilizer Recommendation Result',
                  recipients=[email],
                  html=html_content)
            mail.send(msg)
        except Exception as e:
            print(e)

        return render_template('result1.html', predict=predict3)

    else:
        return render_template("main.html")


if __name__ == '__main__':
    app.run(debug=True)

