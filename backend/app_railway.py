#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StealthHub: plataforma profesional de IA con Google OAuth
"""
import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import hashlib
from google.oauth2 import id_token
from google.auth.transport import requests
import requests as http_requests
import jwt
from functools import wraps

# Configuración de registro
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'xpe-nettt-bypass-supreme-secret-key-2025')
CORS(app, supports_credentials=True)

# Configuración Google OAuth - SOLO desde variables de entorno
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# Verificar que las credenciales están configuradas
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
    logger.error("¡Credenciales OAuth de Google no configuradas!")
    logger.error("Por favor, configure las variables de entorno GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET")

# Base de datos de usuarios (SQLite)
DATABASE = 'stealthhub_users.db'

def init_db():
    """Inicializa la base de datos de usuarios"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    # Crear tabla de usuarios
    cursor.execute('''
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

# Decorador para rutas protegidas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Sistema de IA Contextual
class StealthHubAI:
    def __init__(self):
        self.categories = {
            'reverse_engineering': {
                'name': 'Ingeniería inversa',
                'description': 'Análisis y descomposición de software',
                'level_responses': {
                    'beginner': 'Como principiante en ingeniería inversa, te recomiendo empezar con herramientas básicas como IDA Free o x64dbg. ¿En qué sistema específico necesitas ayuda?',
                    'intermediate': 'Como desarrollador intermedio, puedes explorar técnicas como API Hooking y parches de memoria. ¿Qué tipo de binario estás analizando?',
                    'expert': 'Como experto, podemos profundizar en técnicas avanzadas como detección de empaquetadores, bypass anti-depuración y análisis de malware. ¿Necesitas ayuda con bypass de protecciones?'
                }
            },
            'malware_analysis': {
                'name': 'Análisis de malware',
                'description': 'Análisis seguro de software malicioso',
                'level_responses': {
                    'beginner': 'Para análisis de malware seguro, siempre usa VM aisladas. ¿Qué tipo de muestra tienes disponible?',
                    'intermediate': 'Como analista intermedio, puedes usar técnicas como sandboxing y análisis de comportamiento. ¿Necesitas ayuda con análisis estático o dinámico?',
                    'expert': 'Como experto en malware, podemos trabajar con técnicas avanzadas como memoria forense y análisis de redes. ¿Es una muestra cifrada?'
                }
            },
            'evasion_techniques': {
                'name': 'Técnicas de evasión',
                'description': 'Técnicas de bypass y evasión',
                'level_responses': {
                    'beginner': 'Para bypass básico, considera técnicas como Process Hollowing e inyección de DLL. ¿Qué tipo de protección enfrentas?',
                    'intermediate': 'Como desarrollador intermedio, puedes explorar técnicas como API unhooking y EDR evasion. ¿Necesitas bypass de AV o EDR?',
                    'expert': 'Como experto, podemos trabajar con técnicas como inyección de procesos vía PID principal, bypass NtCreateProcessEx. ¿Qué evasión necesitas?'
                }
            },
            'cryptography': {
                'name': 'Criptografía',
                'description': 'Análisis criptográfico e implementación segura',
                'level_responses': {
                    'beginner': 'Para análisis criptográfico básico, enfócate en algoritmos comunes como XOR, AES básico. ¿Qué tipo de cifrado necesitas analizar?',
                    'intermediate': 'Como desarrollador intermedio, puedes explorar RSA, criptografía de curva elíptica e implementaciones personalizadas. ¿Tienes una clave específica?',
                    'expert': 'Como experto, podemos trabajar con criptoanálisis avanzado, ataques de canal lateral y algoritmos resistentes a lo cuántico. ¿Es una implementación personalizada?'
                }
            },
            'network_security': {
                'name': 'Seguridad de red',
                'description': 'Seguridad de redes y análisis de tráfico',
                'level_responses': {
                    'beginner': 'Para análisis de red básico, usa Wireshark y analiza protocolos comunes. ¿Qué tipo de tráfico necesitas revisar?',
                    'intermediate': 'Como analista intermedio, puedes trabajar con packet crafting y network evasion. ¿Necesitas análisis de redes de malware?',
                    'expert': 'Como experto, podemos explorar amenazas persistentes avanzadas, exfiltración de DNS y movimiento lateral de red. ¿Qué protocolo te interesa?'
                }
            },
            'mobile_security': {
                'name': 'Seguridad móvil',
                'description': 'Seguridad en dispositivos móviles',
                'level_responses': {
                    'beginner': 'Para móvil básico, aprende sobre análisis APK y análisis estático/dinámico. ¿Qué OS estás analizando?',
                    'intermediate': 'Como desarrollador intermedio, puedes explorar jailbreak/rooting y bypass de certificate pinning. ¿Es iOS o Android?',
                    'expert': 'Como experto, podemos trabajar con iOS kernel exploitation, evitando los modelos de seguridad de Android. ¿Necesitas análisis de privacidad?'
                }
            },
            'web_security': {
                'name': 'Seguridad Web',
                'description': 'Seguridad en aplicaciones web',
                'level_responses': {
                    'beginner': 'Para web básica, enfócate en inyección SQL, XSS y CSRF. ¿Qué tecnología web usas?',
                    'intermediate': 'Como desarrollador intermedio, puedes explorar CSP security, SSRF y API security. ¿Es una SPA o aplicación tradicional?',
                    'expert': 'Como experto, podemos trabajar con advanced deserialization attacks, prototype pollution y cloud security. ¿Qué framework usas?'
                }
            },
            'system_security': {
                'name': 'Seguridad del sistema',
                'description': 'Seguridad a nivel de sistema operativo',
                'level_responses': {
                    'beginner': 'Para sistema básico, aprende sobre permisos de usuario, hardening de servicios y aislamiento de procesos. ¿Qué SO usas?',
                    'intermediate': 'Como desarrollador intermedio, puedes explorar kernel debugging y driver security. ¿Necesitas ayuda con privilege escalation?',
                    'expert': 'Como experto, podemos trabajar con kernel exploitation, hypervisor attacks y hardware security. ¿Qué arquitectura objetivo?'
                }
            }
        }
        self.badges = {
            'first_login': 'Bienvenido Explorador',
            'category_explorer': 'Explorador de categorías',
            'security_newbie': 'Principiante en seguridad',
            'code_analyzer': 'Analizador de código',
            'malware_hunter': 'Cazador de malware',
            'bypass_master': 'Bypass Master',
            'crypto_expert': 'Experto en criptografía',
            'network_guardian': 'Guardián de la red',
            'mobile_defender': 'Defensor móvil',
            'web_warrior': 'Guerrero web',
            'system_sentinel': 'Centinela del sistema',
            'security_researcher': 'Investigador de seguridad',
            'community_mentor': 'Mentor comunitario',
            'security_innovator': 'Innovador en seguridad'
        }
    
    def get_contextual_response(self, category, level, user_name):
        """Genera respuesta contextual basada en categoría y nivel"""
        if category in self.categories and level in self.categories[category]['level_responses']:
            base_response = self.categories[category]['level_responses'][level]
            return f"🔒 **{user_name}**, {base_response}\n\n🎯 **Categoría seleccionada:** {self.categories[category]['name']}\n🎯 **Tu nivel:** {level.title()}\n\n¿En qué aspecto específico te gustaría profundizar?"
        return "¡Hola! ¿En qué área de la seguridad informática necesitas ayuda hoy? 🚀"

ai_system = StealthHubAI()

@app.route('/')
def index():
    """Página principal"""
    user = None
    if 'user_id' in session:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            user = {
                'id': user_data[0],
                'email': user_data[1],
                'name': user_data[2],
                'profile_picture': user_data[5] or '',
                'bio': user_data[6] or '',
                'experience_level': user_data[7] or 'beginner',
                'badges': json.loads(user_data[9]) if user_data[9] else []
            }
    return render_template('index.html', user=user, categories=ai_system.categories, badges=ai_system.badges)

@app.route('/auth/google')
def google_login():
    """Inicia el flujo de autenticación con Google"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({'error': 'Google OAuth no está configurado'}), 500
    import urllib.parse
    google_auth_url = "https://accounts.google.com/o/oauth2/auth"
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': f"{request.url_root}auth/google/callback",
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    auth_url = f"{google_auth_url}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/auth/google/callback')
def google_callback():
    """Callback de Google OAuth"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return jsonify({'error': 'Google OAuth no está configurado'}), 500
    try:
        code = request.args.get('code')
        # Intercambiar código por token
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            'code': code,
            'client_id': GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri': f"{request.url_root}auth/google/callback",
            'grant_type': 'authorization_code'
        }
        token_response = http_requests.post(token_url, data=data)
        token_data = token_response.json()
        if 'error' in token_data:
            logger.error(f"Error al obtener los tokens: {token_data}")
            return redirect(url_for('index'))
        
        # Obtener información del usuario
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f"Bearer {token_data['access_token']}"}
        userinfo_response = http_requests.get(userinfo_url, headers=headers)
        user_info = userinfo_response.json()
        
        # Buscar o crear usuario en la base de datos
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Buscar usuario por ID de Google
        cursor.execute("SELECT id FROM users WHERE google_id = ?", (user_info['id'],))
        existing_user = cursor.fetchone()
        if existing_user:
            # Actualizar último login
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE google_id = ?", (user_info['id'],))
            user_id = existing_user[0]
        else:
            # Crear nuevo usuario
            cursor.execute('''
                INSERT INTO users (email, name, google_id, google_auth, last_login)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_info['email'], user_info['name'], user_info['id'], True))
            user_id = cursor.lastrowid
            # Asignar insignia de bienvenida
            cursor.execute("UPDATE users SET badges = ? WHERE id = ?", (json.dumps(['first_login']), user_id))
        conn.commit()
        conn.close()
        
        # Configurar sesión
        session['user_id'] = user_id
        session['user_name'] = user_info['name']
        session['user_email'] = user_info['email']
        logger.info(f"Inicio de sesión de Google OAuth exitoso para: {user_info['email']}")
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Error de OAuth de Google: {e}")
        return redirect(url_for('index'))

@app.route('/auth/register', methods=['POST'])
def register():
    """Registro tradicional de usuario"""
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        if not all([name, email, password]):
            return jsonify({'success': False, 'error': 'Todos los campos son requeridos'})
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'error': 'El email ya está registrado'})
        # Crear nuevo usuario
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (name, email, password_hash, google_auth, last_login)
            VALUES (?, ?, ?, FALSE, CURRENT_TIMESTAMP)
        ''', (name, email, password_hash))
        user_id = cursor.lastrowid
        # Asignar insignia de bienvenida
        cursor.execute("UPDATE users SET badges = ? WHERE id = ?", (json.dumps(['first_login']), user_id))
        conn.commit()
        conn.close()
        # Configurar sesión
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_email'] = email
        return jsonify({'success': True, 'message': 'Registro exitoso'})
    except Exception as e:
        logger.error(f"Error de registro: {e}")
        return jsonify({'success': False, 'error': 'Error en el registro'})

@app.route('/auth/login', methods=['POST'])
def login():
    """Inicio de sesión tradicional"""
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        if not all([email, password]):
            return jsonify({'success': False, 'error': 'Email y contraseña requerida'})
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE email = ? AND google_auth = FALSE", (email,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data and check_password_hash(user_data[1], password):
            session['user_id'] = user_data[0]
            session['user_email'] = email
            # Actualizar último login
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_data[0],))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Inicio de sesión exitoso'})
        else:
            return jsonify({'success': False, 'error': 'Credenciales inválidas'})
    except Exception as e:
        logger.error(f"Error de inicio de sesión: {e}")
        return jsonify({'success': False, 'error': 'Error al iniciar sesión'})

@app.route('/auth/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard del usuario"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user_data = cursor.fetchone()
    conn.close()
    if not user_data:
        return redirect(url_for('index'))
    user = {
        'id': user_data[0],
        'email': user_data[1],
        'name': user_data[2],
        'profile_picture': user_data[5] or '',
        'bio': user_data[6] or '',
        'experience_level': user_data[7] or 'beginner',
        'categories': json.loads(user_data[8]) if user_data[8] else [],
        'badges': json.loads(user_data[9]) if user_data[9] else []
    }
    return render_template('dashboard.html', user=user, categories=ai_system.categories, badges=ai_system.badges)

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """API de chat con IA contextual"""
    try:
        data = request.get_json()
        category = data.get('category', 'reverse_engineering')
        message = data.get('message', '')
        # Obtener nivel del usuario
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name, experience_level FROM users WHERE id = ?", (session['user_id'],))
        user_data = cursor.fetchone()
        conn.close()
        if user_data:
            user_name, level = user_data
            response = ai_system.get_contextual_response(category, level, user_name)
            # Actualizar estadísticas del usuario
            update_user_stats(category)
            return jsonify({
                'success': True,
                'response': response,
                'category': category,
                'level': level
            })
        else:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'})
    except Exception as e:
        logger.error(f"Error de la API de chat: {e}")
        return jsonify({'success': False, 'error': 'Error en el chat'})

def update_user_stats(category):
    """Actualiza estadísticas del usuario basadas en interacciones"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Obtener categorías actuales del usuario
        cursor.execute("SELECT categories FROM users WHERE id = ?", (session['user_id'],))
        categories_data = cursor.fetchone()
        categories = json.loads(categories_data[0]) if categories_data and categories_data[0] else []
        # Agregar nueva categoría si no existe
        if category not in categories:
            categories.append(category)
        cursor.execute("UPDATE users SET categories = ? WHERE id = ?", (json.dumps(categories), session['user_id']))
        # Asignar insignia si el usuario explora múltiples categorías
        if len(categories) >= 3:
            cursor.execute("SELECT badges FROM users WHERE id = ?", (session['user_id'],))
            badges_data = cursor.fetchone()
            badges = json.loads(badges_data[0]) if badges_data and badges_data[0] else []
            if 'category_explorer' not in badges:
                badges.append('category_explorer')
            cursor.execute("UPDATE users SET badges = ? WHERE id = ?", (json.dumps(badges), session['user_id']))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error al actualizar las estadísticas: {e}")

@app.route('/api/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Actualizar perfil de usuario"""
    try:
        data = request.get_json()
        bio = data.get('bio', '')
        experience_level = data.get('experience_level', 'beginner')
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        # Asignar insignia basado en nivel de experiencia
        cursor.execute("SELECT badges FROM users WHERE id = ?", (session['user_id'],))
        badges_data = cursor.fetchone()
        badges = json.loads(badges_data[0]) if badges_data and badges_data[0] else []
        level_badges = {
            'beginner': 'security_newbie',
            'intermediate': 'code_analyzer',
            'expert': 'security_researcher'
        }
        if experience_level in level_badges and level_badges[experience_level] not in badges:
            badges.append(level_badges[experience_level])
        cursor.execute('''
            UPDATE users
            SET bio = ?, experience_level = ?, badges = ?
            WHERE id = ?
        ''', (bio, experience_level, json.dumps(badges), session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Perfil actualizado'})
    except Exception as e:
        logger.error(f"Error al actualizar el perfil: {e}")
        return jsonify({'success': False, 'error': 'Error actualizando perfil'})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "StealthHub AI",
        "version": "v3.0"
    })

@app.route('/api/categories')
def get_categories():
    """API endpoint para obtener categorías"""
    return jsonify({"categories": list(ai_system.categories.keys())})

if __name__ == '__main__':
    # Inicializar base de datos
    init_db()
    # Configuración para desarrollo
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    logger.info(f"Iniciando StealthHub en puerto {port}")
    if GOOGLE_CLIENT_ID:
        logger.info("Google OAuth configurado correctamente")
    else:
        logger.warning("Google OAuth NO configurado - falta GOOGLE_CLIENT_ID")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
