# 🏠 Rent Flatmate

A full-stack web application that helps users find rental properties and compatible flatmates based on lifestyle preferences. The platform provides separate dashboards for tenants, owners, and administrators, along with real-time chat and email notifications.

## 🌐 Live Demo

🔗 **https://rent-flat-mate-production.up.railway.app**

---

## ✨ Features

### 👤 User Authentication
- User Registration
- Secure Login
- Role-based Access Control
- User Profiles

### 🏠 Property Management
- Owners can create property listings
- Edit and delete listings
- Browse available rental properties
- View property details

### 🤝 Flatmate Matching
- AI-based compatibility scoring
- Lifestyle preference matching
- Match recommendations

### 💬 Real-Time Chat
- WebSocket-based messaging
- Instant communication between owners and tenants
- Conversation history

### 📩 Email Notifications
- Welcome email on registration
- SMTP integration using Brevo

### 👨‍💼 Admin Dashboard
- Manage users
- Manage property listings
- Platform monitoring

---

# 🛠 Tech Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-SocketIO

### Frontend
- HTML
- CSS
- JavaScript
- Jinja2 Templates

### Database
- SQLite

### Communication
- WebSockets (Socket.IO)

### Email Service
- Brevo SMTP

### Deployment
- Railway

---

# 📂 Project Structure

```
RentFlat/
│── app.py
│── compatibility.py
│── mailer.py
│── requirements.txt
│── Procfile
│── README.md
│── templates/
│── static/
│── instance/
```

---

# 🚀 Installation

Clone the repository

```bash
git clone https://github.com/your-username/rent-flatmate.git
```

Move into the project

```bash
cd rent-flatmate
```

Create a virtual environment

```bash
python -m venv venv
```

Activate the environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the application

```bash
python app.py
```

---

# ⚙ Environment Variables

Create a `.env` file in the project root.

```env
SECRET_KEY=your_secret_key

DATABASE_URL=sqlite:///rentflat.db

SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your_smtp_login
SMTP_PASS=your_smtp_password

SENDER_EMAIL=your_verified_email
SENDER_NAME=Rent Flatmate
```

---

# 📸 Screenshots

Add screenshots here:

- Home Page
- Login Page
- Registration Page
- Owner Dashboard
- Tenant Dashboard
- Admin Dashboard
- Property Listings
- Chat
- AI Compatibility Score

---

# 📌 Future Improvements

- PostgreSQL support
- Google Maps Integration
- Payment Gateway
- Password Reset
- Push Notifications
- Mobile Responsive UI Improvements
- AI Recommendation Enhancement

---

# 👨‍💻 Author

**Harshit Bhandari**

- GitHub: https://github.com/your-github-username
- LinkedIn: https://linkedin.com/in/your-linkedin

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub.
