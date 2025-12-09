```markdown
# **Skill Gap Analyzer – README**

A fully modular **AI-driven CV vs Job Description analyzer** built using FastAPI.  
It identifies skill gaps, computes suitability scores, and generates actionable improvement recommendations using a combination of **LLM reasoning** + **deterministic fallback pipelines**.

---

# 🚀 **Features**

- Upload CV (PDF/DOCX/TXT) → Automated parsing & caching  
- LLM-powered JD–CV comparison with structured JSON output  
- Fallback analysis pipeline (zero-cost, no external API calls)  
- Smart missing-skill recommendations  
- Human-readable summaries for candidates  
- Daily rotating logs  
- Clean modular architecture  

---

# 📁 **Project Structure**

```

app/
│
├── api/
│   └── routes.py
│
├── core/
│   ├── config.py
│   ├── logger.py
│   └── prompts.py
│
├── cache/
│   └── cv_cache.py
│
├── llm/
│   └── client.py
│
├── models/
│   └── schemas.py
│
├── services/
│   ├── analyze_service.py
│   ├── extractor_service.py
│   ├── compare_service.py
│   ├── parser_service.py
│   └── recommend_service.py
│
└── main.py

```

---

# ⚙️ **Services Overview**

### **1. analyze_service.py (THE BRAIN)**
Handles the full end-to-end analysis:
- Calls LLM with structured prompts  
- Validates JSON response  
- Performs hallucination checks  
- Computes skill gap & suitability  
- Combines LLM suggestions + deterministic recommendations  
- Builds human-readable summaries  
- Fallback mode activates automatically when:
  - LLM quota exceeded  
  - JSON invalid  
  - API failure  

---

### **2. extractor_service.py**
Used mainly in fallback mode:
- Extracts skills from JD/CV  
- Attempts LLM first  
- Falls back to regex-based keyword extraction  
- Ensures the system still functions without LLM

---

### **3. compare_service.py**
Deterministic skill comparison:
- Keyword matching  
- Occurrence-based metrics  
- Missing-skill identification  
- Suitability scoring (non-LLM)  

---

### **4. parser_service.py**
Handles file parsing:
- Reads PDF, DOCX, TXT  
- Extracts text safely  
- Cleans content  
- Generates MD5 hash (cv_id)  
- Stores parsed CV in cache  

---

### **5. recommend_service.py**
Offline recommendation generator:
- For each missing skill:
  - Suggests a small project  
  - Generates an addable CV bullet  
  - Provides resources/tools for learning  
- Zero LLM cost  
- Used in combination with LLM suggestions  

---

# 🧠 **LLM Prompts**

Stored centrally in:
```

app/core/prompts.py

```

Contains:
- `ANALYZE_PROMPT_TEMPLATE`
- `CAREER_SUGGEST_PROMPT`
- `READABLE_POLISH_PROMPT`

Modifying behaviour requires changing only this file.

---

# 🧾 **API Endpoints**

### **1. Upload CV**
```

POST /api/v1/upload-cv

```
Returns:
- `cv_id`
- `snippet`
- `cached`

---

### **2. Analyze CV vs JD (Form-data)**
```

POST /api/v1/analyze-form

```
Good for large JDs in Postman/Swagger.

---

### **3. Analyze CV vs JD (JSON)**
```

POST /api/v1/analyze

```

---

### **4. Health**
```

GET /api/v1/health

```

---

# 🔧 **Configuration (.env)**

```

OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash-lite

MAX_CV_CHARS=12000
MAX_CACHED_ITEMS=200

```

---

# 📜 **Logging**

File: `app/core/logger.py`

- Logs everything: uploads, LLM calls, fallback usage, errors  
- Daily log rotation  
- Log folder example:
```

logs/
├── 2025-12-09.log
├── 2025-12-10.log

```

Format:
```

2025-12-09 21:38:17,354 | INFO | skill_gap_analyzer | analyze_and_recommend:379 | message...

```

---

# 🌐 **Installation**

```

git clone <repo>
cd skill-gap-analyzer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

```

---

# 🔄 **High-Level Flowchart (Text Version)**

```

```
                   ┌─────────────────────────┐
                   │     Upload CV File      │
                   └────────────┬────────────┘
                                │
                                ▼
                  ┌──────────────────────────┐
                  │   parser_service reads   │
                  │  PDF/DOCX/TXT → text     │
                  └────────────┬─────────────┘
                                │
                       cv_id generated
                                │
                                ▼
                 ┌───────────────────────────┐
                 │   CV stored in cache      │
                 └────────────┬──────────────┘
                                │
                User sends JD + cv_id (Analyze)
                                │
                                ▼
             ┌──────────────────────────────────┐
             │    analyze_service orchestrates   │
             │   (LLM attempt → fallback if fail)│
             └──────────────────┬────────────────┘
                                │
                 ┌──────────────┴────────────────┐
                 │         LLM CALL SUCCESS?      │
                 └───────────┬──────┬────────────┘
                             │      │
                          YES│      │NO
                             │      │
                             ▼      ▼
   ┌───────────────────────────┐    ┌────────────────────────┐
   │ Parse structured JSON     │    │ extractor_service       │
   │ Required/CV/Missing Skills│    │ extract skills          │
   └──────────────┬────────────┘    └──────────────┬─────────┘
                  │                                │
                  ▼                                ▼
    ┌────────────────────────┐         ┌────────────────────────┐
    │ Merge recommendations  │         │ compare_service scores │
    │ (LLM + deterministic)  │         │ suitability & keywords │
    └──────────────┬─────────┘         └──────────────┬────────┘
                   │                                 │
                   ▼                                 ▼
     ┌──────────────────────────────┐     ┌──────────────────────────────┐
     │ Build human-readable summary │     │ recommend_service suggests   │
     │ readable_recommendations     │     │ projects & learning links    │
     └──────────────┬──────────────┘     └──────────────┬──────────────┘
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       ▼
                     ┌───────────────────────────────────┐
                     │   Structured JSON Response        │
                     │  + Human Summary                  │
                     └───────────────────────────────────┘
```

```

---

# 📦 **Example Output**

```

{
"required_skills": ["Python", "TensorFlow", "ML Ops"],
"cv_skills": ["Python", "Pytorch", "SQL"],
"missing_skills": ["TensorFlow", "ML Ops"],
"suitability": {"score": 0.62, "label": "Potential Fit"},
"readable_recommendations": [
"Build a TensorFlow CNN model...",
"Deploy a model using CI/CD..."
],
"human_readable_summary": "Fit: Potential Fit (62%). Missing skills: TensorFlow..."
}

```

---

# 🎯 **Future Enhancements (Optional)**

- User authentication (JWT)  
- Database storage of user sessions  
- Rate limiting per user  
- Admin dashboard for usage stats  
- Frontend UI (React / Next.js)  

---

If you'd like, I can also provide:
- Architecture diagram (text-based or Mermaid format)  
- A more detailed developer guide  
- API usage examples  
- A CLI wrapper for testing  

Just ask!  
```
