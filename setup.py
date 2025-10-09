# setup.py
from setuptools import setup, find_packages

setup(
    name="noa",
    version="0.1.0",
    description="A package for simulating social causality with LLM agents.",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "langchain",
        "langchain-google-genai",
        "langchain-community",
        "langgraph",
        "kerykeion",
        "pytz",
        "python-dotenv",
        "tiktoken",
    ],
)