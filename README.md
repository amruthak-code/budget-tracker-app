# budget-tracker-app
cat > README.md << 'README'
# Budget Master - Personal Finance Tracker

A full-stack budget tracking application with real-time expense tracking and email alerts.

## 🚀 Live Demo

**Try it here:** https://sparkly-buttercream-7ea94e.netlify.app/
The above link will be active on my free-plan till Oct 28th. Later, it can be run on local host. 
- Backend API: https://budget-tracker-backend.onrender.com
- Fully functional with email alerts!

## ✨ Features

- ✅ User Registration & Authentication
- ✅ Customizable Budget Limits for 6 Categories
- ✅ Real-time Expense Tracking
- ✅ Progress Bars & Visual Indicators
- ✅ Email Alerts when Budget Limits Exceeded
- ✅ Expense History Tracking
- ✅ Responsive Design (Mobile & Desktop)
- ✅ PostgreSQL Database

## 🛠️ Tech Stack

**Frontend:**
- HTML5, CSS3, JavaScript (Vanilla)
- Responsive Design
- Hosted on Netlify

**Backend:**
- Python Flask
- SQLAlchemy ORM
- PostgreSQL Database
- SMTP Email Integration
- Hosted on Render

## 📸 Screenshots

Registration page:
<img width="1487" height="874" alt="registration" src="https://github.com/user-attachments/assets/47230874-8d35-4614-9eaa-669d87027536" />
Login page:
<img width="1361" height="886" alt="login" src="https://github.com/user-attachments/assets/2b91c32e-ef17-415e-81f2-e7ed7a9b8e31" />
Set your budget limits:
<img width="1466" height="896" alt="set budget limits" src="https://github.com/user-attachments/assets/2a2f7182-5f9b-42f6-92e8-f9f18fdd364b" />
Landing page of categories dashboard:
<img width="1504" height="903" alt="landing page" src="https://github.com/user-attachments/assets/347a1a85-e520-472d-bea9-bfe64054ebf2" />
Update of expenditure:
<img width="999" height="631" alt="updates" src="https://github.com/user-attachments/assets/ca98ca7b-6e86-4559-99df-0d41b7abc803" />
Dashboard tracking all categories:
<img width="1512" height="906" alt="dashboard" src="https://github.com/user-attachments/assets/7a61a173-a32a-4330-9380-b9de1cce7e36" />
When the limit is reached, you will receive an email like this:
<img width="1898" height="896" alt="image" src="https://github.com/user-attachments/assets/61fe8fe7-8f03-4636-9a88-69e9e917ba65" />




## 🏃 Local Development

### Backend Setup
```bash
cd backend
python3 -m venv budget_env
source budget_env/bin/activate
pip install -r requirements.txt
python3 app.py
