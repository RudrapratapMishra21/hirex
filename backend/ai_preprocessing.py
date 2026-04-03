import nltk
import re
from nltk.corpus import stopwords

# Download stopwords only if not present
try:
    stopwords.words("english")
except LookupError:
    nltk.download("stopwords")

stop_words = set(stopwords.words("english"))

def preprocess(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', '', text)
    words = text.split()
    words = [w for w in words if w not in stop_words]
    return " ".join(words)