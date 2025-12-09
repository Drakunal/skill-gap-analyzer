import json
from app.llm.client import ask_llm
from app.llm.prompts import RECOMMEND_PROMPT

def recommend_for_skills(skill: str):
    prompt = RECOMMEND_PROMPT.replace('{SKILL}', skill)
    resp = ask_llm(prompt)
    project = f'Build a small project to learn {skill}'
    resources = [f'Official docs for {skill}']
    cv_bullet = f'Worked with {skill}'
    try:
        parsed = json.loads(resp)
        project = parsed.get('project', project)
        resources = parsed.get('resources', resources)
        cv_bullet = parsed.get('cv_bullet', cv_bullet)
    except Exception:
        # fallback simple split
        pass
    return {'skill': skill, 'project': project, 'resources': resources, 'cv_bullet': cv_bullet}
