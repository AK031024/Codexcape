from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import sqlite3
import os
import hashlib
import random
import google.generativeai as genai
from datetime import datetime
import json

app = Flask(__name__)

# Simple configuration (no YAML needed)
app.secret_key = 'storyweaver-secret-key-2024'
DATABASE_PATH = os.path.join('instance', 'storyweaver.db')

# Configure Gemini AI - Direct key usage
GEMINI_API_KEY = 'AIzaSyD813g9qRIqaOdxnrxYBIezlOZIuBOSbFc'

# Use gemini-3-flash-preview directly - reliable model for API 3.0
GEMINI_MODEL_NAME = 'gemini-3-flash-preview'

def configure_gemini():
    """Configure Gemini AI with direct model selection"""
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not found")
        return None
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        print("Gemini AI configured successfully")
        print(f"Using model: {GEMINI_MODEL_NAME}")
        return GEMINI_MODEL_NAME
    except Exception as e:
        print(f"Gemini AI configuration error: {e}")
        return None

# Configure Gemini during startup
GEMINI_MODEL = configure_gemini()

def get_db_connection():
    """Get database connection"""
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables with schema updates"""
    conn = get_db_connection()
    
    # Users table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Creative profiles table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS creative_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            writing_samples TEXT,
            preferred_genres TEXT,
            tone_preferences TEXT,
            favorite_authors TEXT,
            voice_fingerprint TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Writing projects table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS writing_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL DEFAULT 'Untitled',
            genre TEXT DEFAULT 'General',
            content TEXT,
            characters TEXT,
            world_settings TEXT,
            word_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # AI generations table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS ai_generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            generation_type TEXT NOT NULL,
            prompt TEXT,
            result TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Check if word_count column exists, if not add it
    try:
        conn.execute('SELECT word_count FROM writing_projects LIMIT 1')
        print("word_count column exists")
    except sqlite3.OperationalError:
        print("Adding word_count column to writing_projects table...")
        conn.execute('ALTER TABLE writing_projects ADD COLUMN word_count INTEGER DEFAULT 0')
        print("Updated writing_projects table")
    
    # Add sample data for demo
    try:
        # Check if we need to add sample user
        user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        if user_count == 0:
            print("Adding sample user and projects...")
            # Add sample user
            conn.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                ('unni', 'unni@storyweaver.com', hash_password('password123'))
            )
            user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Add sample projects
            sample_projects = [
                ('The Last Starweaver', 'Fantasy', 'In a galaxy where constellations are living entities, a young astronomer discovers she can communicate with them...', 3450),
                ('Whispers in the Mist', 'Mystery', 'A detective with the ability to hear ghosts takes on a cold case that leads her to a small coastal town...', 1280),
                ('Chronicles of Aetheria', 'Fantasy', 'In a world where magic is drawn from the elements, a young mage without elemental affinity discovers...', 8760)
            ]
            
            for title, genre, content, word_count in sample_projects:
                conn.execute(
                    'INSERT INTO writing_projects (user_id, title, genre, content, word_count) VALUES (?, ?, ?, ?, ?)',
                    (user_id, title, genre, content, word_count)
                )
            
            conn.commit()
            print("Sample data added successfully")
    except Exception as e:
        print(f"Error adding sample data: {e}")
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def calculate_word_count(content):
    """Calculate word count for content"""
    if not content:
        return 0
    return len(content.split())

class StoryWeaverAI:
    """AI service for story generation using Gemini AI"""
    
    @staticmethod
    def is_ai_available():
        """Check if AI service is available"""
        return GEMINI_API_KEY and GEMINI_MODEL
    
    @staticmethod
    def generate_story_idea(genre, tone="creative"):
        """Generate unique story ideas using Gemini AI each time - SHORT & PROFESSIONAL"""
        if not StoryWeaverAI.is_ai_available():
            return "Gemini AI service is not currently available. Please check your API key configuration."
        
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            # Short, crisp prompts for professional output
            prompt_variations = [
                f"Create a concise {genre} story idea (2-3 sentences). Focus on unique premise and clear conflict.",
                f"Generate a brief {genre} concept: protagonist, central conflict, and unique element. Keep it under 100 words.",
                f"Provide a short professional {genre} story premise with one surprising twist."
            ]
            
            prompt = random.choice(prompt_variations)
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Gemini AI error: {e}")
            return f"Gemini AI encountered an error: {str(e)}. Please try again."
    
    @staticmethod
    def generate_dialogue(character_desc, context):
        """Generate character dialogue using Gemini AI only - SHORT & PROFESSIONAL"""
        if not StoryWeaverAI.is_ai_available():
            return "Gemini AI service is not currently available. Please check your API key configuration."
        
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = f"Create 2-3 lines of natural dialogue for: {character_desc}. Context: {context}. Keep it brief and impactful."
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini AI dialogue error: {e}")
            return f"Gemini AI encountered an error: {str(e)}. Please try again."
    
    @staticmethod
    def generate_world_building(genre, theme):
        """Generate world-building elements using Gemini AI only - SHORT & PROFESSIONAL"""
        if not StoryWeaverAI.is_ai_available():
            return "Gemini AI service is not currently available. Please check your API key configuration."
        
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = f"Create 2-3 concise world-building elements for {genre} with theme: {theme}. Focus on key unique aspects only."
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini AI world-building error: {e}")
            return f"Gemini AI encountered an error: {str(e)}. Please try again."
    
    @staticmethod
    def generate_inspiration(prompt_type):
        """Generate inspiration using Gemini AI only - SHORT & PROFESSIONAL"""
        if not StoryWeaverAI.is_ai_available():
            return "Gemini AI service is not currently available. Please check your API key configuration."
        
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            
            if prompt_type == 'plot':
                prompt = "Generate one concise plot twist or story premise (2 sentences max). Make it unexpected but coherent."
            else:
                prompt = "Create one brief, inspiring writing prompt (1 sentence). Make it thought-provoking but clear."
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini AI inspiration error: {e}")
            return f"Gemini AI encountered an error: {str(e)}. Please try again."

def generate_with_gemini_ai(prompt, image_file=None):
    """Generate content using Gemini AI for custom prompts - SHORT & PROFESSIONAL"""
    try:
        if not StoryWeaverAI.is_ai_available():
            return "Gemini AI service is not currently available. Please check your API key configuration."
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Short, professional prompt
        final_prompt = f"""Based on: "{prompt}"
        
Generate a concise story idea (2-3 sentences). Include:
- Clear protagonist
- Central conflict  
- One unique element
Keep it professional and under 100 words."""
        
        response = model.generate_content(final_prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini AI generation error: {e}")
        return f"Gemini AI encountered an error: {str(e)}. Please try again."

# Initialize database
init_db()
ai_service = StoryWeaverAI()

# Routes - FIXED: Index route now properly shows index.html first
@app.route('/')
def index():
    """Home/Landing page - This should be the first page users see"""
    # Clear any existing session to ensure fresh start
    session.clear()
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Main writing dashboard - Requires login"""
    # Check if user is logged in, if not redirect to login
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    projects = conn.execute(
        'SELECT * FROM writing_projects WHERE user_id = ? ORDER BY updated_at DESC',
        (session['user_id'],)
    ).fetchall()
    
    # Calculate total word count
    total_words = conn.execute(
        'SELECT COALESCE(SUM(word_count), 0) as total FROM writing_projects WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()['total']
    
    conn.close()
    
    # Convert projects to list of dictionaries for easier template handling
    projects_list = []
    for project in projects:
        projects_list.append({
            'id': project['id'],
            'title': project['title'],
            'genre': project['genre'],
            'content': project['content'],
            'word_count': project['word_count'],
            'updated_at': project['updated_at']
        })
    
    return render_template('dashboard.html', 
                         projects=projects_list, 
                         username=session.get('username', 'Writer'),
                         total_words=total_words,
                         project_count=len(projects_list),
                         ai_available=StoryWeaverAI.is_ai_available())

@app.route('/project/<int:project_id>')
def project_editor(project_id):
    """Project editor page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    project = conn.execute(
        'SELECT * FROM writing_projects WHERE id = ? AND user_id = ?',
        (project_id, session['user_id'])
    ).fetchone()
    conn.close()
    
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('project.html', project=project, ai_available=StoryWeaverAI.is_ai_available())

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Support both JSON and form-encoded data
        data = request.get_json(silent=True) or {}
        username = data.get('username') or request.form.get('username')
        password = data.get('password') or request.form.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Please provide username and password'})
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password_hash = ?',
            (username, hash_password(password))
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'error': 'Invalid username or password'})
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User registration"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Support both JSON and form-encoded data
        data = request.get_json(silent=True) or {}
        username = data.get('username') or request.form.get('username')
        email = data.get('email') or request.form.get('email')
        password = data.get('password') or request.form.get('password')
        
        if not username or not email or not password:
            return jsonify({'success': False, 'error': 'Please fill in all fields'})
        
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, hash_password(password))
            )
            user_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            
            # Create creative profile
            conn.execute(
                'INSERT INTO creative_profiles (user_id) VALUES (?)',
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
            
        except sqlite3.IntegrityError:
            return jsonify({'success': False, 'error': 'Username or email already exists'})
        except Exception as e:
            return jsonify({'success': False, 'error': 'Error creating account'})
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))  # Redirect to index after logout

# API Routes
@app.route('/api/generate-idea', methods=['POST'])
def api_generate_idea():
    """Generate story idea API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    genre = data.get('genre', 'fantasy')
    
    idea = ai_service.generate_story_idea(genre)
    
    # Save generation to database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO ai_generations (user_id, generation_type, prompt, result) VALUES (?, ?, ?, ?)',
        (session['user_id'], 'story_idea', genre, idea)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'idea': idea})

@app.route('/api/generate-dialogue', methods=['POST'])
def api_generate_dialogue():
    """Generate dialogue API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    character_desc = data.get('character', 'mysterious stranger')
    context = data.get('context', 'tense confrontation')
    
    dialogue = ai_service.generate_dialogue(character_desc, context)
    
    # Save generation to database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO ai_generations (user_id, generation_type, prompt, result) VALUES (?, ?, ?, ?)',
        (session['user_id'], 'dialogue', f"{character_desc} - {context}", dialogue)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'dialogue': dialogue})

@app.route('/api/generate-world', methods=['POST'])
def api_generate_world():
    """Generate world-building API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    genre = data.get('genre', 'fantasy')
    theme = data.get('theme', 'exploration')
    
    world = ai_service.generate_world_building(genre, theme)
    
    # Save generation to database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO ai_generations (user_id, generation_type, prompt, result) VALUES (?, ?, ?, ?)',
        (session['user_id'], 'world_building', f"{genre} - {theme}", world)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'world': world})

@app.route('/api/generate-inspiration', methods=['POST'])
def api_generate_inspiration():
    """Generate inspiration API"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    prompt_type = data.get('type', 'prompt')
    
    inspiration = ai_service.generate_inspiration(prompt_type)
    
    # Save generation to database
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO ai_generations (user_id, generation_type, prompt, result) VALUES (?, ?, ?, ?)',
        (session['user_id'], 'inspiration', prompt_type, inspiration)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'inspiration': inspiration})

@app.route('/generate-with-gemini', methods=['POST'])
def generate_with_gemini():
    """Generate content using Gemini AI with custom prompts"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        prompt = request.form.get('prompt', '')
        
        if not prompt.strip():
            return jsonify({'error': 'Please provide a text prompt'}), 400
        
        suggestion = generate_with_gemini_ai(prompt)
        return jsonify({'suggestion': suggestion})
        
    except Exception as e:
        print(f"Gemini AI route error: {e}")
        return jsonify({'error': 'Unable to generate suggestions at the moment. Please try again.'}), 500

@app.route('/api/projects', methods=['POST'])
def api_create_project():
    """Create new writing project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    title = data.get('title', 'Untitled Project')
    genre = data.get('genre', 'General')
    
    conn = get_db_connection()
    cursor = conn.execute(
        'INSERT INTO writing_projects (user_id, title, genre, content, word_count) VALUES (?, ?, ?, ?, ?)',
        (session['user_id'], title, genre, '', 0)
    )
    project_id = cursor.lastrowid
    conn.commit()
    
    # Get the created project
    project = conn.execute(
        'SELECT * FROM writing_projects WHERE id = ?', (project_id,)
    ).fetchone()
    conn.close()
    
    return jsonify({
        'success': True, 
        'project': {
            'id': project['id'],
            'title': project['title'],
            'genre': project['genre'],
            'content': project['content'],
            'word_count': project['word_count']
        }
    })

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def api_update_project(project_id):
    """Update writing project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    word_count = calculate_word_count(data.get('content', ''))
    
    conn = get_db_connection()
    conn.execute(
        '''UPDATE writing_projects 
           SET title = ?, genre = ?, content = ?, word_count = ?, updated_at = CURRENT_TIMESTAMP 
           WHERE id = ? AND user_id = ?''',
        (data.get('title'), data.get('genre'), data.get('content'), word_count, project_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def api_delete_project(project_id):
    """Delete writing project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    conn.execute(
        'DELETE FROM writing_projects WHERE id = ? AND user_id = ?',
        (project_id, session['user_id'])
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def api_get_project(project_id):
    """Get specific project"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    project = conn.execute(
        'SELECT * FROM writing_projects WHERE id = ? AND user_id = ?',
        (project_id, session['user_id'])
    ).fetchone()
    conn.close()
    
    if project:
        return jsonify({
            'project': {
                'id': project['id'],
                'title': project['title'],
                'genre': project['genre'],
                'content': project['content'],
                'word_count': project['word_count']
            }
        })
    else:
        return jsonify({'error': 'Project not found'}), 404

@app.route('/api/projects', methods=['GET'])
def api_get_projects():
    """Get user's projects"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db_connection()
    projects = conn.execute(
        'SELECT * FROM writing_projects WHERE user_id = ? ORDER BY updated_at DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    projects_list = []
    for project in projects:
        projects_list.append({
            'id': project['id'],
            'title': project['title'],
            'genre': project['genre'],
            'content': project['content'],
            'word_count': project['word_count']
        })
    
    return jsonify({'projects': projects_list})

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("StoryWeaver AI starting on http://localhost:5000")
    print("First page: Index/Landing page")
    if GEMINI_API_KEY and GEMINI_MODEL:
        print("Gemini AI Integration: Active")
        print(f"Using model: {GEMINI_MODEL}")
    else:
        print("Gemini AI Integration: Not available - check API key")
        print("The application will run without AI features")
    
    app.run(debug=True, host='0.0.0.0', port=5000)