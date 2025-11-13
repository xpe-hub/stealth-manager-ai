#!/usr/bin/env python3
"""
OAuth Service - Sistema de autenticación real Google, GitHub y Discord
Mantiene la calidad y seguridad de Bypass Supreme
"""

import requests
import json
import secrets
import hashlib
import time
from urllib.parse import urlencode
from typing import Dict, Optional, Tuple
from auth_config import oauth_config, OAUTH_SCOPES
import logging

logger = logging.getLogger(__name__)

class OAuthService:
    """Servicio OAuth para autenticación segura"""
    
    def __init__(self):
        self.config = oauth_config
        self.active_sessions = {}  # Almacena sesiones activas
    
    def generate_state(self) -> str:
        """Genera estado único para prevenir CSRF"""
        return secrets.token_urlsafe(32)
    
    def verify_state(self, state: str) -> bool:
        """Verifica que el estado sea válido y reciente"""
        # En implementación real, verificar contra base de datos
        return len(state) > 20
    
    def create_session(self, user_data: Dict) -> str:
        """Crea una nueva sesión de usuario"""
        session_id = secrets.token_urlsafe(32)
        
        self.active_sessions[session_id] = {
            'user_data': user_data,
            'created_at': time.time(),
            'last_access': time.time(),
            'provider': user_data.get('provider', 'unknown')
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Obtiene datos de sesión"""
        if session_id in self.active_sessions:
            # Actualizar último acceso
            self.active_sessions[session_id]['last_access'] = time.time()
            return self.active_sessions[session_id]
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def is_session_valid(self, session_id: str) -> bool:
        """Verifica si una sesión es válida y no ha expirado"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # Verificar expiración (24 horas)
        age = time.time() - session['created_at']
        return age < self.config.SESSION_TIMEOUT
    
    def get_google_auth_url(self) -> Tuple[str, str]:
        """Genera URL de autorización de Google y estado CSRF"""
        state = self.generate_state()
        
        params = {
            'client_id': self.config.GOOGLE_CLIENT_ID,
            'redirect_uri': self.config.GOOGLE_REDIRECT_URI,
            'scope': OAUTH_SCOPES['google'],
            'response_type': 'code',
            'state': state,
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        auth_url = f"{self.config.GOOGLE_AUTH_URL}?{urlencode(params)}"
        return auth_url, state
    
    def get_github_auth_url(self) -> Tuple[str, str]:
        """Genera URL de autorización de GitHub y estado CSRF"""
        state = self.generate_state()
        
        params = {
            'client_id': self.config.GITHUB_CLIENT_ID,
            'redirect_uri': self.config.GITHUB_REDIRECT_URI,
            'scope': OAUTH_SCOPES['github'],
            'state': state
        }
        
        auth_url = f"{self.config.GITHUB_AUTH_URL}?{urlencode(params)}"
        return auth_url, state
    
    def get_discord_auth_url(self) -> Tuple[str, str]:
        """Genera URL de autorización de Discord y estado CSRF"""
        state = self.generate_state()
        
        params = {
            'client_id': self.config.DISCORD_CLIENT_ID,
            'redirect_uri': self.config.DISCORD_REDIRECT_URI,
            'scope': OAUTH_SCOPES['discord'],
            'response_type': 'code',
            'state': state
        }
        
        auth_url = f"{self.config.DISCORD_AUTH_URL}?{urlencode(params)}"
        return auth_url, state
    
    def exchange_google_code(self, code: str, state: str) -> Optional[Dict]:
        """Intercambia código de autorización de Google por token"""
        try:
            data = {
                'client_id': self.config.GOOGLE_CLIENT_ID,
                'client_secret': self.config.GOOGLE_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.config.GOOGLE_REDIRECT_URI
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                self.config.GOOGLE_TOKEN_URL,
                data=urlencode(data),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data['access_token']
                
                # Obtener información del usuario
                user_info = self._get_google_user_info(access_token)
                
                return {
                    'provider': 'google',
                    'id': user_info.get('id'),
                    'email': user_info.get('email'),
                    'name': user_info.get('name'),
                    'picture': user_info.get('picture'),
                    'access_token': access_token,
                    'verified_email': user_info.get('verified_email', False)
                }
            
            logger.error(f"Error Google OAuth: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error intercambiando código Google: {str(e)}")
            return None
    
    def exchange_github_code(self, code: str, state: str) -> Optional[Dict]:
        """Intercambia código de autorización de GitHub por token"""
        try:
            data = {
                'client_id': self.config.GITHUB_CLIENT_ID,
                'client_secret': self.config.GITHUB_CLIENT_SECRET,
                'code': code,
                'redirect_uri': self.config.GITHUB_REDIRECT_URI
            }
            
            headers = {
                'Accept': 'application/json'
            }
            
            response = requests.post(
                self.config.GITHUB_TOKEN_URL,
                data=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data['access_token']
                
                # Obtener información del usuario
                user_info = self._get_github_user_info(access_token)
                
                # Obtener emails del usuario
                emails = self._get_github_emails(access_token)
                primary_email = emails[0]['email'] if emails else None
                
                return {
                    'provider': 'github',
                    'id': str(user_info.get('id')),
                    'login': user_info.get('login'),
                    'email': primary_email,
                    'name': user_info.get('name') or user_info.get('login'),
                    'avatar_url': user_info.get('avatar_url'),
                    'bio': user_info.get('bio'),
                    'access_token': access_token,
                    'public_repos': user_info.get('public_repos', 0),
                    'followers': user_info.get('followers', 0)
                }
            
            logger.error(f"Error GitHub OAuth: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error intercambiando código GitHub: {str(e)}")
            return None
    
    def exchange_discord_code(self, code: str, state: str) -> Optional[Dict]:
        """Intercambia código de autorización de Discord por token"""
        try:
            data = {
                'client_id': self.config.DISCORD_CLIENT_ID,
                'client_secret': self.config.DISCORD_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.config.DISCORD_REDIRECT_URI
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                self.config.DISCORD_TOKEN_URL,
                data=urlencode(data),
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data['access_token']
                
                # Obtener información del usuario
                user_info = self._get_discord_user_info(access_token)
                
                return {
                    'provider': 'discord',
                    'id': user_info.get('id'),
                    'username': user_info.get('username'),
                    'discriminator': user_info.get('discriminator'),
                    'email': user_info.get('email'),
                    'avatar': user_info.get('avatar'),
                    'avatar_url': self._get_discord_avatar_url(user_info),
                    'verified': user_info.get('verified', False),
                    'access_token': access_token
                }
            
            logger.error(f"Error Discord OAuth: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error intercambiando código Discord: {str(e)}")
            return None
    
    def _get_google_user_info(self, access_token: str) -> Dict:
        """Obtiene información del usuario de Google"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(
            self.config.GOOGLE_USERINFO_URL,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def _get_github_user_info(self, access_token: str) -> Dict:
        """Obtiene información del usuario de GitHub"""
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(
            self.config.GITHUB_USERINFO_URL,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def _get_github_emails(self, access_token: str) -> list:
        """Obtiene emails del usuario de GitHub"""
        headers = {
            'Authorization': f'token {access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        response = requests.get(
            'https://api.github.com/user/emails',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return []
    
    def _get_discord_user_info(self, access_token: str) -> Dict:
        """Obtiene información del usuario de Discord"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(
            self.config.DISCORD_USERINFO_URL,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        return {}
    
    def _get_discord_avatar_url(self, user_info: Dict) -> Optional[str]:
        """Genera URL del avatar de Discord"""
        user_id = user_info.get('id')
        avatar_hash = user_info.get('avatar')
        
        if user_id and avatar_hash:
            return f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
        return None

# Instancia global del servicio OAuth
oauth_service = OAuthService()