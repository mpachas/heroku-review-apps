import argparse
from .core import HerokuReviewAppCreator

def main():
    parser = argparse.ArgumentParser(description='Heroku Review App Creator')
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando setup
    setup_parser = subparsers.add_parser('setup', help='Configurar el script')
    
    # Comando create
    create_parser = subparsers.add_parser('create', help='Crear una nueva review app')
    create_parser.add_argument('--name', help='Nombre para la app de Heroku')
    create_parser.add_argument('--branch', help='Rama de git a utilizar')
    
    # Comando deploy
    deploy_parser = subparsers.add_parser('deploy', help='Desplegar a una review app existente')
    deploy_parser.add_argument('--name', help='Nombre de la app de Heroku')
    deploy_parser.add_argument('--branch', help='Rama de git a desplegar')
    
    args = parser.parse_args()
    
    creator = HerokuReviewAppCreator()
    
    if args.command == 'setup':
        creator.setup()
    elif args.command == 'create':
        app = creator.create_app(name=args.name, branch=args.branch)
        if app:
            creator.deploy(app_name=app.name, branch=args.branch)
    elif args.command == 'deploy':
        creator.deploy(app_name=args.name, branch=args.branch)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()