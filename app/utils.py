import pdfplumber
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_resume_text(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

def extract_keywords(text):
    # Basic regex + NLTK for skills (expand with custom list)
    skills_pattern = re.compile(r'(python|java|sql|react|flask|aws|docker|machine learning|etc)', re.I)
    skills = skills_pattern.findall(text)
    return list(set(skills))

def compare_resume_to_jd(resume_text, job_description):
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([resume_text, job_description])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    return round(similarity * 100, 2)  # Match percentage