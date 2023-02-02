from flask import Flask, render_template, request, redirect, url_for ,session,make_response
import secrets
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import pymysql



app = Flask(__name__)
app.secret_key = '8f42a73054b1749f8f58848be5e6502c'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/link2'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class ReferralLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    username = db.Column(db.String(32), nullable=False)
    district = db.Column(db.String(255))
    location = db.Column(db.String(255))
    contact_number = db.Column(db.String(255))
    app_link = db.Column(db.String(512))


    def __repr__(self):
        return f'<ReferralLink code={self.code}>'

@app.route('/')
def index():
    return 'Hello, welcome to the referral link generator!'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'password': #Todo : change this system
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html')


@app.route('/admin', methods=['GET'])
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    host = request.host
    referral_links = ReferralLink.query.with_entities(ReferralLink.username, ReferralLink.district, ReferralLink.location, ReferralLink.contact_number, ReferralLink.code, ReferralLink.app_link, ReferralLink.clicks, ReferralLink.conversions).all()
    return render_template('admin.html', referral_links=referral_links, host=host)


@app.route('/create_link', methods=['POST'])
def create_link():
    referral_code = secrets.token_hex(8)
    username = request.form.get('username')
    district = request.form.get('district')
    location = request.form.get('location')
    contact_number = request.form.get('contact')
    app_link = request.form.get('app_link')

    existing_username = ReferralLink.query.filter_by(username=username).first()
    if existing_username:
        return redirect(url_for('admin'))
    referral_link = ReferralLink(code=referral_code, clicks=0, conversions=0, username=username, district=district, location=location, contact_number=contact_number, app_link=app_link)
    db.session.add(referral_link)
    db.session.commit()
    return redirect(url_for('admin'))



#host = request.host

@app.route('/referral/<referral_code>')
def referral(referral_code):
    referral_link = ReferralLink.query.filter_by(code=referral_code).first()
    if 'referral_clicked' not in request.cookies:
        response = make_response(render_template('test.html', code=referral_code,host=request.host))
        referral_link.clicks += 1
        db.session.commit()
        response.set_cookie('referral_clicked', '1')
        return response
    else:
        return render_template('test.html', code=referral_code,host=request.host)

@app.route('/convert/<referral_code>')
def convert(referral_code):
    referral_link = ReferralLink.query.filter_by(code=referral_code).first()
    if referral_link:
        # check if the cookie is set
        if 'converted' in request.cookies:
            return redirect(referral_link.app_link)
        else:
            referral_link.conversions += 1
            db.session.commit()
            resp = make_response(redirect(referral_link.app_link))
            resp.set_cookie('converted', 'True')
            return resp
    else:
        return "Invalid referral code"

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# @app.route('/stats')
# def stats():
#     referral_links = ReferralLink.query.all()
#     return render_template('stats.html', referral_links=referral_links)
