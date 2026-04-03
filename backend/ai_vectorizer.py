from sklearn.feature_extraction.text import TfidfVectorizer
from ai_preprocessing import preprocess

def vectorize(job_desc, resumes):

    corpus = [preprocess(job_desc)] + [preprocess(r["text"]) for r in resumes]

    vectorizer = TfidfVectorizer(ngram_range=(1,2))

    vectors = vectorizer.fit_transform(corpus)

    return vectors