# **Skill Gap Analyzer – README**

A modular **AI-powered CV vs Job Description Analyzer** built using FastAPI.
It identifies required skills, matches them against the candidate’s CV, computes suitability scores, and generates actionable improvement recommendations using:

* LLM-powered structured reasoning
* Deterministic fallback pipelines (no API cost)
* Human-readable summaries

---

# 🚀 **Features**

* Upload CV (PDF / DOCX / TXT)
* Automated text extraction & caching
* LLM-based JD–CV comparison
* Extraction of required skills, missing skills, matched keywords
* Suitability scoring + difficulty estimation
* Actionable recommendations (LLM + deterministic)
* Human-readable summary for candidates
* Daily rotating logs for full observability

---

# 📁 **Project Structure**

```
app/
│
├── api/
│   └── routes.py                  # All API endpoints
│
├── core/
│   ├── config.py                  # Settings (.env loader)
│   └──  logger.py                  # Rotating logs
│
├── cache/
│   └── cv_cache.py                # In-memory CV storage
│
├── llm/
│   ├── client.py                  # OpenAI/Gemini wrapper
│   └── prompts.py                 # Centralized LLM prompts
│
├── models/
│   └── schemas.py                 # Pydantic API models
│
├── services/
│   ├── analyze_service.py         # The main engine (LLM + fallback)
│   ├── extractor_service.py       # Extracts skills (LLM + regex)
│   ├── compare_service.py         # Deterministic skill comparison
│   ├── parser_service.py          # File parsing + CV ID creation
│   └── recommend_service.py       # Offline recommendations
│
└── main.py                        # FastAPI entrypoint
```

---

# ⚙️ **Service Breakdown**

## **1. analyze_service.py → The Orchestrator**

This is the **core intelligence layer**.

Responsibilities:

* Builds prompts using JD + CV
* Calls LLM (analyze + recommendations)
* Validates JSON output
* Detects hallucinations
* Computes missing skills, matches, suitability
* Merges LLM suggestions + deterministic skill projects
* Generates human-readable summaries
* Falls back to non-LLM pipeline when:

  * LLM quota exceeded
  * JSON invalid
  * API failure

---

## **2. extractor_service.py**

Used primarily in fallback mode.

Responsibilities:

* Extract skill-like tokens from text
* Uses:

  * LLM-based extraction (first attempt)
  * Regex keyword extraction (fallback)
* Ensures analysis always works even when LLM is unavailable

---

## **3. compare_service.py**

Deterministic scoring engine.

Responsibilities:

* Compare JD skills vs CV skills
* Keyword matching with occurrence counts
* Missing skill detection
* Suitability score calculation
* Difficulty estimation heuristics

---

## **4. parser_service.py**

Handles file uploads.

Responsibilities:

* Parse PDF / DOCX / TXT → clean normalized text
* Generate `cv_id` using MD5 hashing
* Store parsed content in cache
* Return CV snippet for preview

---

## **5. recommend_service.py**

Provides **zero-cost** recommendations without LLM.

Responsibilities:

* Suggests a project for each missing skill
* Generates a CV bullet the user can add
* Includes learning resources or links
* Combined with LLM recommendations in output

---

# 🧠 **Centralized Prompts**

Located in:

```
app/core/prompts.py
```

Contains:

* `ANALYZE_PROMPT_TEMPLATE`
* `CAREER_SUGGEST_PROMPT`
* `READABLE_POLISH_PROMPT`

All LLM behavior can be tuned from this one file — no need to touch service logic.

---

# 🧾 **API Endpoints**

## **1. Upload CV**

```
POST /api/v1/upload-cv
```

Response:

* `cv_id`
* `snippet`
* `cached`

## **2. Analyze (Multipart Form)**

```
POST /api/v1/analyze-form
```

Best for large JDs.

## **3. Analyze (JSON)**

```
POST /api/v1/analyze
```

## **4. Health Check**

```
GET /api/v1/health
```

---

# 🛠️ **Configuration (.env)**

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

File:

```
app/core/logger.py
```

Features:

* Daily rotating logs (`YYYY-MM-DD.log`)
* Logs LLM prompts, errors, fallback events, API calls
* Keeps console output clean (unless debug enabled)

Example log entry:

```
2025-12-09 21:38:17,354 | INFO | skill_gap_analyzer | analyze_and_recommend:379 | LLM analyze failed — fallback activated.
```

---

# 🔄 **High-Level Flowchart (Text Format)**

```
                           ┌────────────────────────┐
                           │      Upload CV File    │
                           └─────────────┬──────────┘
                                         │
                                         ▼
                        ┌────────────────────────────────┐
                        │ parser_service: extract text    │
                        │ generate cv_id → save to cache  │
                        └─────────────────┬───────────────┘
                                          │
                           User sends JD + cv_id for analysis
                                          │
                                          ▼
                    ┌─────────────────────────────────────────┐
                    │   analyze_service orchestrates process   │
                    └──────────────────┬──────────────────────┘
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 │            LLM call successful?           │
                 └───────────────┬───────────────┬──────────┘
                                 │ Yes           │ No
                                 ▼               ▼
        ┌─────────────────────────────┐   ┌───────────────────────────┐
        │ Parse LLM JSON              │   │ extractor_service extracts │
        │ Required/CV/missing skills  │   │ skills (LLM → regex)       │
        └──────────────┬──────────────┘   └──────────────┬────────────┘
                       │                                   │
                       ▼                                   ▼
        ┌────────────────────────────┐      ┌──────────────────────────┐
        │ Merge LLM suggestions +    │      │ compare_service scores   │
        │ deterministic recommendations│      │ suitability & keywords  │
        └──────────────┬─────────────┘      └──────────────┬─────────┘
                       │                                     │
                       ▼                                     ▼
           ┌────────────────────────────┐      ┌───────────────────────────┐
           │ Build human summary        │      │ recommend_service generates│
           │ readable_recommendations   │      │ project ideas + CV bullets │
           └──────────────┬────────────┘      └──────────────┬────────────┘
                          │                                    │
                          └──────────────────┬─────────────────┘
                                             ▼
                               ┌────────────────────────────────┐
                               │ Final structured JSON response │
                               │ + human_readable_summary       │
                               └────────────────────────────────┘
```

---

# 📦 **Example Output**

```
{
  "required_skills": ["Python", "TensorFlow", "ML Ops"],
  "cv_skills": ["Python", "SQL", "Pytorch"],
  "missing_skills": ["TensorFlow", "ML Ops"],
  "suitability": {"score": 0.62, "label": "Potential Fit"},
  "readable_recommendations": [
    "Implement a TensorFlow CNN model for classification...",
    "Deploy a model through a minimal CI/CD pipeline..."
  ],
  "human_readable_summary": "Fit: Potential Fit (62%). Missing skills: TensorFlow, ML Ops. Top action: Implement a TensorFlow CNN model..."
}
```
---

# 🏃‍♂️ **How to Run the Project**

Follow these steps to set up and run the Skill Gap Analyzer locally.

---

## **1️⃣ Clone the Repository**

```
git clone https://github.com/Drakunal/skill-gap-analyzer.git
cd skill-gap-analyzer
```

---

## **2️⃣ Create a Virtual Environment**

```
python3 -m venv venv
source venv/bin/activate       # macOS / Linux
venv\Scripts\activate          # Windows PowerShell
```

---

## **3️⃣ Install Dependencies**

```
pip install -r requirements.txt
```

---

## **4️⃣ Create a `.env` File**

Inside the project root, create:

```
.env
```

With contents:

```
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o-mini

GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash-lite

MAX_CV_CHARS=12000
MAX_CACHED_ITEMS=200
```

⚠️ **At least one key (OpenAI or Gemini) must be valid** for full LLM-powered analysis.
If both fail, the system automatically falls back to deterministic mode.

---

## **5️⃣ Run the Server**

```
uvicorn app.main:app --reload
```

You should now see:

```
Uvicorn running on http://127.0.0.1:8000
```

---

## **6️⃣ Open API Docs**

Visit:

```
http://127.0.0.1:8000/docs
```

You'll find:

* **POST /upload-cv**
* **POST /analyze-form**
* **POST /analyze**
* **GET /health**

Everything is interactive.

---

## **7️⃣ Usage Flow**

### **Step 1 → Upload CV**

Use `/api/v1/upload-cv`
Returns:

* `cv_id`
* `cached`
* `snippet`

### **Step 2 → Analyze**

Use either:

#### **Form Data (recommended for large JDs):**

```
POST /api/v1/analyze-form
job_description = (paste JD here)
cv_id = (from upload response)
```

#### **JSON Input:**

```
POST /api/v1/analyze
{
  "job_description": "....",
  "cv_id": "md5hash..."
}
```

---

## **8️⃣ Logs**

All logs go to:

```
logs/YYYY-MM-DD.log
```

Logs include:

* LLM prompts (trimmed)
* Errors
* Fallback triggers
* Parsed CV sizes
* Timing diagnostics

---

## **9️⃣ Optional: Run in Production (Gunicorn + Uvicorn Workers)**

```
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
```

---

# 🎯 **Future Enhancements**

* Database integration (PostgreSQL / MongoDB)
* User accounts & saved analyses
* Frontend (Next.js / React)
* PDF report export
* Multi-model support (Anthropic, DeepSeek, Llama)
