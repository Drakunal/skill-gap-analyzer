import time
import re
from collections import Counter
from app.models.schemas import KeywordMatch, Suitability, Difficulty, Improvement

def analyze_gap_and_keywords(required_skills, cv_skills, jd_text, cv_text):
    start = time.time()
    req = set([s.lower() for s in required_skills or []])
    cv = set([s.lower() for s in cv_skills or []])
    matched = sorted([s.title() for s in (req & cv)])
    missing = sorted([s.title() for s in (req - cv)])
    # keywords match - count occurrences
    matched_keywords = []
    for k in req:
        occ_jd = len(re.findall(r'\b' + re.escape(k) + r'\b', jd_text, flags=re.IGNORECASE))
        occ_cv = len(re.findall(r'\b' + re.escape(k) + r'\b', cv_text, flags=re.IGNORECASE))
        if occ_jd or occ_cv:
            context = []
            # extract small contexts
            for m in re.finditer(r'(.{0,40}\b' + re.escape(k) + r'\b.{0,40})', jd_text, flags=re.IGNORECASE):
                context.append(m.group(1))
                if len(context) >= 2:
                    break
            matched_keywords.append({
                'keyword': k.title(),
                'occurrences_in_jd': occ_jd,
                'occurrences_in_cv': occ_cv,
                'context_jd': context
            })
    # simple suitability score
    suit_score = 0.0
    if req:
        suit_score = round(len(matched)/len(req), 2)
    label = 'Not a Fit'
    if suit_score > 0.75:
        label = 'Strong Fit'
    elif suit_score > 0.4:
        label = 'Potential Fit'
    else:
        label = 'Not a Fit'
    # difficulty heuristic
    difficulty_score = 0.5
    reason = ''
    infra_terms = ['docker','ci/cd','aws','gcp','kubernetes']
    infra_missing = [m for m in missing if m.lower() in infra_terms]
    if infra_missing:
        difficulty_score = min(1.0, 0.6 + 0.1*len(infra_missing))
        reason = 'Missing infra/cloud skills: ' + ', '.join(infra_missing)
    else:
        difficulty_score = max(0.0, 1 - len(missing)*0.15)
        reason = 'Missing skills: ' + ', '.join(missing) if missing else 'No major missing skills'
    # suggested improvements (simple heuristics)
    improvements = []
    for ms in missing:
        improvements.append({
            'type': 'project',
            'title': f'Hands-on: small project for {ms}',
            'description': f'Build a small project demonstrating {ms} usage.',
            'priority': 'high'
        })
        improvements.append({
            'type': 'keyword',
            'keyword': ms,
            'suggestion': f'Add {ms} under skills or projects section in CV.',
            'priority': 'medium'
        })
    end = time.time()
    timing = {'analyzed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'parsing_ms': 0, 'analysis_ms': int((end-start)*1000)}
    flags = {'jd_malformed': False, 'cv_low_content': False, 'possible_hallucination': False}
    confidence = round(0.6 + 0.4*suit_score, 2)
    return {
        'required_skills': [s.title() for s in required_skills],
        'cv_skills': [s.title() for s in cv_skills],
        'missing_skills': missing,
        'matched_keywords': matched_keywords,
        'suitability': {'score': suit_score, 'label': label},
        'difficulty_estimate': {'score': round(difficulty_score,2), 'reason': reason},
        'suggested_improvements': improvements,
        'confidence': confidence,
        'flags': flags,
        'timing': timing
    }
