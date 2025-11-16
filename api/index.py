from flask import Flask, request, jsonify, session, redirect, url_for, render_template_string
from flask_cors import CORS
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from google_auth_oauthlib.flow import Flow
import json
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Enable CORS
CORS(app, supports_credentials=True)

# Database setup
def get_db():
    conn = sqlite3.connect('stealthhub_users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT,
            google_id TEXT UNIQUE,
            profile_picture TEXT,
            bio TEXT DEFAULT '',
            experience_level TEXT DEFAULT 'beginner',
            categories TEXT DEFAULT '[]',
            badges TEXT DEFAULT '[]',
            google_auth BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# AI Categories and System
AI_CATEGORIES = {
    "reverse_engineering": {"name": "Ingenier铆a inversa", "description": "An谩lisis y descomposici贸n de software", "levels": ["beginner", "intermediate", "expert"]},
    "malware_analysis": {"name": "An谩lisis de malware", "description": "An谩lisis seguro de software malicioso", "levels": ["beginner", "intermediate", "expert"]},
    "evasion_techniques": {"name": "T茅cnicas de evasi贸n", "description": "T茅cnicas de bypass y evasi贸n", "levels": ["beginner", "intermediate", "expert"]},
    "cryptography": {"name": "Criptograf铆a", "description": "An谩lisis criptogr谩fico e implementaci贸n segura", "levels": ["beginner", "intermediate", "expert"]},
    "network_security": {"name": "Seguridad de red", "description": "Seguridad de redes y an谩lisis de tr谩fico", "levels": ["beginner", "intermediate", "expert"]},
    "mobile_security": {"name": "Seguridad m贸vil", "description": "Seguridad en dispositivos m贸viles", "levels": ["beginner", "intermediate", "expert"]},
    "web_security": {"name": "Seguridad Web", "description": "Seguridad en aplicaciones web", "levels": ["beginner", "intermediate", "expert"]},
    "system_security": {"name": "Seguridad del sistema", "description": "Seguridad a nivel de sistema operativo", "levels": ["beginner", "intermediate", "expert"]}
}

class StealthHubAI:
    def __init__(self):
        self.context_system = """
        You are StealthHub, an advanced AI assistant specialized in cybersecurity, DLL injection, memory hacking, reverse engineering, and related security technologies. You assist developers, researchers, and professionals in:
        
        1. Development & Coding:
        - DLL injection techniques
        - Memory manipulation
        - Reverse engineering tools
        - Security programming
        - Malware analysis techniques
        
        2. Security & Bypasses:
        - System bypass methods
        - Game bypasses
        - Application modifications
        - Security testing
        - Penetration testing
        
        3. Analysis & Research:
        - Binary analysis
        - System forensics
        - Network analysis
        - Vulnerability research
        - Security auditing
        
        Provide detailed, technical responses suitable for security professionals and researchers.
        """

def handle_api_request(method):
    """Wrapper to handle API requests for Vercel"""
    init_db()
    
    if method == 'GET':
        return handle_get_request()
    elif method == 'POST':
        return handle_post_request()
    elif method == 'DELETE':
        return handle_delete_request()

def handle_get_request():
    """Handle GET requests"""
    path = request.path
    
    if path == '/api/health':
        return jsonify({
            "status": "ok",
            "message": "StealthHub AI Platform v3.0",
            "categories": list(AI_CATEGORIES.keys()),
            "timestamp": datetime.now().isoformat()
        })
    
    elif path == '/api/categories':
        return jsonify({
            "categories": AI_CATEGORIES,
            "total": len(AI_CATEGORIES)
        })
    
    elif path == '/api/profile':
        # Get user profile (requires authentication)
        email = session.get('user_email')
        if not email:
            return jsonify({"error": "Not authenticated"}), 401
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user:
            user_dict = dict(user)
            user_dict.pop('password_hash', None)  # Remove sensitive data
            return jsonify(user_dict)
        else:
            return jsonify({"error": "User not found"}), 404

def handle_post_request():
    """Handle POST requests"""
    path = request.path
    data = request.get_json()
    
    if path == '/api/chat':
        return handle_chat_request(data)
    elif path == '/api/update_profile':
        return handle_update_profile_request(data)
    elif path == '/api/register':
        return handle_register_request(data)
    elif path == '/api/login':
        return handle_login_request(data)

def handle_chat_request(data):
    """Handle AI chat requests"""
    message = data.get('message', '')
    category = data.get('category', 'reverse_engineering')
    
    # Check authentication
    email = session.get('user_email')
    if not email:
        return jsonify({"error": "Authentication required"}), 401
    
    # Get user context
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        # Update user categories and give badge
        categories = eval(user['categories']) if user['categories'] != '[]' else []
        if category not in categories:
            categories.append(category)
            conn.execute('UPDATE users SET categories = ? WHERE email = ?', (str(categories), email))
            
            # Award category explorer badge
            badges = eval(user['badges']) if user['badges'] != '[]' else []
            if 'category_explorer' not in badges:
                badges.append('category_explorer')
                conn.execute('UPDATE users SET badges = ? WHERE email = ?', (str(badges), email))
        
        conn.commit()
        user_dict = dict(user)
    else:
        return jsonify({"error": "User not found"}), 404
    
    conn.close()
    
    # Generate AI response (simplified for demo)
    ai = StealthHubAI()
    category_info = AI_CATEGORIES.get(category, AI_CATEGORIES['reverse_engineering'])
    
    response = f"""
    **StealthHub AI - {category_info['name']}**
    
    Regarding your request about {message}, here are some insights:
    
    - This is a specialized {category_info['description']}
    - For {user_dict.get('experience_level', 'beginner')} level professionals
    - Key considerations include security, ethics, and legal compliance
    - Recommended tools and techniques vary by context
    
    Would you like more specific information about any particular aspect?
    """
    
    return jsonify({
        "response": response.strip(),
        "category": category,
        "user_level": user_dict.get('experience_level', 'beginner')
    })

def handle_update_profile_request(data):
    """Handle profile updates"""
    email = session.get('user_email')
    if not email:
        return jsonify({"error": "Authentication required"}), 401
    
    bio = data.get('bio', '')
    experience_level = data.get('experience_level', 'beginner')
    
    conn = get_db()
    conn.execute('UPDATE users SET bio = ?, experience_level = ? WHERE email = ?', 
                (bio, experience_level, email))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Profile updated successfully"})

def handle_register_request(data):
    """Handle user registration"""
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not all([email, password, name]):
        return jsonify({"error": "Missing required fields"}), 400
    
    password_hash = generate_password_hash(password)
    
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)', 
                    (email, password_hash, name))
        conn.commit()
        
        # Set session
        session['user_email'] = email
        
        # Award first login badge
        conn.execute('UPDATE users SET badges = ? WHERE email = ?', 
                    ('["first_login"]', email))
        conn.commit()
        
        return jsonify({"message": "Registration successful", "user": {"email": email, "name": name}})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400
    finally:
        conn.close()

def handle_login_request(data):
    """Handle user login"""
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({"error": "Missing required fields"}), 400
    
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], password):
        # Set session
        session['user_email'] = email
        
        # Update last login
        conn = get_db()
        conn.execute('UPDATE users SET last_login = ? WHERE email = ?', 
                    (datetime.now(), email))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Login successful", "user": {"email": email, "name": user['name']}})
    else:
        return jsonify({"error": "Invalid credentials"}), 401

def handle_delete_request():
    """Handle DELETE requests"""
    if request.path == '/api/logout':
        session.clear()
        return jsonify({"message": "Logout successful"})

# Root endpoint for frontend
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>StealthHub Professional AI Platform</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; min-height: 100vh; }
            .header { background: rgba(30, 41, 59, 0.95); backdrop-filter: blur(10px); border-bottom: 1px solid #334155; padding: 1rem 0; position: sticky; top: 0; z-index: 100; }
            .nav { max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center; }
            .logo { font-size: 1.5rem; font-weight: bold; color: #60a5fa; display: flex; align-items: center; gap: 0.5rem; }
            .nav-links { display: flex; gap: 2rem; }
            .nav-links a { color: #cbd5e1; text-decoration: none; transition: color 0.3s; }
            .nav-links a:hover { color: #60a5fa; }
            .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
            .hero { text-align: center; padding: 4rem 0; }
            .hero h1 { font-size: 3rem; margin-bottom: 1rem; background: linear-gradient(45deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .hero p { font-size: 1.25rem; color: #94a3b8; margin-bottom: 2rem; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 2rem; margin: 3rem 0; }
            .stat-card { background: rgba(30, 41, 59, 0.5); padding: 2rem; border-radius: 12px; border: 1px solid #334155; text-align: center; }
            .stat-number { font-size: 2.5rem; font-weight: bold; color: #60a5fa; }
            .stat-label { color: #94a3b8; margin-top: 0.5rem; }
            .categories { margin: 4rem 0; }
            .category-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem; }
            .category-card { background: rgba(30, 41, 59, 0.5); padding: 2rem; border-radius: 12px; border: 1px solid #334155; transition: transform 0.3s, border-color 0.3s; }
            .category-card:hover { transform: translateY(-5px); border-color: #60a5fa; }
            .category-title { color: #60a5fa; font-size: 1.25rem; margin-bottom: 1rem; }
            .category-desc { color: #94a3b8; margin-bottom: 1.5rem; }
            .category-levels { display: flex; gap: 0.5rem; }
            .level { padding: 0.25rem 0.75rem; background: rgba(96, 165, 250, 0.2); border-radius: 20px; font-size: 0.875rem; color: #60a5fa; }
            .footer { background: rgba(30, 41, 59, 0.5); border-top: 1px solid #334155; padding: 2rem 0; text-align: center; color: #64748b; }
            @media (max-width: 768px) { .nav { flex-direction: column; gap: 1rem; } .nav-links { flex-wrap: wrap; justify-content: center; } .hero h1 { font-size: 2rem; } }
        </style>
    </head>
    <body>
        <header class="header">
            <nav class="nav">
                <div class="logo">馃洝锔� StealthHub</div>
                <div class="nav-links">
                    <a href="#dashboard">Dashboard</a>
                    <a href="#categories">Categor铆as</a>
                    <a href="#analytics">Analytics</a>
                    <a href="#settings">Configuraci贸n</a>
                </div>
            </nav>
        </header>

        <main class="container">
            <section class="hero">
                <h1>StealthHub Professional AI Platform</h1>
                <p>Plataforma profesional de IA avanzada para desarrolladores, investigadores y profesionales de la seguridad inform谩tica</p>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">25+</div>
                        <div class="stat-label">Asistente General</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">42+</div>
                        <div class="stat-label">Desarrollo & Coding</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">18+</div>
                        <div class="stat-label">Security & Bypasses</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">31+</div>
                        <div class="stat-label">An谩lisis & Investigaci贸n</div>
                    </div>
                </div>
            </section>

            <section class="categories">
                <h2 style="text-align: center; margin-bottom: 2rem;">Categor铆as Principales</h2>
                <div class="category-grid">
                    <div class="category-card">
                        <div class="category-title">馃敡 Desarrollo & Coding</div>
                        <div class="category-desc">DLL Injection, Memory Hacking, Reverse Engineering, desarrollo de herramientas de seguridad</div>
                        <div class="category-levels">
                            <span class="level">Beginner</span>
                            <span class="level">Intermediate</span>
                            <span class="level">Expert</span>
                        </div>
                    </div>
                    <div class="category-card">
                        <div class="category-title">馃攼 Security & Bypasses</div>
                        <div class="category-desc">Vulnerabilidades, bypasses, t茅cnicas de evasi贸n, pruebas de penetraci贸n</div>
                        <div class="category-levels">
                            <span class="level">Beginner</span>
                            <span class="level">Intermediate</span>
                            <span class="level">Expert</span>
                        </div>
                    </div>
                    <div class="category-card">
                        <div class="category-title">馃攳 An谩lisis & Investigaci贸n</div>
                        <div class="category-desc">An谩lisis de datos profundo, investigaci贸n de sistemas, forense digital</div>
                        <div class="category-levels">
                            <span class="level">Beginner</span>
                            <span class="level">Intermediate</span>
                            <span class="level">Expert</span>
                        </div>
                    </div>
                    <div class="category-card">
                        <div class="category-title">馃帹 Creative & Content</div>
                        <div class="category-desc">Generaci贸n de contenido, documentaci贸n t茅cnica, soluciones innovadoras</div>
                        <div class="category-levels">
                            <span class="level">Beginner</span>
                            <span class="level">Intermediate</span>
                            <span class="level">Expert</span>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <footer class="footer">
            <p>&copy; 2025 StealthHub Professional AI Platform. Desarrollado para la comunidad de seguridad inform谩tica.</p>
        </footer>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "message": "StealthHub AI Platform v3.0", 
        "timestamp": datetime.now().isoformat(),
        "environment": "vercel"
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

# Export the Flask app for Vercel
app = app
