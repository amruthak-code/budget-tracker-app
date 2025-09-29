from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///budget_tracker.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Email Configuration
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    monthly_savings_target = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    expenses = db.relationship('Expense', backref='user', lazy=True)
    budget_limits = db.relationship('BudgetLimit', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    icon = db.Column(db.String(50))
    color = db.Column(db.String(7))
    
    expenses = db.relationship('Expense', backref='category', lazy=True)
    budget_limits = db.relationship('BudgetLimit', backref='category', lazy=True)

class BudgetLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    monthly_limit = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    notification_type = db.Column(db.String(50))

# Helper Functions
def send_email(to_email, subject, body):
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            print("Email credentials not configured")
            return False
            
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def check_budget_and_notify(user_id, category_id):
    user = User.query.get(user_id)
    category = Category.query.get(category_id)
    budget_limit = BudgetLimit.query.filter_by(user_id=user_id, category_id=category_id).first()
    
    if not budget_limit:
        return
    
    # Calculate total expenses for current month
    current_month = date.today().replace(day=1)
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.category_id == category_id,
        Expense.expense_date >= current_month
    ).all()
    
    total_spent = sum(expense.amount for expense in expenses)
    
    # Check if budget limit exceeded
    if total_spent >= budget_limit.monthly_limit:
        # Check if notification already sent this month
        notification_exists = Notification.query.filter(
            Notification.user_id == user_id,
            Notification.category_id == category_id,
            Notification.sent_at >= datetime.combine(current_month, datetime.min.time())
        ).first()
        
        if not notification_exists:
            # Send email notification
            subject = f"Budget Alert: {category.name} Limit Reached"
            body = f"""
            Dear {user.name},
            
            You have reached your monthly budget limit for {category.name}.
            
            Budget Limit: ${budget_limit.monthly_limit:.2f}
            Amount Spent: ${total_spent:.2f}
            
            Consider reviewing your expenses to stay within budget.
            
            Best regards,
            Budget Master App
            """
            
            if send_email(user.email, subject, body):
                # Log notification
                notification = Notification(
                    user_id=user_id,
                    category_id=category_id,
                    notification_type='budget_exceeded'
                )
                db.session.add(notification)
                db.session.commit()

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(
        email=data['email'],
        name=data['name'],
        password_hash=generate_password_hash(data['password']),
        monthly_savings_target=data.get('monthly_savings_target', 0)
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully', 'user_id': user.id}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({
            'message': 'Login successful',
            'user_id': user.id,
            'name': user.name,
            'email': user.email
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': cat.id,
        'name': cat.name,
        'icon': cat.icon,
        'color': cat.color
    } for cat in categories])

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.get_json()
    
    expense = Expense(
        user_id=data['user_id'],
        category_id=data['category_id'],
        amount=data['amount'],
        description=data.get('description', ''),
        expense_date=datetime.strptime(data.get('expense_date', str(date.today())), '%Y-%m-%d').date()
    )
    
    db.session.add(expense)
    db.session.commit()
    
    # Check budget and send notification if needed
    check_budget_and_notify(data['user_id'], data['category_id'])
    
    return jsonify({'message': 'Expense added successfully', 'expense_id': expense.id}), 201

@app.route('/api/expenses/<int:user_id>', methods=['GET'])
def get_expenses(user_id):
    expenses = db.session.query(Expense, Category).join(Category).filter(Expense.user_id == user_id).all()
    
    return jsonify([{
        'id': expense.Expense.id,
        'amount': expense.Expense.amount,
        'description': expense.Expense.description,
        'expense_date': expense.Expense.expense_date.isoformat(),
        'category_name': expense.Category.name,
        'category_icon': expense.Category.icon
    } for expense in expenses])

@app.route('/api/budget-limits', methods=['POST'])
def set_budget_limits():
    data = request.get_json()
    user_id = data['user_id']
    
    # Update savings target
    user = User.query.get(user_id)
    user.monthly_savings_target = data.get('monthly_savings_target', 0)
    
    # Update budget limits
    for limit_data in data['limits']:
        existing_limit = BudgetLimit.query.filter_by(
            user_id=user_id,
            category_id=limit_data['category_id']
        ).first()
        
        if existing_limit:
            existing_limit.monthly_limit = limit_data['amount']
        else:
            budget_limit = BudgetLimit(
                user_id=user_id,
                category_id=limit_data['category_id'],
                monthly_limit=limit_data['amount']
            )
            db.session.add(budget_limit)
    
    db.session.commit()
    return jsonify({'message': 'Budget limits updated successfully'}), 200

@app.route('/api/budget-status/<int:user_id>', methods=['GET'])
def get_budget_status(user_id):
    current_month = date.today().replace(day=1)
    
    # Get budget limits
    budget_limits = BudgetLimit.query.filter_by(user_id=user_id).all()
    
    status = []
    for limit in budget_limits:
        # Calculate expenses for current month
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.category_id == limit.category_id,
            Expense.expense_date >= current_month
        ).all()
        
        total_spent = sum(expense.amount for expense in expenses)
        
        category = Category.query.get(limit.category_id)
        status.append({
            'category_id': limit.category_id,
            'category_name': category.name,
            'category_icon': category.icon,
            'category_color': category.color,
            'limit': limit.monthly_limit,
            'spent': total_spent,
            'remaining': max(0, limit.monthly_limit - total_spent),
            'percentage': min(100, (total_spent / limit.monthly_limit) * 100) if limit.monthly_limit > 0 else 0
        })
    
    return jsonify(status)

# Initialize database
def init_db():
    db.create_all()
    
    # Add default categories if they don't exist
    if Category.query.count() == 0:
        categories = [
            {'name': 'Groceries', 'icon': '🛒', 'color': '#27ae60'},
            {'name': 'Outside Food', 'icon': '🍕', 'color': '#e74c3c'},
            {'name': 'Gas', 'icon': '⛽', 'color': '#f39c12'},
            {'name': 'Rent', 'icon': '🏠', 'color': '#3498db'},
            {'name': 'Lent Money', 'icon': '🤝', 'color': '#9b59b6'},
            {'name': 'Additional', 'icon': '💳', 'color': '#34495e'}
        ]
        
        for cat_data in categories:
            category = Category(**cat_data)
            db.session.add(category)
        
        db.session.commit()
@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Test endpoint to verify email configuration"""
    data = request.get_json()
    to_email = data.get('to_email')
    subject = data.get('subject', 'Budget Tracker - Test Email')
    message = data.get('message', 'This is a test email from Budget Tracker')
    
    if not to_email:
        return jsonify({'error': 'Email address required'}), 400
    
    try:
        if send_email(to_email, subject, message):
            return jsonify({'message': 'Email sent successfully!'}), 200
        else:
            return jsonify({'error': 'Failed to send email. Check EMAIL_USER and EMAIL_PASSWORD in .env'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug-email-config', methods=['GET'])
def debug_email_config():
    """Debug endpoint to check email configuration"""
    return jsonify({
        'email_host': EMAIL_HOST,
        'email_port': EMAIL_PORT,
        'email_user': EMAIL_USER if EMAIL_USER else 'NOT SET',
        'email_password': 'SET' if EMAIL_PASSWORD else 'NOT SET'
    })

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Test endpoint to verify email configuration"""
    data = request.get_json()
    to_email = data.get('to_email')
    subject = data.get('subject', 'Budget Tracker - Test Email')
    message = data.get('message', 'This is a test email from Budget Tracker')
    
    if not to_email:
        return jsonify({'error': 'Email address required'}), 400
    
    try:
        if send_email(to_email, subject, message):
            return jsonify({'message': 'Email sent successfully!'}), 200
        else:
            return jsonify({'error': 'Failed to send email. Check EMAIL_USER and EMAIL_PASSWORD in .env'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

