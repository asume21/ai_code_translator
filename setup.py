from setuptools import setup, find_packages

setup(
    name="ai_code_translator",
    version="1.0.0",
    description="AI-powered code translator with vulnerability scanning",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "google-generativeai>=0.3.0",
        "ttkbootstrap>=1.10.1",
        "pygments>=2.16.1",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "jsonschema>=4.19.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scikit-learn>=1.3.0",
        "nltk>=3.8.1",
        "spacy>=3.6.0",
        "transformers>=4.36.0",
        "torch>=2.1.0",
        "pydantic>=2.5.3",
        "python-jose>=3.3.0",
        "passlib>=1.7.4",
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "python-multipart>=0.0.6",
        "pytest>=7.4.3",
        "black>=23.11.0",
        "isort>=5.12.0",
        "mypy>=1.6.1",
        "flake8>=6.1.0",
        "pre-commit>=3.5.0"
    ],
    package_data={
        "": ["*.json", "*.ico"],
        "security": ["patterns/*.json"],
        "resources": ["icon.ico"]
    },
    entry_points={
        'console_scripts': [
            'ai_code_translator=integrated_gui:main',
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.11',
)
