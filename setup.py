from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    """Read README.md file."""
    here = os.path.abspath(os.path.dirname(__file__))
    readme_path = os.path.join(here, 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Smart Lamp System - VIP Project Group E"

# Read requirements
def read_requirements():
    """Read requirements.txt file."""
    here = os.path.abspath(os.path.dirname(__file__))
    requirements_path = os.path.join(here, 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="smart-lamp-vip",
    version="1.0.0",
    description="Smart Lamp System with ML pattern recognition and environmental monitoring",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    
    # Project information
    author="VIP Project Group E",
    author_email="smart-lamp-group-e@inha.edu",
    url="https://github.com/vip-group-e/smart-lamp",
    project_urls={
        "Documentation": "https://github.com/vip-group-e/smart-lamp/docs",
        "Source": "https://github.com/vip-group-e/smart-lamp",
        "Tracker": "https://github.com/vip-group-e/smart-lamp/issues",
    },
    
    # Package configuration
    packages=find_packages(exclude=["tests*", "docs*", "scripts*"]),
    python_requires=">=3.8",
    install_requires=read_requirements(),
    
    # Entry points
    entry_points={
        "console_scripts": [
            "smart-lamp=main:main",
            "smart-lamp-test=main:run_tests",
        ],
    },
    
    # Additional data files
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
        "src": ["config/*.py"],
        "data": ["*.json", "*.csv"],
        "docs": ["*.md", "*.rst"],
    },
    
    # Classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "Topic :: Home Automation",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Environment :: Web Environment",
    ],
    
    keywords=[
        "smart-lamp", "iot", "raspberry-pi", "machine-learning", 
        "environmental-monitoring", "home-automation", "vip-project"
    ],
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "rpi": [
            "RPi.GPIO>=0.7.1",
            "adafruit-circuitpython-dht>=3.7.0",
            "adafruit-circuitpython-mcp3xxx>=1.4.0",
        ],
        "audio": [
            "pygame>=2.1.0",
            "pyaudio>=0.2.11",
            "pydub>=0.25.1",
        ],
        "web": [
            "streamlit>=1.25.0",
            "plotly>=5.15.0",
            "pandas>=1.5.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "numpy>=1.24.0",
            "scipy>=1.10.0",
        ],
    },
    
    # License
    license="MIT",
    
    # Zip safety
    zip_safe=False,
    
    # Minimum requirements check
    setup_requires=[
        "setuptools>=45",
        "wheel",
    ],
)
