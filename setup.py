from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="heroku-review-apps",
    version="0.1.0",
    author="mpachas",
    description="Herramienta para crear y gestionar review apps en Heroku con integración de GitHub y Cloudflare",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mpachas/heroku-review-apps",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests",
        "python-cloudflare",
        "git+https://github.com/mpachas/heroku-python-client.git",
    ],
    entry_points={
        "console_scripts": [
            "heroku-review=heroku_review_apps.cli:main",
        ],
    },
)