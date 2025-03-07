# Heroku Review Apps

Una herramienta para crear y gestionar review apps en Heroku con integración de GitHub y Cloudflare.

## Instalación

```bash
pip install heroku-review-apps
```

## Características

- Creación automatizada de review apps en Heroku basadas en ramas de git
- Configuración de buildpacks, addons y variables de entorno
- Integración con pipelines de Heroku
- Configuración opcional de subdominios en Cloudflare
- Despliegue automatizado desde ramas de git

## Uso

### Configuración inicial

```bash
heroku-review setup
```

### Crear una nueva review app

```bash
heroku-review create
```

### Desplegar a una app existente

```bash
heroku-review deploy
```

## Requisitos

- Python 3.6+
- Git
- Cuenta de Heroku
- Cuenta de Cloudflare (opcional)

## Licencia

MIT