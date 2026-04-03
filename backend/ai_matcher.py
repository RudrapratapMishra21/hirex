from sklearn.metrics.pairwise import cosine_similarity
from ai_vectorizer import vectorize

def rank_resumes(job_desc, resumes):

    if len(resumes) == 0:
        return []

    vectors = vectorize(job_desc, resumes)

    scores = cosine_similarity(vectors[0:1], vectors[1:])[0]

    results = []

    for i, score in enumerate(scores):

        results.append({
            "candidate": resumes[i]["name"],
            "match_percent": round(score * 100, 2)
        })

    results.sort(key=lambda x: x["match_percent"], reverse=True)

    return results