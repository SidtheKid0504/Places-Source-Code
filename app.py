#Install Dependencies With pip install In Your Command Line Or Terminal 
from email.policy import default # Dependency Gets Installed By Default When Using flask_mail
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_cors import CORS, cross_origin
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import os

#Initialize Flask App
app = Flask(__name__)
app.config.from_pyfile('.env')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')[:8] + "ql" + os.environ.get('DATABASE_URL')[8:] 
app.config['MAIL_PORT'] = int(app.config['MAIL_PORT'])

CORS(app)
Session(app)
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
mail = Mail(app)

#Serializes URl
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

#Initalize SQLAlchemy Tables
class Pixel(db.Model):
  __tablename__ = 'pixels'
  id = db.Column('id_of_pixel', db.Integer, primary_key = True)
  pixel_id = db.Column(db.String)
  color = db.Column(db.String)

class User(db.Model):
  __tablename__ = 'users'
  id = db.Column('user_id', db.Integer, primary_key = True)
  email = db.Column(db.String)
  username = db.Column(db.String)
  password = db.Column(db.String)
  confirmed = db.Column(db.Boolean, nullable=False, default=False)
  last_pixel_placed = db.Column(db.String)
  db.UniqueConstraint('email', 'username', name='login_info')

#Home Route
@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def home():
  #Get All Pixels Already Placed
  all_pixels = Pixel.query.all()
  pixels = []
  for i in all_pixels:
    pixels.append(
      {
        "id": i.id, 
        "pixel_id": i.pixel_id,
        "color": i.color
      }
    )
  #Run If Data Is Being Sent To Server 
  if request.method == 'POST':
    #Check If User Is Logging In
    if 'login_username' in request.form and 'login_password' in request.form:
      login_username = request.form['login_username']
      login_password = request.form['login_password']
      user_found = db.session.query(User).filter_by(username=login_username).filter_by(password=login_password).filter_by(confirmed=True).first()
      if user_found != None: 
        #Set Session's Current User To Inputted User
        session["curr_user"] = user_found
        session["curr_email"] = user_found.email
        #Return Canvas While Sending Data To Client Side
        return render_template('index.html', pixels=pixels, current_username=session["curr_user"].username, last_pixel=session["curr_user"].last_pixel_placed, user_not_found=False)
      else:
        #Rerender Login Modal 
        return render_template('index.html', user_not_found = True)
    #Check If User Is Placing A Pixel
    if 'color' in request.form:
      #Get Data From Client Of Pixel Information 
      color = request.form['color']
      pixel_id = request.form['pixel_id']
      last_time_pixel_placed = request.form['last_time_pixel_placed'] 
      
      #Get The Current User And Pixel
      loggedUser = db.session.query(User).filter_by(username=session["curr_user"].username).first()
      curr_pixel = db.session.query(Pixel).filter_by(pixel_id=pixel_id).first()
      #If The Pixel Isn't Already Used, Make A New One
      #Else Change The Color Of The Pixel
      if curr_pixel == None:
        curr_pixel = Pixel(pixel_id=pixel_id, color=color)
      else:
        curr_pixel.color = color

      #Send The Data To All Other Users
      socketio.emit('send_pixel', {
          "pixel_id": curr_pixel.pixel_id,
          "color": curr_pixel.color,
      })

      #Update The Last Time The User Placed The Pixel
      loggedUser.last_pixel_placed = last_time_pixel_placed

      #Add And Save Data To Database
      db.session.add(curr_pixel)
      db.session.commit()
    
    #Check If User Is Sending A Message That Isn't Empty
    if 'message' in request.form and request.form['message'] != "":

      #Send Message To All Other Users
      socketio.emit('send_message', {
        "current_username": session["curr_user"].username, 
        "message": request.form['message']
      })

  #Render Login Modal And Home Page When User Enter
  return render_template('index.html', pixels=pixels, current_user="", user_not_found=False)

#Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
  #Function To Send Verication Email To User's Email
  #Change Sender To Whatever Email You Want To Use 
  def send_email(email):
    token = s.dumps(email, salt="email-confirm")
    msg = Message('Confirm Email', sender="places0504@gmail.com", recipients=[email])
    link = url_for('confirm_email', token=token, external=True)
    msg.body = 'Your link is {}'.format(app.config["CURRENT_DOMAIN"]+link)
    mail.send(msg)

  if request.method == 'POST':
    #Check If User Is Entering Account Information 
    if 'email' in request.form:
      email = request.form['email']
      username = request.form['username']
      password = request.form['password']
      #Check If User Is Already Added
      if db.session.query(User).filter_by(email=email).first():
        return render_template('signup.html', email_exists=True, username_exists=False)
      elif db.session.query(User).filter_by(username=username).first():
        return render_template('signup.html', email_exists=False, username_exists=True)
      curr_user = User(email=email, username=username, password=password)
      session['curr_email'] = email
      db.session.add(curr_user)
      db.session.commit()
      send_email(email)
    #Check If User Is Resending Verification Email
    if not 'email' in request.form:
      send_email(session['curr_email'])
    return render_template('notif.html')
  return render_template('signup.html', email_exists=False, username_exists=False)

#Verification Route
@app.route('/confirm_email/<token>')
def confirm_email(token):
  #Confirm User When They Enter Link
  try:
    email = s.loads(token, salt="email-confirm", max_age=120)
    foundUser = db.session.query(User).filter_by(email=email).first()
    foundUser.confirmed = True

    db.session.commit()
  #Check If The Verification Email Expired
  except SignatureExpired:
    return render_template('expired.html')
  return render_template('verify.html', link=app.config["CURRENT_DOMAIN"]+url_for('home'))

#Forgot Password Route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
  #Function To Send Forgot Password Link
  def send_email(email):
    token = s.dumps(email, salt="email-confirm")
    msg = Message('Request To Change Password', sender="places0504@gmail.com", recipients=[email])
    link = url_for('change_password', token=token, external=True)
    msg.body = 'Link To Change Password {}'.format(app.config["CURRENT_DOMAIN"]+link)
    mail.send(msg)

  if request.method == 'POST':
    #Check If Email Is Registered
    if db.session.query(User).filter_by(email=request.form['email']).first():
      send_email(request.form['email'])
    #Else Send Message That Account Doesn't Exist
    else:
      return render_template('forgot_password.html', email_exists=False)
  return render_template('forgot_password.html', email_exists=True)

#Change Password Route
@app.route('/change_password/<token>', methods=['GET', 'POST'])
def change_password(token):
  try:
    #Get Email And Change Password To Input 
    email = s.loads(token, salt="email-confirm", max_age=180)
    if request.method == 'POST':
      #Check If Password Was Properly Confirmed And Redirect Back To Home Page
      if request.form['new-password'] == request.form['confirm-password']:
        find_user = db.session.query(User).filter_by(email=email).first()
        find_user.password = request.form['new-password']

        db.session.commit()
        return redirect(url_for('home'))
      #Else Send Message That Password Don't Match
      else:
        return render_template('change_password.html', token=token, pass_matched=False)
    #Show The Password To Change Passwords 
    return render_template('change_password.html', token=token, pass_matched=True)
  except SignatureExpired:
    return render_template('expired.html')

#Run App
if __name__ == '__main__':
  socketio.run(app, port=int(os.enviorn.get("PORT", 5000)))