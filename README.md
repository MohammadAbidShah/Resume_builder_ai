# Resume Builder AI - Agentic Workflow

A sophisticated multi-agent AI system that builds and iteratively refines resumes until they meet all quality standards including ATS compatibility, keyword matching, and visual excellence.

## 🎯 Overview

This project implements a production-ready **Agentic AI Workflow** using **LangChain** and **LangGraph** that:

1. **Generates** optimized resume content from job descriptions
2. **Creates** professional LaTeX resumes
3. **Validates** ATS compatibility with real-time scoring
4. **Assesses** PDF quality and visual appeal
5. **Iterates** automatically until all standards are met

## 🏗️ Architecture

### Five Specialized Agents

```
┌─────────────────────────────────────────────────────────────────┐
│                    RESUME BUILDER WORKFLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  INPUT: Job Description + Personal Info                         │
│    ↓                                                             │
│  [AGENT 1] Content Generator                                    │
│    • Extracts job keywords                                      │
│    • Optimizes resume content                                   │
│    • Highlights relevant experience                             │
│    ↓                                                             │
│  [AGENT 2] LaTeX Generator                                      │
│    • Converts content to LaTeX                                  │
│    • Ensures ATS-friendly formatting                            │
│    ↓                                                             │
│  ┌──────────────────┬─────────────────────────────┐            │
│  ↓                  ↓                              ↓            │
│  [AGENT 3]      [AGENT 4]                    [Parallel]         │
│  ATS Checker    PDF Validator                                   │
│  • Score: 0-100  • Quality: 0-100                               │
│  • Keywords      • Formatting                                   │
│  • Blocking issues • Structure                                  │
│  ↓                  ↓                                            │
│  └──────────────────┬──────────────────┘                        │
│                     ↓                                            │
│  [AGENT 5] Feedback & Decision                                  │
│    • Check all standards                                        │
│    • Generate feedback                                          │
│    • Decide: PASS or CONTINUE?                                  │
│    ├─→ ✓ PASS → Output Final Resume                            │
│    └─→ ✗ CONTINUE → Loop back to AGENT 1                       │
│                                                                   │
│  (Repeat until all standards met or max iterations reached)     │
└─────────────────────────────────────────────────────────────────┘
```

### Quality Standards (Exit Conditions)

- **ATS Score**: ≥ 90%
- **Keywords**: All critical keywords from job description present
- **LaTeX Structure**: Valid, compilable, no syntax errors
- **PDF Quality**: Visual appeal score ≥ 85/100

## 📁 Project Structure

```
ResumeBuilderAI/
├── config/
│   ├── settings.py          # Configuration & API keys
│   ├── prompts.py           # System prompts for all agents
│   └── __init__.py
│
├── agents/
│   ├── content_generator.py # Agent 1: Content generation
│   ├── latex_generator.py   # Agent 2: LaTeX creation
│   ├── ats_checker.py       # Agent 3: ATS validation
│   ├── pdf_validator.py     # Agent 4: Quality assessment
│   ├── feedback_agent.py    # Agent 5: Decision making
│   └── __init__.py
│
├── tools/
│   ├── content_tools.py     # Content parsing & optimization
│   ├── latex_tools.py       # LaTeX generation & validation
│   ├── validation_tools.py  # ATS & PDF validation
│   └── __init__.py
│
├── graph/
│   ├── state.py             # State schema definition
│   ├── nodes.py             # Workflow nodes
│   ├── edges.py             # Conditional logic
│   ├── workflow.py          # LangGraph compilation
│   └── __init__.py
│
├── utils/
│   ├── logger.py            # Logging configuration
│   ├── validators.py        # Validation utilities
│   ├── helpers.py           # Helper functions
│   └── __init__.py
│
├── outputs/
│   ├── resumes/             # Generated JSON resumes
│   ├── latex/               # Generated LaTeX files
│   └── pdfs/                # Generated PDFs
│
├── main.py                  # Entry point
├── requirements.txt         # Dependencies
├── .env.example            # Environment template
├── ARCHITECTURE.md         # Detailed architecture
└── README.md              # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Anthropic API key (for Claude)
- OpenAI API key (optional, for GPT-4)

### Installation

1. **Clone the repository**

   ```bash
   cd ResumeBuilderAI
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   ```bash
   # Copy the example
   cp .env.example .env

   # Edit .env with your API keys
   # ANTHROPIC_API_KEY=your_key_here
   # OPENAI_API_KEY=your_key_here
   ```

### Quick Start

```python
from main import run_resume_builder

# With sample data (for testing)
result = run_resume_builder(
    job_description="",
    personal_info={},
    use_sample=True
)

# With custom data
result = run_resume_builder(
    job_description="Your job description",
    personal_info={
        "name": "Your Name",
        "email": "your@email.com",
        "phone": "+1 (XXX) XXX-XXXX",
        "experience": [...],
        "skills": {...},
        "education": [...]
    }
)
```

## 📊 How It Works

### Iteration Flow

Each iteration follows this sequence:

1. **Content Generation**: Create optimized resume content
2. **LaTeX Creation**: Generate professional LaTeX code
3. **Parallel Validation**:
   - ATS Compatibility Check
   - PDF Quality Assessment
4. **Decision Making**: Evaluate all standards
5. **Feedback/Finalization**: Iterate or output

### Example Iteration

```
Iteration 1:
├─ Content Generated (professional summary, skills, experience)
├─ LaTeX Code Generated (valid, ATS-formatted)
├─ ATS Score: 75% (Need: 90%)
├─ PDF Quality: 82/100 (Need: 85)
├─ Decision: FAIL - Missing 5% ATS + Quality
└─ Feedback: "Add keywords: Docker, AWS; Improve formatting"
    ↓
Iteration 2:
├─ Content Regenerated (with keywords incorporated)
├─ LaTeX Updated (improved formatting)
├─ ATS Score: 92% ✓
├─ PDF Quality: 87/100 ✓
├─ Decision: PASS ✓ All standards met
└─ Output: Final resume ready
```

## 🔧 Configuration

Edit `config/settings.py`:

```python
# Quality Thresholds
MIN_ATS_SCORE = 0.90  # 90%
PDF_QUALITY_THRESHOLD = 85  # out of 100
KEYWORD_MATCH_THRESHOLD = 0.80  # 80%

# Workflow
MAX_ITERATIONS = 5
ITERATION_TIMEOUT = 120  # seconds

# Models
CONTENT_MODEL = "claude-3-5-sonnet-20241022"
VALIDATION_MODEL = "claude-3-5-haiku-20241022"
```

## 📝 Input Format

### Personal Information

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1 (555) 123-4567",
  "experience": [
    {
      "title": "Senior Developer",
      "company": "Tech Corp",
      "duration": "2020 - Present",
      "description": "Led development of scalable APIs..."
    }
  ],
  "skills": {
    "Programming": ["Python", "JavaScript"],
    "Databases": ["PostgreSQL", "MongoDB"],
    "Tools": ["Docker", "Kubernetes", "AWS"]
  },
  "education": [
    {
      "degree": "BS Computer Science",
      "school": "University Name",
      "year": "2020"
    }
  ]
}
```

## 📤 Output

The system generates:

1. **LaTeX Resume** (`outputs/latex/resume_*.tex`)

   - Production-ready, compilable LaTeX
   - ATS-friendly formatting
   - Professional styling

2. **JSON Resume** (`outputs/resumes/resume_*.json`)

   - Structured resume content
   - Matched keywords
   - Metadata

3. **Execution Report** (`outputs/execution_report_*.json`)
   - Iteration history
   - All validation scores
   - Feedback logs

## 🤖 Agent Details

### Agent 1: Content Generator

- **Model**: Claude 3.5 Sonnet
- **Role**: Create optimized resume content
- **Tools**: Job parser, keyword extractor, experience matcher
- **Output**: Structured JSON resume

### Agent 2: LaTeX Generator

- **Model**: Claude 3.5 Sonnet
- **Role**: Convert content to LaTeX
- **Tools**: LaTeX template, formatter, ATS optimizer
- **Output**: Compilable LaTeX code

### Agent 3: ATS Checker

- **Model**: Claude 3.5 Haiku
- **Role**: Validate ATS compatibility
- **Tools**: Keyword analyzer, score calculator
- **Output**: ATS score (0-100) + keyword report

### Agent 4: PDF Validator

- **Model**: Claude 3.5 Haiku
- **Role**: Assess quality & rendering
- **Tools**: LaTeX validator, structure analyzer, visual scorer
- **Output**: Quality score (0-100) + recommendations

### Agent 5: Feedback Agent

- **Model**: Claude 3.5 Sonnet
- **Role**: Decide pass/fail & generate feedback
- **Tools**: Standard checker, feedback generator
- **Output**: Decision + specific improvements

## 📊 Monitoring & Logging

Logs are saved to `logs/resume_builder_*.log`

Example log output:

```
2025-01-15 10:30:45 - ResumeBuilder - INFO - ============================================================
2025-01-15 10:30:45 - ResumeBuilder - INFO - RESUME BUILDER AI - STARTING EXECUTION
2025-01-15 10:30:45 - ResumeBuilder - INFO - ============================================================
2025-01-15 10:30:46 - ResumeBuilder - INFO - === ITERATION 1: Content Generation ===
2025-01-15 10:30:48 - ResumeBuilder - INFO - ✓ Resume content generated successfully
2025-01-15 10:30:49 - ResumeBuilder - INFO - Generating LaTeX code...
2025-01-15 10:30:52 - ResumeBuilder - INFO - ✓ LaTeX code generated successfully
2025-01-15 10:30:53 - ResumeBuilder - INFO - Checking ATS compatibility...
2025-01-15 10:30:54 - ResumeBuilder - INFO - ✓ ATS Analysis: Score = 78.5%
```

## 🔐 Best Practices

1. **API Key Security**: Never commit `.env` file with real keys
2. **Iteration Limits**: Set reasonable MAX_ITERATIONS to avoid excessive API calls
3. **Error Handling**: Check logs for any failures
4. **Output Organization**: Keep outputs organized for auditing
5. **Feedback Loop**: Review feedback messages to improve prompts

## 🚨 Troubleshooting

### API Key Issues

```
ERROR: ANTHROPIC_API_KEY not set
Solution: Set environment variable or .env file
```

### Max Iterations Reached

```
The workflow hits MAX_ITERATIONS without passing all standards.
Solution: Check logs for feedback, adjust thresholds or improve input quality
```

### LaTeX Compilation Errors

```
LaTeX validation errors in PDF Validator
Solution: Check formatting, remove special characters
```

## 🎓 Learning Resources

- **LangChain Docs**: https://python.langchain.com/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Claude API**: https://docs.anthropic.com/
- **LaTeX Documentation**: https://www.overleaf.com/learn

## 🤝 Contributing

Contributions welcome! Areas for enhancement:

- [ ] PDF rendering and validation
- [ ] More sophisticated ATS scoring
- [ ] Custom LaTeX templates
- [ ] Resume parsing from uploaded PDFs
- [ ] Multiple resume variations
- [ ] LinkedIn integration

## 📄 License

MIT License - See LICENSE file for details

## 🙋 Support

For issues or questions:

1. Check logs in `logs/` directory
2. Review error messages and stack traces
3. Check ARCHITECTURE.md for design details
4. Create an issue with detailed logs

---

**Built with**: LangChain • LangGraph • Claude • Python
**Last Updated**: December 2025
