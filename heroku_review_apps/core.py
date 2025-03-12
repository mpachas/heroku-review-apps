import os
import sys
import json
import subprocess
import configparser
from pathlib import Path

import requests
import heroku3
from cloudflare import Cloudflare

class HerokuReviewAppCreator:
    def __init__(self, config_path=None):
        self.config_path = config_path or Path.home() / '.heroku-review-apps.ini'
        self.config = self._load_config()
        self.heroku_api_key = self.config.get('heroku', 'api_key', fallback=os.environ.get('HEROKU_API_KEY'))
        self.heroku_client = None
        self.cf_api_key = self.config.get('cloudflare', 'api_key', fallback=os.environ.get('CLOUDFLARE_API_KEY'))
        self.cf_email = self.config.get('cloudflare', 'email', fallback=os.environ.get('CLOUDFLARE_EMAIL'))
        self.cf_zone_id = self.config.get('cloudflare', 'zone_id', fallback=os.environ.get('CLOUDFLARE_ZONE_ID'))
        self.cf_domain = self.config.get('cloudflare', 'domain', fallback=None)
        self.pipeline_id = self.config.get('heroku', 'pipeline_id', fallback=None)
        self.addons = self.config.get('heroku', 'addons', fallback='').split(',')
        self.buildpacks = self.config.get('heroku', 'buildpacks', fallback='').split(',')
        self.env_vars = self._parse_env_vars()
        
    def _load_config(self):
        config = configparser.ConfigParser()
        if self.config_path.exists():
            config.read(self.config_path)
        return config

    def _parse_env_vars(self):
        if not self.config.has_section('env_vars'):
            return {}
        return dict(self.config['env_vars'])

    def _save_config(self):
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def setup(self):
        """Guía interactiva para configurar el script."""
        if not self.config.has_section('heroku'):
            self.config.add_section('heroku')
        if not self.config.has_section('cloudflare'):
            self.config.add_section('cloudflare')
        if not self.config.has_section('env_vars'):
            self.config.add_section('env_vars')

        # Configuración de Heroku
        self.heroku_api_key = input(f"Heroku API Key [{self.heroku_api_key or ''}]: ") or self.heroku_api_key
        self.config.set('heroku', 'api_key', self.heroku_api_key)
        
        self.pipeline_id = input(f"Heroku Pipeline ID [{self.pipeline_id or ''}]: ") or self.pipeline_id
        self.config.set('heroku', 'pipeline_id', self.pipeline_id)
        
        addons_str = input(f"Heroku Addons (comma separated) [{','.join(self.addons) if self.addons[0] else ''}]: ")
        if addons_str:
            self.addons = [addon.strip() for addon in addons_str.split(',')]
            self.config.set('heroku', 'addons', ','.join(self.addons))
        
        buildpacks_str = input(f"Heroku Buildpacks (comma separated) [{','.join(self.buildpacks) if self.buildpacks[0] else ''}]: ")
        if buildpacks_str:
            self.buildpacks = [bp.strip() for bp in buildpacks_str.split(',')]
            self.config.set('heroku', 'buildpacks', ','.join(self.buildpacks))

        # Variables de entorno
        print("\nConfigura variables de entorno (deja en blanco para terminar):")
        while True:
            key = input("Nombre de la variable: ")
            if not key:
                break
            value = input(f"Valor para {key}: ")
            self.config.set('env_vars', key, value)

        # Configuración de Cloudflare (opcional)
        use_cf = input("¿Configurar Cloudflare? (s/n): ").lower() == 's'
        if use_cf:
            self.cf_api_key = input(f"Cloudflare API Key [{self.cf_api_key or ''}]: ") or self.cf_api_key
            self.config.set('cloudflare', 'api_key', self.cf_api_key)
            
            self.cf_email = input(f"Cloudflare Email [{self.cf_email or ''}]: ") or self.cf_email
            self.config.set('cloudflare', 'email', self.cf_email)
            
            self.cf_zone_id = input(f"Cloudflare Zone ID [{self.cf_zone_id or ''}]: ") or self.cf_zone_id
            self.config.set('cloudflare', 'zone_id', self.cf_zone_id)
            
            self.cf_domain = input(f"Cloudflare Domain [{self.cf_domain or ''}]: ") or self.cf_domain
            self.config.set('cloudflare', 'domain', self.cf_domain)

        self._save_config()
        print(f"\nConfiguración guardada en {self.config_path}")

    def init_heroku_client(self):
        """Inicializa el cliente de Heroku."""
        if not self.heroku_api_key:
            print("Error: No se ha configurado la API key de Heroku.")
            sys.exit(1)
        self.heroku_client = heroku3.from_key(self.heroku_api_key)
        
    def get_branch_name(self):
        """Obtiene el nombre de la rama actual de git."""
        try:
            return subprocess.check_output("git rev-parse --abbrev-ref HEAD", shell=True).decode().strip()
        except subprocess.CalledProcessError:
            print("Error: No se pudo obtener el nombre de la rama.")
            sys.exit(1)
    
    def get_repo_name(self):
        """Obtiene el nombre del repositorio de GitHub."""
        try:
            remote_url = subprocess.check_output("git config --get remote.origin.url", shell=True).decode().strip()
            # Extraer el nombre del repositorio (user/repo) de la URL
            if "github.com" in remote_url:
                if remote_url.startswith("git@github.com:"):
                    return remote_url.split("git@github.com:")[1].replace(".git", "")
                elif remote_url.startswith("https://github.com/"):
                    return remote_url.split("https://github.com/")[1].replace(".git", "")
            return None
        except subprocess.CalledProcessError:
            return None
    
    def create_app(self, name=None, branch=None):
        """Crea una nueva aplicación en Heroku."""
        self.init_heroku_client()
        
        if not branch:
            branch = self.get_branch_name()
        
        # Crear un nombre para la app basado en el branch si no se especifica
        if not name:
            # Normalizar el nombre del branch para que sea válido en Heroku
            normalized_branch = branch.replace('/', '-').replace('_', '-').lower()
            name = f"review-{normalized_branch}"
            # Limitar a 30 caracteres (límite de Heroku)
            if len(name) > 30:
                name = name[:30]
        
        print(f"Creando app de Heroku: {name} para la rama: {branch}")
        
        try:
            app = self.heroku_client.create_app(name=name)
            print(f"✅ App creada: {app.name} ({app.web_url})")
            
            # Configurar buildpacks
            if self.buildpacks and self.buildpacks[0]:
                print("Configurando buildpacks...")
                for buildpack in self.buildpacks:
                    if buildpack:
                        app.add_buildpack(buildpack)
                print("✅ Buildpacks configurados")
            
            # Configurar addons
            if self.addons and self.addons[0]:
                print("Configurando addons...")
                for addon in self.addons:
                    if addon:
                        try:
                            app.add_addon(addon)
                            print(f"  ✅ Addon añadido: {addon}")
                        except Exception as e:
                            print(f"  ❌ Error al añadir addon {addon}: {str(e)}")
            
            # Configurar variables de entorno
            if self.env_vars:
                print("Configurando variables de entorno...")
                app.update_config(self.env_vars)
                print("✅ Variables de entorno configuradas")
            
            # Añadir al pipeline si se especificó uno
            if self.pipeline_id:
                print(f"Añadiendo app al pipeline {self.pipeline_id}...")
                url = f"https://api.heroku.com/pipeline-couplings"
                headers = {
                    "Accept": "application/vnd.heroku+json; version=3",
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.heroku_api_key}"
                }
                data = {
                    "app": app.id,
                    "pipeline": self.pipeline_id,
                    "stage": "development"
                }
                response = requests.post(url, headers=headers, json=data)
                if response.status_code in (201, 200):
                    print("✅ App añadida al pipeline")
                else:
                    print(f"❌ Error al añadir al pipeline: {response.text}")
            
            # Configurar git remote
            try:
                subprocess.run(f"git remote add {name} https://git.heroku.com/{name}.git", shell=True, check=True)
                print(f"✅ Git remote añadido: {name}")
            except subprocess.CalledProcessError:
                print(f"❌ No se pudo añadir el git remote. Quizás ya existe.")
                
            # Configurar Cloudflare si está habilitado
            if self.cf_api_key and self.cf_email and self.cf_zone_id and self.cf_domain:
                self.setup_cloudflare_domain(app.name, app.web_url)
                
            return app
            
        except Exception as e:
            print(f"❌ Error al crear la app: {str(e)}")
            return None
    
    def setup_cloudflare_domain(self, app_name, app_url):
        """Configura un subdominio en Cloudflare para la app."""
        if not all([self.cf_api_key, self.cf_email, self.cf_zone_id, self.cf_domain]):
            print("❌ Configuración de Cloudflare incompleta")
            return False
            
        print(f"Configurando subdominio en Cloudflare...")
        try:
            cf = Cloudflare(email=self.cf_email, token=self.cf_api_key)
            
            # Crear un subdominio basado en el nombre de la app
            subdomain = f"{app_name}.{self.cf_domain}"
            
            # Extraer el dominio de la URL de Heroku (quitar https://)
            target_domain = app_url.replace('https://', '').strip('/')
            
            # Crear un registro CNAME apuntando a la app de Heroku
            record = {
                'name': subdomain,
                'type': 'CNAME',
                'content': target_domain,
                'ttl': 1,  # Auto
                'proxied': True  # Usar proxy de Cloudflare
            }
            
            result = cf.zones.dns_records.post(self.cf_zone_id, data=record)
            print(f"✅ Subdominio configurado: {subdomain}")
            print(f"  URL: https://{subdomain}")
            return True
            
        except Exception as e:
            print(f"❌ Error al configurar Cloudflare: {str(e)}")
            return False
    
    def deploy(self, app_name=None, branch=None):
        """Despliega la rama actual a la app de Heroku."""
        if not branch:
            branch = self.get_branch_name()
            
        if not app_name:
            # Normalizar el nombre del branch para que sea válido en Heroku
            normalized_branch = branch.replace('/', '-').replace('_', '-').lower()
            app_name = f"review-{normalized_branch}"
            # Limitar a 30 caracteres (límite de Heroku)
            if len(app_name) > 30:
                app_name = app_name[:30]
                
        print(f"Desplegando rama {branch} a {app_name}...")
        try:
            # Verificar si existe el remote
            remotes = subprocess.check_output("git remote", shell=True).decode().strip().split('\n')
            if app_name not in remotes:
                print(f"Añadiendo git remote para {app_name}...")
                subprocess.run(f"git remote add {app_name} https://git.heroku.com/{app_name}.git", 
                              shell=True, check=True)
            
            # Hacer push al remote de Heroku
            subprocess.run(f"git push {app_name} {branch}:main -f", shell=True, check=True)
            print(f"✅ Despliegue completado en {app_name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error al desplegar: {str(e)}")
            return False
