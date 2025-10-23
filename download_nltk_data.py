#!/usr/bin/env python3
import nltk
import sys

print("Downloading NLTK stopwords...")
try:
    nltk.download('stopwords', quiet=False)
    print("Successfully downloaded NLTK stopwords")
    sys.exit(0)
except Exception as e:
    print(f"Error downloading NLTK data: {e}")
    sys.exit(1)
