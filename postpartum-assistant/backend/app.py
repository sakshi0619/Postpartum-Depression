import os
import secrets
import random
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from textblob import TextBlob
from werkzeug.exceptions import NotFound
from jinja2 import TemplateNotFound

# ====== EPDS QUESTIONS DATA ======
EPDS_QUESTIONS = {
    1: {
        "text": "I have been able to laugh and see the funny side of things",
        "options": [
            {"text": "As much as I always could", "value": 0},
            {"text": "Not quite so much now", "value": 1},
            {"text": "Definitely not so much now", "value": 2},
            {"text": "Not at all", "value": 3}
        ]
    },
    2: {
        "text": "I have looked forward with enjoyment to things",
        "options": [
            {"text": "As much as I ever did", "value": 0},
            {"text": "Rather less than I used to", "value": 1},
            {"text": "Definitely less than I used to", "value": 2},
            {"text": "Hardly at all", "value": 3}
        ]
    },
    3: {
        "text": "I have blamed myself unnecessarily when things went wrong",
        "options": [
            {"text": "Yes, most of the time", "value": 3},
            {"text": "Yes, some of the time", "value": 2},
            {"text": "Not very often", "value": 1},
            {"text": "No, never", "value": 0}
        ]
    },
    4: {
        "text": "I have been anxious or worried for no good reason",
        "options": [
            {"text": "No, not at all", "value": 0},
            {"text": "Hardly ever", "value": 1},
            {"text": "Yes, sometimes", "value": 2},
            {"text": "Yes, very often", "value": 3}
        ]
    },
    5: {
        "text": "I have felt scared or panicky for no very good reason",
        "options": [
            {"text": "Yes, quite a lot", "value": 3},
            {"text": "Yes, sometimes", "value": 2},
            {"text": "No, not much", "value": 1},
            {"text": "No, not at all", "value": 0}
        ]
    },
    6: {
        "text": "Things have been getting on top of me",
        "options": [
            {"text": "Yes, most of the time I haven't been able to cope at all", "value": 3},
            {"text": "Yes, sometimes I haven't been coping as well as usual", "value": 2},
            {"text": "No, most of the time I have coped quite well", "value": 1},
            {"text": "No, I have been coping as well as ever", "value": 0}
        ]
    },
    7: {
        "text": "I have been so unhappy that I have had difficulty sleeping",
        "options": [
            {"text": "Yes, most of the time", "value": 3},
            {"text": "Yes, sometimes", "value": 2},
            {"text": "Not very often", "value": 1},
            {"text": "No, not at all", "value": 0}
        ]
    },
    8: {
        "text": "I have felt sad or miserable",
        "options": [
            {"text": "Yes, most of the time", "value": 3},
            {"text": "Yes, quite often", "value": 2},
            {"text": "Not very often", "value": 1},
            {"text": "No, not at all", "value": 0}
        ]
    },
    9: {
        "text": "I have been so unhappy that I have been crying",
        "options": [
            {"text": "Yes, most of the time", "value": 3},
            {"text": "Yes, quite often", "value": 2},
            {"text": "Only occasionally", "value": 1},
            {"text": "No, never", "value": 0}
        ]
    },
    10: {
        "text": "The thought of harming myself has occurred to me",
        "options": [
            {"text": "Never", "value": 0},
            {"text": "Hardly ever", "value": 1},
            {"text": "Sometimes", "value": 2},
            {"text": "Yes, quite often", "value": 3}
        ]
    }
}
# ====== END EPDS DATA ======
  

# Initialize Flask app with robust template path handling
BASE_DIR = Path(__file__).parent.resolve()
TEMPLATE_DIR = BASE_DIR / 'templates'

# ====== ADD DEBUG PRINTS HERE ======
print("=" * 50)
print("DEBUG TEMPLATE PATHS:")
print(f"1. BASE_DIR: {BASE_DIR}")
print(f"2. TEMPLATE_DIR: {TEMPLATE_DIR}")
print(f"3. Template folder exists: {TEMPLATE_DIR.exists()}")

# Check for epds_form.html
epds_path = TEMPLATE_DIR / 'resources' / 'epds_form.html'
print(f"4. EPDS template path: {epds_path}")
print(f"5. EPDS template exists: {epds_path.exists()}")

# List files in templates/resources
resources_dir = TEMPLATE_DIR / 'resources'
if resources_dir.exists():
    print(f"6. Files in resources folder:")
    for file in resources_dir.glob('*'):
        print(f"   - {file.name}")
else:
    print(f"6. Resources folder doesn't exist!")

print("=" * 50)
# ====== END DEBUG ======

if not TEMPLATE_DIR.exists():
    raise RuntimeError(f"Templates folder missing at {TEMPLATE_DIR}")

app = Flask(__name__, template_folder=str(TEMPLATE_DIR))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(24)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True



# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Database models (unchanged from your original)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    with app.app_context():
     db.create_all()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ========= ADD FROM HERE =========
class ScreeningSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_score = db.Column(db.Integer)
    result_category = db.Column(db.String(50))
    q10_score = db.Column(db.Integer)  # NEW LINE ADDED HERE
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ScreeningResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('screening_session.id'))
    question_number = db.Column(db.Integer)
    answer_value = db.Column(db.Integer)
# ========= TO HERE =========

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def determine_sentiment(text, polarity):
    print(f"Determining sentiment for polarity: {polarity}")
    if polarity > 0.2:
        result = 'positive', polarity
    elif polarity < -0.2:
        result = 'negative', abs(polarity)
    else:
        result = 'neutral', 1.0 - abs(polarity)
    print(f"Returning: {result}")
    return result

# Template verification system
def verify_template(template_path):
    """Ensure template exists with proper case sensitivity"""
    full_path = TEMPLATE_DIR / template_path

    # Template verification system
def verify_template(template_path):
    """Ensure template exists with proper case sensitivity"""
    full_path = TEMPLATE_DIR / template_path
    
    # ====== ADD DEBUG PRINTS HERE ======
    print(f"\n🔍 VERIFY_TEMPLATE: Looking for '{template_path}'")
    print(f"   Full path: {full_path}")
    print(f"   Full path exists: {full_path.exists()}")
    
    if not full_path.exists():
        print(f"   ❌ Template not found at main path!")
        # Try to find case-insensitive match (for Windows/Mac development)
        matches = []
        for f in TEMPLATE_DIR.glob('**/*'):
            if f.name.lower() == Path(template_path).name.lower():
                matches.append(str(f.relative_to(TEMPLATE_DIR)))
        
        if matches:
            print(f"   ✅ Found {len(matches)} case-insensitive match(es):")
            for match in matches:
                print(f"      - {match}")
            return str(matches[0])
        else:
            print(f"   ❌❌ No matches found anywhere in {TEMPLATE_DIR}!")
            raise TemplateNotFound(template_path)
    
    print(f"   ✅ Template found!")
    return template_path

@app.before_request
def check_templates():
    """Verify required templates exist on startup"""
    required_templates = {
        'auth/login.html': verify_template('auth/login.html'),
        'auth/register.html': verify_template('auth/register.html'),
        'analyze/form.html': verify_template('analyze/form.html'),
        'analyze/results.html': verify_template('analyze/results.html'),
        'history.html': verify_template('history.html'),
        'dashboard.html': verify_template('dashboard.html'),
        'errors/404.html': verify_template('errors/404.html'),
        'errors/500.html': verify_template('errors/500.html'),
        # ADD THIS LINE:
        'resources/epds_form.html': verify_template('resources/epds_form.html')
    }
    app.config['VERIFIED_TEMPLATES'] = required_templates

def render_verified(template_name, **context):
    """Safe template renderer with verification"""
    try:
        verified_path = app.config['VERIFIED_TEMPLATES'][template_name]
        return render_template(verified_path, **context)
    except KeyError:
        raise NotFound(f"Template '{template_name}' not registered")
    except TemplateNotFound:
        raise NotFound(f"Template file missing: {template_name}")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Get the next page from URL parameter
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            
            # Get next page from URL parameter
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            
            # Redirect to next page or dashboard
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
            
        flash('Invalid username or password', 'error')
    
    return render_verified('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_verified('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Main Application Routes (modified to use render_verified)
@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get analysis counts
    total_analyses = Analysis.query.filter_by(user_id=current_user.id).count()
    positive_count = Analysis.query.filter_by(user_id=current_user.id, sentiment='positive').count()
    neutral_count = Analysis.query.filter_by(user_id=current_user.id, sentiment='neutral').count()
    negative_count = Analysis.query.filter_by(user_id=current_user.id, sentiment='negative').count()

    recent_analyses = Analysis.query.filter_by(user_id=current_user.id)\
                     .order_by(Analysis.timestamp.desc())\
                     .limit(5)\
                     .all()
    # Weekly stats (simplified)
    weekly_stats = {
        'positive': min(70, positive_count * 10),
        'neutral': min(20, neutral_count * 5),
        'negative': min(10, negative_count * 3)
    }
    
    # Daily tip
    daily_tips = [
        "Remember to take deep breaths throughout the day",
        "Try to get 10 minutes of sunlight today",
        "Reach out to a friend or family member",
        "Practice gentle stretching or walking"
    ]
    daily_tip = random.choice(daily_tips)

    return render_verified('dashboard.html', 
                         analyses=recent_analyses,
                         total_analyses=total_analyses,
                         positive_count=positive_count,
                         neutral_count=neutral_count,
                         negative_count=negative_count,
                         weekly_stats=weekly_stats,
                         daily_tip=daily_tip)

@app.route('/analyze', methods=['GET', 'POST'])
@login_required
def analyze_form():
    if request.method == 'POST':
        text = request.form.get('text')
        if not text or len(text.strip()) < 10:
            flash('Please enter valid text (minimum 10 characters)', 'error')
            return redirect(url_for('analyze_form'))
            
        analysis = TextBlob(text)
        sentiment, confidence = determine_sentiment(text, analysis.sentiment.polarity)
        
        print(f"=== DEBUG ===")
        print(f"Input text: {text}")
        print(f"TextBlob polarity: {analysis.sentiment.polarity}")
        print(f"Determined sentiment: {sentiment}")
        print(f"Confidence: {confidence}")
        print(f"=============")
        
        
        request_entry = Analysis(
            text=text,
            sentiment=sentiment,
            confidence=confidence,
            user_id=current_user.id
        )
        db.session.add(request_entry)
        db.session.commit()
        
          # ADD THIS PRINT HERE (around line 195)
        print(f"Stored in DB - Sentiment: '{request_entry.sentiment}', Confidence: {request_entry.confidence}")
        
        session['analysis_results'] = {
            'text': text,
            'sentiment': sentiment,
            'confidence': confidence,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        }
        return redirect(url_for('show_results'))
        
    return render_verified('analyze/form.html')
# Replace entire show_results() function (Lines 217-240) with:
@app.route('/results')
@login_required
def show_results():
    results = session.get('analysis_results')
    if not results:
        flash('No analysis results found', 'error')
        return redirect(url_for('analyze_form'))
    
    text = results.get('text', '')
    word_count = len(text.split())
    reading_time = f"{max(1, round(word_count/200))} min"

    # Add emergency contacts to the template context
    emergency_contacts = [
        {"name": "National Suicide Prevention Lifeline", "number": "988"},
        {"name": "Postpartum Support International", "number": "1-800-944-4773"},
        {"name": "Crisis Text Line", "number": "Text HOME to 741741"},
        {"name": "Emergency Services", "number": "911"}
    ]
    
    return render_verified(
        'analyze/results.html',
        results=results,
        sentiment=results.get('sentiment'),
        confidence=results.get('confidence'),
        reading_time=reading_time,
        word_count=word_count
    )

@app.route('/history')
@login_required
def history():
    """Render the history page with paginated analysis data"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Query analyses for current user with pagination
        analyses = Analysis.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Analysis.timestamp.desc()  # Using timestamp since that's what your model has
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('history.html', analyses=analyses)
        
    except Exception as e:
        flash('Error loading history: ' + str(e), 'error')
        return redirect(url_for('dashboard'))

# ... your existing routes (analyze, results, history, etc.) ...

# === ADD THE NEW RESOURCE ROUTES HERE ===
@app.route('/self-care-guide')
@login_required
def self_care_guide():
    """Self-care guide page"""
    return render_verified('resources/self_care.html')

@app.route('/support-groups')
@login_required
def support_groups():
    """Support groups information page"""
    return render_verified('resources/support_groups.html')

@app.route('/emergency-contacts')
@login_required
def emergency_contacts():
    """Emergency contacts page"""
    emergency_contacts = [
        {"name": "National Suicide Prevention Lifeline", "number": "988", "description": "24/7 free and confidential support"},
        {"name": "Postpartum Support International", "number": "1-800-944-4773", "description": "Specialized postpartum support"},
        {"name": "Crisis Text Line", "number": "Text HOME to 741741", "description": "24/7 crisis support via text"},
        {"name": "Emergency Services", "number": "911", "description": "Immediate emergency assistance"},
        {"name": "National Maternal Mental Health Hotline", "number": "1-833-943-5746", "description": "24/7 professional support"}
    ]
    return render_verified('resources/emergency_contacts.html', contacts=emergency_contacts)

@app.route('/api/analyze', methods=['POST'])  # Fixed typo: 'analyze' to 'analyze'
@login_required
def analyze_sentiment():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Analyze sentiment (replace with your actual analysis logic)
        sentiment, confidence = analyze_text_sentiment(text)
        
        # Save to database - Use your Analysis model (not SentimentAnalysis)
        analysis = Analysis(
            user_id=current_user.id,
            text=text,
            sentiment=sentiment,
            confidence=confidence
        )
        db.session.add(analysis)
        db.session.commit()
        
        return jsonify({
            'sentiment': sentiment,
            'confidence': confidence,
            'id': analysis.id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/api/history')
@login_required
def get_history():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # Use Analysis model (not SentimentAnalysis)
        analyses = Analysis.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Analysis.created_at.desc()  # Use created_at instead of timestamp
        ).paginate(page=page, per_page=per_page)
        
        history = []
        for analysis in analyses.items:
            # Shorten text for preview
            text_preview = analysis.text
            if len(text_preview) > 30:
                text_preview = text_preview[:27] + '...'
            
            history.append({
                'id': analysis.id,
                'date': analysis.created_at.strftime('%Y-%m-%d %H:%M'),  # Use created_at
                'text_preview': text_preview,
                'full_text': analysis.text,
                'sentiment': analysis.sentiment,
                'confidence': analysis.confidence
            })
        
        return jsonify({
            'history': history,
            'has_next': analyses.has_next,
            'has_prev': analyses.has_prev,
            'page': page,
            'total_pages': analyses.pages
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500    

@app.route('/screening-history')
@login_required
def screening_history():
    """View past screening results"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    screenings = ScreeningSession.query.filter_by(
        user_id=current_user.id
    ).order_by(
        ScreeningSession.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Screening History</h1>
        <p>Number of screenings: {screenings.total}</p>
    </body>
    </html>
    """

def analyze_text_sentiment(text):
    # Replace this with your actual sentiment analysis logic
    # This is a placeholder implementation
    negative_words = ['hate', 'not feeling', 'sad', 'depressed', 'anxious', 'tired']
    positive_words = ['happy', 'good', 'great', 'excited', 'joy', 'love']
    
    text_lower = text.lower()
    negative_count = sum(1 for word in negative_words if word in text_lower)
    positive_count = sum(1 for word in positive_words if word in text_lower)
    
    if negative_count > positive_count:
        return "Negative", 80.0
    elif positive_count > negative_count:
        return "Positive", 85.0
    else:
        return "Neutral", 70.0

# === ERROR HANDLERS (KEEP THESE AFTER THE NEW ROUTES) ===
@app.errorhandler(404)
def page_not_found(e):
    return render_verified('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_verified('errors/500.html'), 500

# API Endpoint (unchanged)
@app.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text parameter'}), 400
        
    text = data['text']
    analysis = TextBlob(text)
    sentiment, confidence = determine_sentiment(text, analysis.sentiment.polarity)
    
    return jsonify({
        'text': text,
        'sentiment': sentiment,
        'confidence': confidence,
        'user_id': current_user.id
    })

@app.route('/ppd-screening')  # or @app.route('/ppd-screening', methods=['GET', 'POST'])
@login_required
def ppd_screening():
    pass
    # Your current code here

@app.route('/submit-screening', methods=['POST'])
@login_required
def submit_screening():
    """Process EPDS questionnaire"""
    try:
        # Get all 10 question responses
        responses = {}
        total_score = 0
        
        for i in range(1, 11):
            answer = request.form.get(f'q{i}', type=int)
            if answer is None:
                flash(f'Please answer question {i}', 'error')
                return redirect(url_for('ppd_screening'))
            
            responses[i] = answer
            total_score += answer
        
        q10_score = responses[10]
        
        # Determine result category
        if q10_score >= 1:
            result_category = 'psychosis_warning'
        elif total_score >= 10:
            result_category = 'ppd'
        else:
            result_category = 'baby_blues'
        
        # Save to database
        session_record = ScreeningSession(
            user_id=current_user.id,
            total_score=total_score,
            result_category=result_category,
            q10_score=q10_score
        )
        db.session.add(session_record)
        db.session.flush()  # Get session ID
        
        # Save individual responses
        for q_num, answer in responses.items():
            response = ScreeningResponse(
                session_id=session_record.id,
                question_number=q_num,
                answer_value=answer
            )
            db.session.add(response)
        
        db.session.commit()
        
        # Store in session for results page
        session['screening_result'] = {
            'score': total_score,
            'category': result_category,
            'q10_score': q10_score,
            'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }
        
        # Redirect to results page
        return redirect(url_for('screening_results'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing screening: {str(e)}', 'error')
        return redirect(url_for('ppd_screening'))

@app.route('/screening-results')
@login_required
def screening_results():
    """Display enhanced EPDS screening results"""
    result = session.get('screening_result')
    if not result:
        flash('No screening results found', 'error')
        return redirect(url_for('ppd_screening'))
    
    # Get score and date
    score = result.get('score', 15)
    date_completed = result.get('date', datetime.now().strftime('%B %d, %Y'))
    
    # Render the enhanced results page
    return render_template('screening/results.html', 
                          score=score, 
                          date_completed=date_completed)
    # Emergency contacts
    emergency_contacts = [
        {"name": "National Suicide Prevention Lifeline", "number": "988"},
        {"name": "Postpartum Support International", "number": "1-800-944-4773"},
        {"name": "Crisis Text Line", "number": "Text HOME to 741741"}
    ]
    
    return f"""
    <!DOCTYPE html>
    <html>
    <body>
        <h1>Screening Results</h1>
        <p>Score: {result['score']}/30</p>
        <p>Result: {result['category']}</p>
    </body>
    </html>
    """


@app.route('/test-screen')
def test_screen():
    """Test PPD screening without login"""
    return "<h1 style='color: green;'>✅ TEST PAGE WORKING!</h1><p>If you see this, it's fixed!</p>"

# Error Handlers (modified to use render_verified)
@app.errorhandler(404)
def page_not_found(e):
    return render_verified('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback()
    return render_verified('errors/500.html'), 500

# Permanent debug route
@app.route('/template-info')
def template_info():
    """Permanent template debugging endpoint"""
    templates = {
        'base_directory': str(TEMPLATE_DIR),
        'verified_templates': app.config.get('VERIFIED_TEMPLATES', {}),
        'search_paths': list(app.jinja_loader.searchpath)
    }
    return jsonify(templates)

# Initialize database (unchanged)
def create_tables():
    with app.app_context():
        db.create_all()

def reset_database():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset complete!")

if __name__ == '__main__':
    # Validate directory structure
    required_dirs = ['analyze', 'auth', 'errors']
    for dir_name in required_dirs:
        dir_path = TEMPLATE_DIR / dir_name
        if not dir_path.exists():
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")

    # Validate critical templates
    critical_templates = [
        'analyze/results.html',
        'analyze/form.html',
        'auth/login.html',
        'base.html'
    ]
    
    for template in critical_templates:
        template_path = TEMPLATE_DIR / template
        if not template_path.exists():
            with open(template_path, 'w', encoding='utf-8') as f:
                content = f"""<!-- Auto-generated {template} -->
{{% extends 'base.html' %}}
{{% block content %}}
{{% endblock %}}"""
                f.write(content)
            print(f"Created template: {template}")

    create_tables()
    app.run(debug=True)