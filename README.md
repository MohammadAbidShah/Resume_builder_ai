# Resume Builder AI - Multi-Agent Agentic Workflow

A sophisticated **multi-agent AI system** specialized for **Data Analyst, Data Scientist, and Data Engineer roles** that builds and iteratively refines FAANG-quality resumes until they meet all professional standards including ATS compatibility, keyword optimization, and LaTeX excellence.

## 🎯 Overview

This project implements a production-ready **Agentic AI Workflow** using **LangGraph** and **Groq LLM APIs** that:

1. **Classifies** the target role from job descriptions with confidence scoring
2. **Generates** FAANG-optimized resume content with XYZ/STAR methodology
3. **Creates** professional, ATS-friendly LaTeX resumes
4. **Validates** ATS compatibility with real-time scoring (≥90% threshold)
5. **Assesses** PDF quality and visual excellence (≥85/100 threshold)
6. **Iterates** automatically with feedback loops until all standards are met
7. **Enforces** strict role constraints (Data Analyst/Scientist/Engineer only)

### Key Features

- ✅ **Dynamic Content Generation**: No pre-stored bullets—all content generated at runtime based on JD and personal info
- ✅ **Professional Summary**: Auto-generates 2-3 sentence summaries with quantified achievements
- ✅ **Model Stratification**: Uses `llama-3.3-70b-versatile` for content generation, `llama-3.1-8b-instant` for validation (~75% TPM savings)
- ✅ **Output Management**: Automatically keeps only the last 3 files per type (LaTeX, JSON, reports)
- ✅ **Network Fallback**: Optional fallback to mock responses when API is unreachable
- ✅ **Role Gating**: Rejects non-data roles with confidence thresholds
- ✅ **Iteration Tracking**: Complete audit trail with per-iteration state snapshots

## 🏗️ Architecture

### Six Specialized Agents + Workflow Orchestration

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   RESUME BUILDER AGENTIC WORKFLOW                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  INPUT: Job Description + Personal Info (personal_info.json)             │
│    ↓                                                                       │
│  [STEP 0] Role Classifier                                                 │
│    • Analyzes JD for role keywords                                        │
│    • Classifies: Data Analyst | Data Scientist | Data Engineer           │
│    • Confidence score (must be ≥90%)                                      │
│    • REJECTS non-data roles                                               │
│    ↓                                                                       │
│  [AGENT 1] Content Generator (llama-3.3-70b-versatile)                   │
│    • Extracts JD keywords with importance ranking                         │
│    • Generates professional summary (2-3 sentences, quantified)           │
│    • Creates experience bullets (XYZ/STAR format)                         │
│    • Generates project bullets (3 per project)                            │
│    • Writes certification descriptions                                    │
│    • Validates action verbs, quantification rate, keyword density         │
│    ↓                                                                       │
│  [AGENT 2] LaTeX Generator                                                │
│    • Converts content to LaTeX using template                             │
│    • Applies ATS-friendly formatting                                      │
│    • Integrates JD-aligned skill grouping                                 │
│    • Validates syntax (0 errors required)                                 │
│    ↓                                                                       │
│  ┌───────────────────────┬────────────────────────┐                      │
│  ↓                       ↓                         ↓                      │
│  [AGENT 3]           [AGENT 4]              [Parallel Validation]         │
│  ATS Checker         PDF Validator          (llama-3.1-8b-instant)       │
│  • Score: 0-100      • Quality: 0-100                                     │
│  • Keywords present  • LaTeX validity                                     │
│  • Missing keywords  • Structure analysis                                 │
│  • Blocking issues   • Visual formatting                                  │
│  ↓                       ↓                                                 │
│  └───────────────────────┴──────────────────┘                            │
│                          ↓                                                 │
│  [AGENT 5] Feedback & Decision (llama-3.1-8b-instant)                    │
│    • Evaluate 5 standards:                                                │
│      1. ATS Score ≥ 90%                                                   │
│      2. Keywords Complete                                                 │
│      3. LaTeX Valid                                                       │
│      4. PDF Quality ≥ 85/100                                              │
│      5. No ATS Blocking Issues                                            │
│    • Generate actionable feedback                                         │
│    • Decide: PASS or CONTINUE?                                            │
│    ├─→ ✓ PASS → Finalize & Save                                          │
│    └─→ ✗ CONTINUE → Loop back to AGENT 1 (max 2 iterations)              │
│                                                                            │
│  [OUTPUT] Final Resume                                                    │
│    • LaTeX file (outputs/latex/resume_*.tex)                              │
│    • JSON resume (outputs/resumes/resume_*.json)                          │
│    • Execution report (outputs/execution_report_*.json)                   │
│    • Iteration snapshots (outputs/iteration_*.json)                       │
│                                                                            │
│  [CLEANUP] Retention Policy                                               │
│    • Keep last 3 LaTeX files                                              │
│    • Keep last 3 JSON resumes                                             │
│    • Keep last 3 execution reports                                        │
│    • Keep last 3 iteration files                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Quality Standards (Exit Conditions)

The workflow **must** satisfy all 5 standards to finalize:

| Standard         | Threshold                     | Agent         |
| ---------------- | ----------------------------- | ------------- |
| **ATS Score**    | ≥ 90%                         | ATS Checker   |
| **Keywords**     | All critical keywords present | ATS Checker   |
| **LaTeX Syntax** | Valid, compilable, 0 errors   | PDF Validator |
| **PDF Quality**  | ≥ 85/100                      | PDF Validator |
| **ATS Blocking** | No format/parse blockers      | ATS Checker   |

**Hybrid Policy**: Allows automatic PASS when numeric thresholds are met and ≤1 non-blocking failures are present.

## 📁 Project Structure

```
ResumeBuilderAI/
├── input/                        # All input files (NEW)
│   ├── input_data.txt           # Job description
│   ├── personal_info.json       # Candidate information
│   └── templates/
│       └── resume_template.tex  # LaTeX template
│
├── config/
│   ├── settings.py              # Configuration, API keys, model selection
│   ├── prompts.py               # System prompts for all agents
│   └── __init__.py
│
├── agents/
│   ├── content_generator.py     # Agent 1: FAANG-optimized content (70B model)
│   ├── latex_generator.py       # Agent 2: LaTeX creation
│   ├── ats_checker.py           # Agent 3: ATS validation (8B model)
│   ├── pdf_validator.py         # Agent 4: Quality assessment (8B model)
│   ├── feedback_agent.py        # Agent 5: Decision making (8B model)
│   └── __init__.py
│
├── tools/
│   ├── groq_client.py           # Groq API client with model stratification
│   ├── content_tools.py         # Job parsing, keyword extraction
│   ├── latex_tools.py           # LaTeX generation & validation
│   ├── ats_optimizer.py         # JD-aligned skill grouping
│   ├── validation_tools.py      # ATS & PDF validation
│   └── __init__.py
│
├── graph/
│   ├── state.py                 # LangGraph state schema
│   ├── nodes.py                 # Workflow nodes (generate, validate, evaluate)
│   ├── edges.py                 # Conditional routing logic
│   ├── workflow.py              # LangGraph StateGraph compilation
│   └── __init__.py
│
├── utils/
│   ├── logger.py                # Structured logging
│   ├── validators.py            # JSON validation, schema checks
│   ├── helpers.py               # Cleanup utilities, iteration saving
│   └── __init__.py
│
├── outputs/
│   ├── resumes/                 # Generated JSON resumes (last 3 kept)
│   ├── latex/                   # Generated LaTeX files (last 3 kept)
│   ├── pdfs/                    # Generated PDFs (if compiled)
│   ├── execution_report_*.json  # Execution logs (last 3 kept)
│   └── iteration_*.json         # Per-iteration state (last 3 kept)
│
├── logs/                        # Application logs
│   └── resume_builder_*.log
│
├── main.py                      # Entry point & CLI
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (API keys, models)
├── .env.example                 # Environment template
├── .gitignore                   # Git exclusions
├── ARCHITECTURE.md              # Detailed system design
├── QUICKSTART.md                # Quick setup guide
└── README.md                    # This file
```

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.11+ (tested on 3.11.4)
- **Groq API Key**: Sign up at [console.groq.com](https://console.groq.com)
- **Virtual Environment**: Recommended for isolation

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ResumeBuilderAI
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv

   # On Windows:
   .venv\Scripts\activate

   # On macOS/Linux:
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the project root:

   ```bash
   # Copy from example
   cp .env.example .env
   ```

   Edit `.env` with your settings:

   ```env
   # Groq API Configuration
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_API_URL=https://api.groq.com
   GROQ_MOCK_MODE=false
   LOG_LEVEL=INFO

   # Model Stratification (Optimized for TPM)
   GROQ_CONTENT_GENERATOR_MODEL=llama-3.3-70b-versatile
   GROQ_ATS_CHECKER_MODEL=llama-3.1-8b-instant
   GROQ_PDF_VALIDATOR_MODEL=llama-3.1-8b-instant
   GROQ_FEEDBACK_AGENT_MODEL=llama-3.1-8b-instant

   # Optional: Network Fallback
   ENABLE_NETWORK_FALLBACK=true
   ```

5. **Configure input files**

   Edit `input/input_data.txt` with your target job description:

   ```
   Data Scientist role requiring Python, SQL, Machine Learning...
   ```

   Edit `input/personal_info.json` with your information:

   ```json
   {
     "name": "Your Name",
     "email": "your@email.com",
     "phone": "+1 (555) 123-4567",
     "location": "City, State",
     "experience": [...],
     "skills": {...},
     "education": [...],
     "projects": [...],
     "awards_and_certifications": [...]
   }
   ```

### Quick Start

**Run the workflow:**

```bash
python main.py
```

**Expected output:**

```
2026-01-08 10:30:45 - ResumeBuilder - INFO - RESUME BUILDER AI - STARTING EXECUTION
2026-01-08 10:30:46 - ResumeBuilder - INFO - === ITERATION 1: Content Generation ===
2026-01-08 10:30:48 - ResumeBuilder - INFO - [OK] Content generated successfully
2026-01-08 10:30:49 - ResumeBuilder - INFO - [OK] LaTeX code generated successfully
2026-01-08 10:30:50 - ResumeBuilder - INFO - [OK] ATS check complete: 92.0%
2026-01-08 10:30:51 - ResumeBuilder - INFO - [OK] PDF validation complete: 97/100
2026-01-08 10:30:52 - ResumeBuilder - INFO - [OK] ALL STANDARDS MET - FINALIZING
2026-01-08 10:30:52 - ResumeBuilder - INFO - Final LaTeX saved to: outputs/latex/resume_20260108_103052.tex
2026-01-08 10:30:52 - ResumeBuilder - INFO - Resume JSON saved to: outputs/resumes/resume_20260108_103052.json
```

**Find your outputs:**

- LaTeX: `outputs/latex/resume_YYYYMMDD_HHMMSS.tex`
- JSON: `outputs/resumes/resume_YYYYMMDD_HHMMSS.json`
- Report: `outputs/execution_report_YYYYMMDD_HHMMSS.json`

## 📊 How It Works

### Iteration Flow

Each iteration follows this strict sequence:

```
1. CONTENT GENERATION (Agent 1)
   ├─ Parse JD for keywords
   ├─ Generate professional summary
   ├─ Create experience bullets (XYZ/STAR)
   ├─ Generate project bullets
   └─ Write certification descriptions

2. LATEX CREATION (Agent 2)
   ├─ Apply template
   ├─ Group skills by JD alignment
   ├─ Format for ATS compliance
   └─ Validate syntax

3. PARALLEL VALIDATION
   ├─ ATS CHECK (Agent 3)
   │  ├─ Calculate score (0-100)
   │  ├─ Check keyword coverage
   │  └─ Detect blocking issues
   │
   └─ PDF VALIDATION (Agent 4)
      ├─ Validate LaTeX syntax
      ├─ Check structure
      └─ Score quality (0-100)

4. DECISION (Agent 5)
   ├─ Evaluate 5 standards
   ├─ Check hybrid policy
   └─ Decide: PASS or CONTINUE

5. FINALIZATION (if PASS)
   ├─ Save LaTeX
   ├─ Save JSON resume
   ├─ Save execution report
   ├─ Cleanup old files (keep last 3)
   └─ Exit

   OR

5. ITERATION (if FAIL and < MAX_ITERATIONS)
   ├─ Generate detailed feedback
   ├─ Save iteration snapshot
   └─ Loop back to step 1
```

### Example Execution

**Iteration 0** (Initial):

```
├─ Content Generated:
│  ├─ Professional summary: "Senior Data Scientist with 5+ years..."
│  ├─ Experience bullets: 4 bullets with metrics
│  ├─ Project bullets: 3 bullets per project
│  └─ Quality: 85% quantification, 100% strong verbs
│
├─ LaTeX Generated: 7402 chars, 0 syntax errors
│
├─ ATS Check: 92.0% (Skills: 90%, Exp: 74%, Proj: 72%)
│  ├─ Keywords present: Python, SQL, Machine Learning, AWS...
│  └─ Keywords missing: None
│
├─ PDF Validation: 97/100
│  ├─ LaTeX valid: Yes
│  └─ Structure: 5 sections, 12 bullets
│
├─ Decision: PASS ✓
│  ├─ ATS ≥ 90%: ✓
│  ├─ Keywords Complete: ✓
│  ├─ LaTeX Valid: ✓
│  ├─ PDF Quality ≥ 85: ✓
│  └─ No Blocking Issues: ✓
│
└─ Output: resume_20260108_103052.tex
```

**Iteration 1** (If iteration 0 failed):

```
├─ Feedback Applied:
│  └─ "Add keywords: TensorFlow, Spark; Improve project metrics"
│
├─ Content Regenerated:
│  ├─ Incorporated missing keywords
│  ├─ Enhanced project bullets with quantified outcomes
│  └─ Quality: 90% quantification, 100% strong verbs
│
├─ ATS Check: 94.5% ✓
├─ PDF Validation: 98/100 ✓
├─ Decision: PASS ✓
└─ Output: Final resume
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# === API Configuration ===
GROQ_API_KEY=your_api_key_here
GROQ_API_URL=https://api.groq.com
GROQ_MOCK_MODE=false              # Set to 'true' for offline testing
LOG_LEVEL=INFO

# === Model Stratification ===
# Use 70B for complex content generation, 8B for validation
# This reduces TPM usage by ~75%
GROQ_CONTENT_GENERATOR_MODEL=llama-3.3-70b-versatile
GROQ_ATS_CHECKER_MODEL=llama-3.1-8b-instant
GROQ_PDF_VALIDATOR_MODEL=llama-3.1-8b-instant
GROQ_FEEDBACK_AGENT_MODEL=llama-3.1-8b-instant

# === Optional Settings ===
ENABLE_NETWORK_FALLBACK=true      # Fallback to mock when API unreachable
HYBRID_ALLOWED_FAILURES=1         # Max non-blocking failures for auto-PASS
```

### Settings Configuration (config/settings.py)

```python
# Quality Thresholds
MIN_ATS_SCORE = 0.90              # 90% minimum ATS score
KEYWORD_MATCH_THRESHOLD = 0.80    # 80% keyword coverage
PDF_QUALITY_THRESHOLD = 85        # out of 100
LATEX_COMPILE_TIMEOUT = 30        # seconds

# Workflow Configuration
MAX_ITERATIONS = 2                # Maximum refinement cycles
ITERATION_TIMEOUT = 120           # seconds per iteration

# Hybrid Pass/Fail Policy
ENABLE_HYBRID_POLICY = True       # Allow PASS with minor non-blocking issues
HYBRID_ALLOWED_FAILURES = 1       # Max non-blocking failures to auto-pass

# Temperature Settings
CONTENT_GENERATION_TEMPERATURE = 0.7  # Higher for creativity
VALIDATION_TEMPERATURE = 0.3          # Lower for consistency
FEEDBACK_TEMPERATURE = 0.5            # Medium for decision-making
```

### Model Selection Strategy

| Agent                 | Model                   | Tokens     | Reason                                          |
| --------------------- | ----------------------- | ---------- | ----------------------------------------------- |
| **Content Generator** | llama-3.3-70b-versatile | ~2000-4000 | Complex reasoning, FAANG-level content creation |
| **ATS Checker**       | llama-3.1-8b-instant    | ~500-1000  | Simple validation, keyword matching             |
| **PDF Validator**     | llama-3.1-8b-instant    | ~500-1000  | Structural checks, syntax validation            |
| **Feedback Agent**    | llama-3.1-8b-instant    | ~500-800   | Binary decision, simple feedback                |

**TPM Savings**: Using 8B models for validation tasks reduces token consumption by ~75% compared to using 70B everywhere.

## 📝 Input Format

### Personal Information (input/personal_info.json)

Complete schema:

```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com",
  "phone": "+1 (555) 123-4567",
  "location": "San Francisco, CA",

  "experience": [
    {
      "title": "Senior Data Scientist",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "duration": "Jan 2021 - Present",
      "description": "Led development of ML models for customer segmentation..."
    },
    {
      "title": "Data Analyst",
      "company": "Analytics Inc",
      "location": "New York, NY",
      "duration": "Jun 2018 - Dec 2020",
      "description": "Built dashboards and reports for executive leadership..."
    }
  ],

  "skills": {
    "Programming Languages": ["Python", "R", "SQL", "JavaScript"],
    "ML & Analytics": [
      "Scikit-learn",
      "TensorFlow",
      "PyTorch",
      "Pandas",
      "NumPy"
    ],
    "Visualization": ["Tableau", "Power BI", "Matplotlib", "Plotly"],
    "Cloud & Tools": ["AWS", "Docker", "Git", "Airflow", "dbt"],
    "Databases": ["PostgreSQL", "MongoDB", "Snowflake", "BigQuery"]
  },

  "education": [
    {
      "degree": "Master of Science in Data Science",
      "school": "Stanford University",
      "location": "Stanford, CA",
      "graduation_year": "2018",
      "gpa": "3.9/4.0",
      "relevant_coursework": "Machine Learning, Statistical Modeling, Big Data Analytics"
    },
    {
      "degree": "Bachelor of Science in Computer Science",
      "school": "UC Berkeley",
      "location": "Berkeley, CA",
      "graduation_year": "2016",
      "gpa": "3.7/4.0"
    }
  ],

  "projects": [
    {
      "name": "Customer Churn Prediction Using Machine Learning",
      "technologies": ["Python", "Scikit-learn", "XGBoost", "AWS"],
      "description": "Built predictive model achieving 89% accuracy...",
      "link": "github.com/username/churn-prediction"
    },
    {
      "name": "Real-Time Sales Dashboard",
      "technologies": ["Tableau", "SQL", "Python", "Airflow"],
      "description": "Developed automated ETL pipeline and executive dashboard...",
      "link": "portfolio.com/sales-dashboard"
    }
  ],

  "awards_and_certifications": [
    {
      "name": "AWS Certified Machine Learning – Specialty",
      "issuer": "Amazon Web Services",
      "date": "2023"
    },
    {
      "name": "Google Data Analytics Professional Certificate",
      "issuer": "Google",
      "date": "2022"
    }
  ]
}
```

### Job Description (input/input_data.txt)

Plain text format. Include:

- Role title and level
- Key responsibilities
- Required skills and tools
- Nice-to-have qualifications
- Company context (optional)

**Example:**

```
Data Scientist - Senior Level

We're seeking an experienced Data Scientist to join our analytics team...

Key Responsibilities:
• Build and deploy ML models for customer behavior prediction
• Collaborate with engineering teams on data pipeline architecture
• Present insights to executive leadership

Required Skills:
• Python, SQL, Machine Learning (scikit-learn, TensorFlow)
• Statistical analysis and hypothesis testing
• Data visualization (Tableau, Power BI)
• 5+ years of experience in data science roles

Nice to Have:
• AWS/GCP cloud experience
• Big data tools (Spark, Hadoop)
• Experience with A/B testing
```

## 📤 Output

The system generates four types of output files (last 3 of each retained):

### 1. LaTeX Resume (`outputs/latex/resume_*.tex`)

Professional, ATS-optimized LaTeX document:

```latex
\documentclass[11pt,a4paper]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{enumitem}
...

\begin{document}

{\Large\textbf{Jane Doe}}
\\ San Francisco, CA | (555) 123-4567 | jane.doe@example.com

\section*{Professional Summary}
Senior Data Scientist with 5+ years building ML models...

\section*{Technical Skills}
\textbf{Programming:} Python, R, SQL...

\section*{Professional Experience}
\textbf{Senior Data Scientist} | Tech Corp | San Francisco, CA | Jan 2021 - Present
\begin{itemize}[leftmargin=*,itemsep=0pt]
  \item Architected ML pipeline processing 5M+ records/day...
  \item Optimized model performance by 40\% using XGBoost...
\end{itemize}

...
\end{document}
```

**Compile to PDF:**

```bash
pdflatex outputs/latex/resume_20260108_103052.tex
```

### 2. JSON Resume (`outputs/resumes/resume_*.json`)

Structured resume content with metadata:

```json
{
  "professional_summary": "Senior Data Scientist with 5+ years...",
  "personal_info": {...},
  "experience": [...],
  "skills": {...},
  "education": [...],
  "projects": [...],
  "matched_keywords": ["Python", "Machine Learning", "AWS", ...],
  "missing_keywords": [],
  "quality_report": {
    "quantification_rate": 0.85,
    "action_verb_compliance": 1.0,
    "keyword_coverage": 0.92
  },
  "source_job_keywords": [...]
}
```

### 3. Execution Report (`outputs/execution_report_*.json`)

Complete audit trail:

```json
{
  "status": "pass",
  "success": true,
  "total_iterations": 1,
  "final_ats_score": 92.0,
  "final_pdf_quality": 97.0,
  "execution_time_seconds": 8.36,
  "iterations": [
    {
      "iteration": 0,
      "ats_score": 92.0,
      "pdf_quality": 97.0,
      "latex_valid": true,
      "standards_met": {
        "ATS_Score_90%+": true,
        "Keywords_Complete": true,
        "LaTeX_Valid": true,
        "PDF_Quality_85+": true,
        "No_ATS_Blocking_Issues": true
      },
      "decision": "PASS",
      "feedback": "All quality standards met..."
    }
  ],
  "timestamp": "2026-01-08T10:30:52.123456"
}
```

### 4. Iteration Snapshot (`outputs/iteration_*.json`)

Per-iteration state capture for debugging:

```json
{
  "iteration": 0,
  "resume_content": {...},
  "latex_code": "\\documentclass...",
  "ats_result": {...},
  "pdf_result": {...},
  "feedback": {...}
}
```

### Output Retention Policy

The cleanup mechanism automatically removes older files, keeping only the **last 3** of each type:

- ✅ Last 3 LaTeX files
- ✅ Last 3 JSON resumes
- ✅ Last 3 execution reports
- ✅ Last 3 iteration snapshots

This prevents disk bloat while maintaining recent history for comparison.

## 🤖 Agent Details

### Agent 0: Role Classifier (Pre-Generation)

- **Model**: Uses mock classification based on keyword detection
- **Role**: Validate job description targets Data Analyst/Scientist/Engineer
- **Logic**:
  - Extracts keywords from JD
  - Scores each role category
  - Returns confidence (must be ≥90%)
- **Output**: `{"classified_role": "Data Scientist", "confidence": 95, "role_level": "Senior"}`
- **Failure**: Rejects non-data roles immediately

### Agent 1: Content Generator

- **Model**: `llama-3.3-70b-versatile` (70B for complex reasoning)
- **Role**: Generate FAANG-quality resume content
- **Features**:
  - XYZ/STAR methodology for bullets
  - Dynamic professional summary (2-3 sentences, quantified)
  - Experience bullets (4 per role, unique verbs)
  - Project bullets (3 per project)
  - Certification descriptions
  - Action verb validation (100% strong verbs required)
  - Quantification tracking (70%+ target)
  - Keyword density optimization (90%+ coverage)
- **Tools**:
  - `parse_job_description()`: Extract keywords
  - `extract_technical_skills()`: Identify tech stack
  - `rank_keywords_by_importance()`: Prioritize JD terms
- **Output**: Structured JSON resume with quality metadata

### Agent 2: LaTeX Generator

- **Model**: No LLM (template-based rendering)
- **Role**: Convert JSON to ATS-friendly LaTeX
- **Features**:
  - Template-driven rendering (`input/templates/resume_template.tex`)
  - JD-aligned skill grouping
  - LaTeX escaping for special characters
  - ATS formatting enforcement
  - Syntax validation (0 errors required)
- **Tools**:
  - `ATSOptimizer`: Skill grouping, JD context extraction
  - `validate_latex_syntax()`: Check compilation errors
- **Output**: Compilable LaTeX code (~5000-8000 chars)

### Agent 3: ATS Checker

- **Model**: `llama-3.1-8b-instant` (8B for efficient validation)
- **Role**: Validate ATS compatibility
- **Checks**:
  - Overall ATS score (0-100, ≥90 required)
  - Skills section coverage
  - Experience keyword density
  - Project alignment
  - Blocking issues (format, parse errors)
- **Tools**:
  - `check_ats_compatibility()`: Built-in heuristics
  - `extract_plain_text_from_latex()`: Parse LaTeX
- **Output**: `{"ats_score": 92.5, "keywords_present": [...], "keywords_missing": [...]}`

### Agent 4: PDF Validator

- **Model**: `llama-3.1-8b-instant` (8B for structural checks)
- **Role**: Assess PDF quality and LaTeX validity
- **Checks**:
  - LaTeX syntax (compilation readiness)
  - Visual formatting
  - Structure analysis (sections, bullet points)
  - ATS warnings
- **Tools**:
  - `validate_latex_syntax()`: Check errors
  - `validate_pdf_quality()`: Structure scoring
- **Output**: `{"quality_score": 97, "latex_valid": true, "recommendation": "PASS"}`

### Agent 5: Feedback & Decision Agent

- **Model**: `llama-3.1-8b-instant` (8B for binary decisions)
- **Role**: Evaluate standards and decide PASS/FAIL
- **Standards Checked**:
  1. ATS Score ≥ 90%
  2. Keywords Complete
  3. LaTeX Valid
  4. PDF Quality ≥ 85/100
  5. No ATS Blocking Issues
- **Decision Logic**:
  - **PASS**: All 5 standards met → Finalize
  - **FAIL**: <5 standards met → Generate feedback → Continue to next iteration
  - **Hybrid PASS**: Numeric thresholds met + ≤1 non-blocking failure
- **Output**: `{"overall_status": "PASS", "standards_met": {...}, "confidence_next_iteration": 85}`

## 📊 Monitoring & Logging

All logs are saved to `logs/resume_builder_YYYYMMDD_HHMMSS.log`

### Log Levels

- **INFO**: Normal workflow progress
- **WARNING**: Non-critical issues (e.g., empty summary, fallback triggered)
- **ERROR**: Critical failures (e.g., API errors, validation failures)

### Example Log Output

```
2026-01-08 10:30:45 - ResumeBuilder - INFO - ============================================================
2026-01-08 10:30:45 - ResumeBuilder - INFO - RESUME BUILDER AI - STARTING EXECUTION
2026-01-08 10:30:45 - ResumeBuilder - INFO - ============================================================
2026-01-08 10:30:46 - ResumeBuilder - INFO - Starting LangGraph workflow...
2026-01-08 10:30:46 - ResumeBuilder - INFO - === ITERATION 1: Content Generation ===
2026-01-08 10:30:46 - ResumeBuilder - INFO - === Content Generator Agent: Starting ===
2026-01-08 10:30:46 - ResumeBuilder - INFO - Extracted 9 critical keywords
2026-01-08 10:30:46 - ResumeBuilder - INFO - Creating initial resume content
2026-01-08 10:30:48 - ResumeBuilder - INFO - Received response from Groq API
2026-01-08 10:30:48 - ResumeBuilder - INFO - Filled professional summary via targeted re-prompt
2026-01-08 10:30:48 - ResumeBuilder - INFO - Master content generated - Summary: 675 chars, Experience: 4 bullets
2026-01-08 10:30:48 - ResumeBuilder - INFO - [OK] Content generated successfully
2026-01-08 10:30:48 - ResumeBuilder - INFO -   - Quantification rate: 80.0%
2026-01-08 10:30:48 - ResumeBuilder - INFO -   - Action verb compliance: 0.0%
2026-01-08 10:30:48 - ResumeBuilder - INFO -   - Keyword coverage: 0.0%
2026-01-08 10:30:48 - ResumeBuilder - INFO - Generating LaTeX code...
2026-01-08 10:30:48 - ResumeBuilder - INFO - LaTeX Generator: Rendered LaTeX from local template
2026-01-08 10:30:48 - ResumeBuilder - INFO - LaTeX validation: PASS (0 errors)
2026-01-08 10:30:48 - ResumeBuilder - INFO - [OK] LaTeX code generated successfully
2026-01-08 10:30:49 - ResumeBuilder - INFO - Checking ATS compatibility...
2026-01-08 10:30:49 - ResumeBuilder - INFO - ATS Analysis: Score = 92.0% (Skills: 85%, Exp: 65%, Proj: 57%)
2026-01-08 10:30:49 - ResumeBuilder - INFO - [OK] ATS check complete: 92.0%
2026-01-08 10:30:50 - ResumeBuilder - INFO - Validating PDF quality...
2026-01-08 10:30:50 - ResumeBuilder - INFO - PDF Quality Check: Score = 97/100
2026-01-08 10:30:50 - ResumeBuilder - INFO - [OK] PDF validation complete: 97/100
2026-01-08 10:30:51 - ResumeBuilder - INFO - Evaluating quality standards...
2026-01-08 10:30:51 - ResumeBuilder - INFO - Standards Check: 5/5 met
2026-01-08 10:30:51 - ResumeBuilder - INFO - [OK] ALL STANDARDS MET - FINALIZING
2026-01-08 10:30:51 - ResumeBuilder - INFO - === FINALIZING RESUME ===
2026-01-08 10:30:51 - ResumeBuilder - INFO - Total execution time: 8.36 seconds
2026-01-08 10:30:51 - ResumeBuilder - INFO - Final LaTeX saved to: outputs/latex/resume_20260108_103051.tex
2026-01-08 10:30:51 - ResumeBuilder - INFO - Resume JSON saved to: outputs/resumes/resume_20260108_103051.json
```

### Key Metrics to Monitor

| Metric                  | Good | Warning | Critical         |
| ----------------------- | ---- | ------- | ---------------- |
| **ATS Score**           | ≥92% | 90-91%  | <90%             |
| **PDF Quality**         | ≥95  | 85-94   | <85              |
| **Quantification Rate** | ≥75% | 60-74%  | <60%             |
| **Keyword Coverage**    | ≥90% | 80-89%  | <80%             |
| **Execution Time**      | <10s | 10-20s  | >20s             |
| **Iterations**          | 1    | 2       | 3+ (max reached) |

## 🔐 Best Practices

### Security

1. **API Key Management**

   - ✅ Store keys in `.env` file (never commit)
   - ✅ Add `.env` to `.gitignore`
   - ✅ Use `.env.example` as template
   - ❌ Never hardcode API keys in source files

2. **Model Selection**
   - ✅ Use 70B for content generation (complex reasoning)
   - ✅ Use 8B for validation tasks (saves ~75% TPM)
   - ❌ Don't use 70B for simple validation

### Performance Optimization

1. **Rate Limiting**

   - Monitor Groq API rate limits (TPM, RPM)
   - Use `ENABLE_NETWORK_FALLBACK=true` during development
   - Consider dev tier for higher limits

2. **Output Management**

   - Automatic cleanup keeps last 3 files per type
   - Adjust `MAX_ITERATIONS` to balance quality vs. cost
   - Review execution reports to optimize prompts

3. **Iteration Strategy**
   - Start with 1-2 iterations for testing
   - Increase to 3-5 for production quality
   - Monitor feedback loops for stuck iterations

### Content Quality

1. **Input Preparation**

   - Provide complete `personal_info.json` with all fields
   - Include quantified achievements in experience
   - List 3-5 relevant projects
   - Use clear, specific job descriptions

2. **Template Customization**

   - Modify `input/templates/resume_template.tex` for branding
   - Adjust margins, fonts, spacing as needed
   - Test LaTeX compilation locally

3. **Validation**
   - Review ATS scores and missing keywords
   - Check LaTeX output for special characters
   - Verify professional summary alignment with JD
   - Test PDF rendering with `pdflatex`

### Error Handling

1. **API Failures**

   - Enable network fallback for continuity
   - Check logs for detailed error messages
   - Verify API key validity
   - Monitor rate limit errors (429)

2. **Content Issues**

   - If summary is empty, re-prompt is automatic
   - If bullets are weak, adjust temperature
   - If keywords missing, enhance personal info

3. **LaTeX Errors**
   - Check for unescaped special characters (%, $, &, #)
   - Validate template syntax
   - Review generated code in `outputs/latex/`

## 🚨 Troubleshooting

### API Key Issues

**Error**: `GROQ_API_KEY is not configured in environment`

**Solution**:

1. Create `.env` file in project root
2. Add line: `GROQ_API_KEY=your_key_here`
3. Restart Python session to reload environment

---

### Rate Limit Errors (429)

**Error**: `Rate limit reached for model llama-3.3-70b-versatile`

**Solutions**:

1. **Wait**: Check error message for retry time
2. **Upgrade**: Consider Groq Dev tier for higher limits
3. **Stratify**: Ensure 8B models used for validation (already configured)
4. **Fallback**: Enable `ENABLE_NETWORK_FALLBACK=true` in `.env`

---

### Empty Professional Summary

**Warning**: `CRITICAL: Master prompt returned EMPTY professional summary!`

**Automatic Fix**: System now auto-retries with targeted re-prompt

**Manual Check**:

- Verify `personal_info.json` has experience data
- Check JD has sufficient context
- Review logs for LLM response issues

---

### Max Iterations Reached Without PASS

**Error**: Workflow completes with `status: fail` after 2 iterations

**Root Causes**:

1. **Low ATS Score**: Missing critical keywords from JD
2. **LaTeX Errors**: Special characters not escaped
3. **Poor Content Quality**: Weak action verbs or no metrics

**Solutions**:

1. Add missing keywords to `personal_info.json`
2. Enhance experience descriptions with quantified results
3. Review feedback in execution report
4. Adjust thresholds in `config/settings.py` (temporary)

---

### LaTeX Compilation Errors

**Error**: PDF validator reports syntax errors

**Common Causes**:

- Unescaped special chars: `%`, `$`, `&`, `#`, `_`, `{`, `}`
- Unclosed environments
- Invalid template modifications

**Solutions**:

1. Check `outputs/latex/resume_*.tex` manually
2. Test compilation: `pdflatex resume_*.tex`
3. Review LaTeX escaping in `agents/latex_generator.py`
4. Reset template: `cp input/templates/resume_template.tex.backup ...`

---

### Network/DNS Errors

**Error**: `NameResolutionError: No such host 'api.groq.com'`

**Solutions**:

1. Check internet connection
2. Verify DNS resolution: `nslookup api.groq.com`
3. Enable fallback: `ENABLE_NETWORK_FALLBACK=true`
4. Use VPN if corporate firewall blocks API

---

### Mock Mode Stuck

**Issue**: System always returns mock responses

**Solution**:

1. Check `.env`: `GROQ_MOCK_MODE=false` (not `true`)
2. Restart Python session
3. Verify with: `python -c "from config.settings import GROQ_MOCK_MODE; print(GROQ_MOCK_MODE)"`

---

### Output Files Not Generated

**Issue**: No LaTeX or JSON files in `outputs/`

**Checks**:

1. Verify workflow reached finalization (check logs)
2. Check directory permissions
3. Review errors in execution report
4. Ensure `config/settings.py` paths are correct

---

### Debugging Checklist

When something fails:

1. ✅ Check logs in `logs/resume_builder_*.log`
2. ✅ Review execution report in `outputs/`
3. ✅ Verify API key is valid and loaded
4. ✅ Check rate limits on Groq console
5. ✅ Validate input files format (JSON syntax)
6. ✅ Test with mock mode first (`GROQ_MOCK_MODE=true`)
7. ✅ Review iteration snapshots for state at failure point

## 🛠️ Advanced Usage

### Custom LaTeX Templates

Edit `input/templates/resume_template.tex` to customize styling:

```latex
% Change margins
\usepackage[margin=0.75in]{geometry}  % Default
\usepackage[margin=0.5in]{geometry}   % Tighter

% Change fonts
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}

% Change section formatting
\usepackage{titlesec}
\titleformat{\section}{\large\bfseries}{\thesection}{1em}{}[\titlerule]
```

### Programmatic Usage

```python
from main import run_resume_builder
from utils.helpers import load_personal_info
import json

# Load inputs
with open('input/input_data.txt', 'r') as f:
    job_description = f.read()

personal_info = load_personal_info('input/personal_info.json')

# Run workflow
result = run_resume_builder(
    job_description=job_description,
    personal_info=personal_info,
    quiet_mode=True  # Suppress display output
)

# Access results
print(f"Status: {result['status']}")
print(f"ATS Score: {result['ats_score']}")
print(f"PDF Quality: {result['pdf_quality']}")
print(f"LaTeX Path: {result['latex_path']}")
print(f"JSON Path: {result['json_path']}")
```

### Batch Processing

Process multiple job descriptions:

```python
import os
from main import run_resume_builder
from utils.helpers import load_personal_info

# Load personal info once
personal_info = load_personal_info('input/personal_info.json')

# Process multiple JDs
job_files = ['jd_analyst.txt', 'jd_scientist.txt', 'jd_engineer.txt']

for jd_file in job_files:
    with open(f'input/{jd_file}', 'r') as f:
        jd = f.read()

    print(f"\n=== Processing {jd_file} ===")
    result = run_resume_builder(jd, personal_info, quiet_mode=True)

    if result['status'] == 'pass':
        print(f"✓ Success: {result['latex_path']}")
    else:
        print(f"✗ Failed: {result.get('error', 'Unknown')}")
```

### Environment-Specific Configurations

Create multiple env files:

```bash
# .env.dev (for development with fallback)
GROQ_MOCK_MODE=false
ENABLE_NETWORK_FALLBACK=true
LOG_LEVEL=DEBUG

# .env.prod (for production)
GROQ_MOCK_MODE=false
ENABLE_NETWORK_FALLBACK=false
LOG_LEVEL=INFO
MAX_ITERATIONS=3
```

Load specific config:

```bash
# Development
cp .env.dev .env
python main.py

# Production
cp .env.prod .env
python main.py
```

### Testing & Validation

Run in mock mode for testing:

```bash
# Set mock mode
export GROQ_MOCK_MODE=true  # Linux/Mac
set GROQ_MOCK_MODE=true     # Windows CMD
$env:GROQ_MOCK_MODE="true"  # Windows PowerShell

# Run workflow (no API calls)
python main.py
```

Validate outputs:

```python
import json
from utils.validators import validate_json_output

# Validate resume JSON
with open('outputs/resumes/resume_20260108_103051.json', 'r') as f:
    resume = json.load(f)

# Check required fields
assert 'professional_summary' in resume
assert 'experience' in resume
assert len(resume['matched_keywords']) > 0

# Validate LaTeX
from tools.latex_tools import validate_latex_syntax
errors = validate_latex_syntax('outputs/latex/resume_20260108_103051.tex')
assert len(errors) == 0, f"LaTeX errors: {errors}"
```

## 📚 Additional Resources

### Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Detailed system design and agent interactions
- **[QUICKSTART.md](QUICKSTART.md)**: Fast setup guide for immediate use
- **[VISUAL_GUIDE.md](VISUAL_GUIDE.md)**: Diagrams and workflow visualizations
- **[GROQ_SETUP.md](GROQ_SETUP.md)**: Groq API configuration details
- **[INSTALLATION.md](INSTALLATION.md)**: Complete installation instructions

### External Resources

- **Groq API Docs**: [console.groq.com/docs](https://console.groq.com/docs)
- **LangGraph Tutorial**: [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/)
- **LaTeX Documentation**: [overleaf.com/learn](https://www.overleaf.com/learn)
- **ATS Best Practices**: [Resume optimization guides](https://www.jobscan.co/ats-resume)

### Community & Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Ask questions in GitHub Discussions
- **Contributing**: See contribution guidelines in `CONTRIBUTING.md`

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:

### High Priority

- [ ] **PDF Generation**: Integrate `pdflatex` subprocess for automatic PDF compilation
- [ ] **Role Gating Enforcement**: Strict confidence threshold checks across all nodes
- [ ] **Resume Parsing**: Extract data from existing resume PDFs/DOCX
- [ ] **A/B Testing**: Generate multiple resume variations for testing

### Medium Priority

- [ ] **Custom Templates**: Template gallery for different industries
- [ ] **LinkedIn Integration**: Import profile data automatically
- [ ] **Cover Letter Generation**: Companion agent for cover letters
- [ ] **Multi-Language Support**: Generate resumes in multiple languages

### Nice to Have

- [ ] **Web UI**: Flask/FastAPI frontend for non-technical users
- [ ] **Resume Analytics**: Historical tracking of ATS scores
- [ ] **Keyword Suggestions**: Proactive keyword recommendations
- [ ] **Interview Prep**: Generate interview questions from resume

### How to Contribute

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

**Guidelines**:

- Follow existing code style
- Add tests for new features
- Update documentation
- Include example outputs

## 📄 License

MIT License

Copyright (c) 2026 ResumeBuilderAI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 🙋 Support & Contact

### Getting Help

1. **Documentation**: Check guides in the repo (ARCHITECTURE.md, QUICKSTART.md)
2. **Logs**: Review `logs/` directory for detailed error traces
3. **Issues**: Search existing issues or create new one with:
   - Error message
   - Log excerpt
   - Input files (sanitized)
   - Environment details (Python version, OS)
4. **Discussions**: Ask questions in GitHub Discussions

### Reporting Bugs

Include in your bug report:

- **Description**: What went wrong?
- **Expected behavior**: What should have happened?
- **Actual behavior**: What actually happened?
- **Steps to reproduce**: How to recreate the issue?
- **Logs**: Relevant log excerpts
- **Environment**: Python version, OS, dependencies
- **Configuration**: `.env` settings (without API key)

### Feature Requests

Include in your feature request:

- **Use case**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches?
- **Impact**: Who benefits from this feature?

---

## 🎯 Project Status

**Current Version**: 1.0.0  
**Status**: Production-ready ✅  
**Last Updated**: January 2026  
**Maintained**: Yes

### Recent Updates

- ✅ Model stratification (70B for content, 8B for validation)
- ✅ Dynamic content generation (no pre-stored bullets)
- ✅ Professional summary auto-generation with re-prompt
- ✅ Output retention policy (last 3 files)
- ✅ Network fallback for API resilience
- ✅ Role classification with confidence gating

### Roadmap

**Q1 2026**:

- PDF auto-compilation
- Template gallery
- Enhanced role classifier

**Q2 2026**:

- Web UI
- Resume parsing
- A/B testing framework

---

**Built with**:

- LangGraph 🔗
- Groq API (llama-3.3-70b, llama-3.1-8b) 🤖
- Python 3.11+ 🐍
- LaTeX 📄

**For**: Data Analysts | Data Scientists | Data Engineers 📊

---

_Made with ❤️ for the data community_
