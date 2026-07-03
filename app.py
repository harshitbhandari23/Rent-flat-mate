
import os, json, datetime
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, join_room, emit
from werkzeug.security import generate_password_hash, check_password_hash
from compatibility import get_compatibility_score
from mailer import send_email

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///rentflat.db')
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
import os


# ---------------- Models ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(20))  # tenant/owner/admin

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    location = db.Column(db.String(120))
    rent = db.Column(db.Integer)
    available_from = db.Column(db.String(20))
    room_type = db.Column(db.String(50))
    furnishing = db.Column(db.String(50))
    photo_url = db.Column(db.String(255))
    filled = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class TenantProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    preferred_location = db.Column(db.String(120))
    budget_min = db.Column(db.Integer)
    budget_max = db.Column(db.Integer)
    move_in_date = db.Column(db.String(20))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'))
    score = db.Column(db.Integer)
    explanation = db.Column(db.Text)
    status = db.Column(db.String(20), default='none')  # none/pending/accepted/declined
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(uid):
    return User.query.get(int(uid))

# ---------------- Auth ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        f = request.form
        if User.query.filter_by(email=f['email']).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        u = User(name=f['name'], email=f['email'],
                  password=generate_password_hash(f['password']), role=f['role'])
        db.session.add(u); db.session.commit()
        login_user(u)
        send_email(
    u.email,
    "Welcome to RentFlat 🎉",
    f"""Hello {u.name},

Welcome to RentFlat!

Your account has been created successfully.

Role: {u.role.capitalize()}
Email: {u.email}

Thank you for using RentFlat.

Regards,
RentFlat Team
"""
)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        f = request.form
        u = User.query.filter_by(email=f['email']).first()
        if u and check_password_hash(u.password, f['password']):
            login_user(u)
            send_email(
    u.email,
    "Login Successful - RentFlat",
    f"""Hello {u.name},

You have successfully logged in to your RentFlat account.

Login Details:

Name : {u.name}
Role : {u.role.capitalize()}
Email: {u.email}

If this login was not made by you, please change your password immediately and contact our support team.

Thank you for using RentFlat!

Regards,
RentFlat Team
"""
)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------------- Dashboard ----------------
@app.route('/')
@login_required
def dashboard():
    if current_user.role == 'owner':
        listings = Listing.query.filter_by(owner_id=current_user.id).all()
        return render_template('owner_dashboard.html', listings=listings)
    elif current_user.role == 'tenant':
        profile = TenantProfile.query.filter_by(tenant_id=current_user.id).first()
        return render_template('tenant_dashboard.html', profile=profile)
    else:
        users = User.query.all()
        listings = Listing.query.all()
        return render_template('admin_dashboard.html', users=users, listings=listings)

# ---------------- Owner: Listings ----------------
@app.route('/listing/new', methods=['GET', 'POST'])
@login_required
def new_listing():
    if current_user.role != 'owner':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        f = request.form
        l = Listing(owner_id=current_user.id, location=f['location'], rent=int(f['rent']),
                    available_from=f['available_from'], room_type=f['room_type'],
                    furnishing=f['furnishing'], photo_url=f.get('photo_url', ''))
        db.session.add(l); db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('new_listing.html')

@app.route('/listing/<int:lid>/fill')
@login_required
def fill_listing(lid):
    l = Listing.query.get_or_404(lid)
    if l.owner_id == current_user.id:
        l.filled = True
        db.session.commit()
    return redirect(url_for('dashboard'))

# ---------------- Tenant: Profile & Browse ----------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'tenant':
        return redirect(url_for('dashboard'))
    p = TenantProfile.query.filter_by(tenant_id=current_user.id).first()
    if request.method == 'POST':
        f = request.form
        if not p:
            p = TenantProfile(tenant_id=current_user.id)
            db.session.add(p)
        p.preferred_location = f['preferred_location']
        p.budget_min = int(f['budget_min'])
        p.budget_max = int(f['budget_max'])
        p.move_in_date = f['move_in_date']
        db.session.commit()
        return redirect(url_for('browse'))
    return render_template('profile.html', profile=p)

@app.route('/browse')
@login_required
def browse():
    if current_user.role != 'tenant':
        return redirect(url_for('dashboard'))
    profile = TenantProfile.query.filter_by(tenant_id=current_user.id).first()
    if not profile:
        return redirect(url_for('profile'))
    q = Listing.query.filter_by(filled=False)
    loc = request.args.get('location')
    if loc:
        q = q.filter(Listing.location.ilike(f'%{loc}%'))
    listings = q.all()
    results = []
    for l in listings:
        match = Match.query.filter_by(tenant_id=current_user.id, listing_id=l.id).first()
        if not match:
            score, explanation = get_compatibility_score(profile, l)
            match = Match(tenant_id=current_user.id, listing_id=l.id, score=score, explanation=explanation)
            db.session.add(match); db.session.commit()
        results.append((l, match))
    results.sort(key=lambda x: x[1].score, reverse=True)
    return render_template('browse.html', results=results)

# ---------------- Interest / Match flow ----------------
@app.route('/interest/<int:lid>')
@login_required
def express_interest(lid):
    l = Listing.query.get_or_404(lid)
    m = Match.query.filter_by(tenant_id=current_user.id, listing_id=lid).first()
    if m:
        m.status = 'pending'
        db.session.commit()
        owner = User.query.get(l.owner_id)
        if m.score > 80:
            send_email(owner.email, "High-match tenant interested!",
                       f"{current_user.name} ({m.score}% match) is interested in your listing at {l.location}.")
        else:
            send_email(owner.email, "New interest in your listing",
                       f"{current_user.name} is interested in your listing at {l.location}.")
    return redirect(url_for('browse'))

@app.route('/requests')
@login_required
def requests_list():
    if current_user.role != 'owner':
        return redirect(url_for('dashboard'))
    listing_ids = [l.id for l in Listing.query.filter_by(owner_id=current_user.id).all()]
    matches = Match.query.filter(Match.listing_id.in_(listing_ids), Match.status == 'pending').all()
    data = [(m, Listing.query.get(m.listing_id), User.query.get(m.tenant_id)) for m in matches]
    return render_template('requests.html', data=data)

@app.route('/respond/<int:mid>/<action>')
@login_required
def respond(mid, action):
    m = Match.query.get_or_404(mid)
    m.status = 'accepted' if action == 'accept' else 'declined'
    db.session.commit()
    tenant = User.query.get(m.tenant_id)
    l = Listing.query.get(m.listing_id)
    send_email(tenant.email, f"Your interest was {m.status}",
               f"Owner has {m.status} your interest in the listing at {l.location}.")
    return redirect(url_for('requests_list'))

@app.route('/chats')
@login_required
def chats():
    if current_user.role == 'tenant':
        matches = Match.query.filter_by(tenant_id=current_user.id, status='accepted').all()
    else:
        listing_ids = [l.id for l in Listing.query.filter_by(owner_id=current_user.id).all()]
        matches = Match.query.filter(Match.listing_id.in_(listing_ids), Match.status == 'accepted').all()
    data = [(m, Listing.query.get(m.listing_id), User.query.get(m.tenant_id)) for m in matches]
    return render_template('chats.html', data=data)

@app.route('/chat/<int:mid>')
@login_required
def chat_room(mid):
    m = Match.query.get_or_404(mid)
    msgs = Message.query.filter_by(match_id=mid).order_by(Message.created_at).all()
    return render_template('chat.html', match=m, messages=msgs)

@socketio.on('join')
def on_join(data):
    join_room(str(data['match_id']))

@socketio.on('send_message')
def on_send_message(data):
    m = Message(match_id=data['match_id'], sender_id=data['sender_id'], content=data['content'])
    db.session.add(m); db.session.commit()
    emit('receive_message', {
        'sender_id': data['sender_id'], 'sender_name': data['sender_name'],
        'content': data['content'], 'time': m.created_at.strftime('%H:%M')
    }, room=str(data['match_id']))

# ---------------- Admin ----------------
@app.route('/admin/user/<int:uid>/delete')
@login_required
def delete_user(uid):
    if current_user.role == 'admin':
        User.query.filter_by(id=uid).delete()
        db.session.commit()
    return redirect(url_for('dashboard'))

def seed_admin():
    if not User.query.filter_by(role='admin').first():
        db.session.add(User(name='Admin', email='admin@rentflat.com',
                             password=generate_password_hash('admin123'), role='admin'))
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_admin()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
