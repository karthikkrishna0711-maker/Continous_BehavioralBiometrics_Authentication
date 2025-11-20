from flask import Flask, render_template, request, jsonify, flash, session, redirect
import joblib
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# app password link https://myaccountapppasswords.google.com/
app_password = ""

app = Flask(__name__)
app.secret_key = ''

# Loading my the trained model
model = joblib.load("decision_tree_user1.pkl")

def connect_to_db():
    return psycopg2.connect(
        user="",
        password="",
        host="",
        port=,
        database=""
    )



conn = connect_to_db()
cursor = conn.cursor()


@app.route('/')
def login():
    return render_template("index.html")


@app.route('/add_users', methods=['POST'])
def add_users():
    name = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    cursor.execute("""
                INSERT INTO login(name, email, password)
               VALUES(%s, %s, %s)
               """, (name, email, password))
    conn.commit()


    cursor.execute("SELECT user_id FROM login WHERE email = %s", (email,))
    user_id = cursor.fetchone()[0]
    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email

    return render_template("successful.html")


@app.route('/login_validation', methods=['POST'])
def login_validation():
    email = request.form.get('username')
    password = request.form.get('password')

    cursor.execute("SELECT user_id, name, email FROM login WHERE email = %s AND password = %s", (email, password))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user[0]
        session['user_name'] = user[1]
        session['user_email'] = user[2]
        return redirect('/starter')
    else:
        flash('Invalid email or password', 'danger')
        return redirect('/')


@app.route('/starter')
def starter():
    name = session.get('user_name')
    if name:
        return render_template("index1.html", name=name)
    else:
        flash('Please log in first.', 'warning')
        return redirect('/')


@app.route("/user")
def user():

    return render_template("index1.html")


def send_email_alert(to_email):
    sender_email = ""
    subject = "Intruder Alert on Your Website"
    body = """
    Dear User,

    An unauthorized user (bot) was detected attempting to use your account on our website. 
    As a precaution, you have been logged out automatically.

    If this was not you, please contact support immediately.

    Best regards,
    support@123.com
    Website Security Team
    """


    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))


    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        print("Alert email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.route("/track", methods=["POST"])
def track():
    data = request.json

    avg_mouse_x = data.get("avg_mouse_x")
    avg_mouse_y = data.get("avg_mouse_y")
    num_clicks = data.get("num_clicks")
    scroll_speed = data.get("scroll_speed")
    typing_speed = data.get("typing_speed")

    if None in [avg_mouse_x, avg_mouse_y, num_clicks, scroll_speed, typing_speed]:
        return "Error: Missing input data", 400


    input_features = [[avg_mouse_x, avg_mouse_y, num_clicks, scroll_speed, typing_speed]]
    prediction = model.predict(input_features)[0]
    label_mapping = {1: 'authorized', 0: 'bot'}
    predicted_label = label_mapping[prediction]

    print(f"Prediction: {predicted_label}")

    if predicted_label == "bot":
        user_email = session.get('user_email')
        if user_email:
            send_email_alert(user_email)
            print("Sending alert email to:", user_email)



        session.clear()
        flash("Unauthorized access detected. You have been logged out.", "danger")
        return jsonify({"Prediction": "bot", "Action": "logout"})
    else:

        if 'user_id' not in session:
            flash("Session expired. Please log in again.", "warning")
            return redirect('/')

        return jsonify({"Prediction": predicted_label})


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect("/")


if __name__ == "__main__":
    app.run(port=3000, debug=True)

