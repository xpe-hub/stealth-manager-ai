#!/usr/bin/env python3
"""
Configuración de OAuth para Google y GitHub
Manteniendo la calidad Bypass Supreme
"""

import os
from dataclasses import dataclass

@dataclass
class OAuthConfig:
    """Configuración de OAuth"""
    
    # GOOGLE OAUTH
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI: str = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:9000/auth/google/callback')
    
    # GITHUB OAUTH  
    GITHUB_CLIENT_ID: str = os.getenv('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET: str = os.getenv('GITHUB_CLIENT_SECRET', '')
    GITHUB_REDIRECT_URI: str = os.getenv('GITHUB_REDIRECT_URI', 'http://localhost:9000/auth/github/callback')
    
    # DISCORD OAUTH
    DISCORD_CLIENT_ID: str = os.getenv('DISCORD_CLIENT_ID', '')
    DISCORD_CLIENT_SECRET: str = os.getenv('DISCORD_CLIENT_SECRET', '')
    DISCORD_REDIRECT_URI: str = os.getenv('DISCORD_REDIRECT_URI', 'http://localhost:9000/auth/discord/callback')
    
    # SESSION SECURITY
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'xpe-nettt-bypass-supreme-secret-key-2025')
    SESSION_TIMEOUT: int = 86400  # 24 horas
    
    # OAUTH ENDPOINTS
    GOOGLE_AUTH_URL: str = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_TOKEN_URL: str = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL: str = 'https://www.googleapis.com/oauth2/v2/userinfo'
    
    GITHUB_AUTH_URL: str = 'https://github.com/login/oauth/authorize'
    GITHUB_TOKEN_URL: str = 'https://github.com/login/oauth/access_token'
    GITHUB_USERINFO_URL: str = 'https://api.github.com/user'
    
    DISCORD_AUTH_URL: str = 'https://discord.com/api/oauth2/authorize'
    DISCORD_TOKEN_URL: str = 'https://discord.com/api/oauth2/token'
    DISCORD_USERINFO_URL: str = 'https://discord.com/api/users/@me'

# Instancia global de configuración
oauth_config = OAuthConfig()

# Validación de configuración
def validate_oauth_config():
    """Valida que la configuración OAuth esté completa"""
    issues = []
    
    if not oauth_config.GOOGLE_CLIENT_ID:
        issues.append("⚠️  GOOGLE_CLIENT_ID no configurado")
    if not oauth_config.GOOGLE_CLIENT_SECRET:
        issues.append("⚠️  GOOGLE_CLIENT_SECRET no configurado")
    
    if not oauth_config.GITHUB_CLIENT_ID:
        issues.append("⚠️  GITHUB_CLIENT_ID no configurado")
    if not oauth_config.GITHUB_CLIENT_SECRET:
        issues.append("⚠️  GITHUB_CLIENT_SECRET no configurado")
    
    if issues:
        print("\n" + "="*60)
        print("🔥 CONFIGURACIÓN OAUTH - BYPASS SUPREME")
        print("="*60)
        for issue in issues:
            print(issue)
        print("\n📋 Para configurar OAuth:")
        print("1. Google Cloud Console → OAuth 2.0 → Crear credenciales")
        print("2. GitHub Settings → Developer settings → OAuth Apps")
        print("3. Discord Developer Portal → OAuth2 → New Application")
        print("4. Configurar variables de entorno:")
        print("   export GOOGLE_CLIENT_ID='tu_google_client_id'")
        print("   export GOOGLE_CLIENT_SECRET='tu_google_client_secret'")
        print("   export GITHUB_CLIENT_ID='tu_github_client_id'")
        print("   export GITHUB_CLIENT_SECRET='tu_github_client_secret'")
        print("   export SECRET_KEY='tu_clave_secreta_segura'")
        print("="*60)
        return False
    
    return True

# SCOPES necesarios
OAUTH_SCOPES = {
    'google': 'openid email profile',
    'github': 'read:user user:email',
    'discord': 'identify email'
}