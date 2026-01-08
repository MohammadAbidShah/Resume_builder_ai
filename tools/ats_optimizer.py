"""ATS Optimizer: Generate JD-aligned, keyword-optimized resume content."""
import re
from typing import Dict, List, Any, Set
from utils.logger import logger


def normalize_text(text: str) -> str:
    """Normalize text for domain detection."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def detect_primary_domain(jd_text: str, domain_keywords: dict) -> str:
    """Detect primary domain from JD using normalized scoring."""
    jd_text = normalize_text(jd_text)

    domain_scores = {}

    for domain, keywords in domain_keywords.items():
        matched = sum(
            1 for kw in keywords
            if kw.lower() in jd_text
        )

        if matched > 0:
            # Normalize by domain size to avoid bias
            domain_scores[domain] = matched / len(keywords)

    if not domain_scores:
        return 'general'

    primary_domain, best_score = max(
        domain_scores.items(),
        key=lambda x: x[1]
    )

    # Confidence threshold to avoid weak matches
    if best_score < 0.08:
        return 'general'

    return primary_domain


class ATSOptimizer:
    """Analyzes JD and generates ATS-optimized resume content."""
    
    def __init__(self, job_description: str):
        """Initialize with job description."""
        self.jd = normalize_text(job_description)
        self.jd_original = job_description
        self.keywords = self._extract_keywords()
        self.skills_from_jd = self._extract_skills()
        self.target_role = self._extract_target_role()
        self.key_responsibilities = self._extract_responsibilities()
        self.domain_context = self._extract_domain_context()
        logger.info(f"ATS Optimizer: Extracted {len(self.keywords)} JD keywords")
        logger.info(f"ATS Optimizer: Target role = {self.target_role}")
        logger.info(f"ATS Optimizer: Domain context = {self.domain_context}")
    
    def _extract_keywords(self) -> Set[str]:
        """Extract technical and business keywords from JD dynamically."""
        # Expanded tech terms covering ML, data science, analytics, backend
        tech_terms = {
            'python', 'r', 'java', 'scala', 'javascript', 'typescript', 'bash',
            'react', 'react.js', 'reactjs', 'redux', 'redux toolkit', 'zustand',
            'next.js', 'nextjs', 'vue', 'vue.js', 'vuejs', 'nuxt', 'angular',
            'svelte', 'sveltekit', 'astro', 'lit', 'web components',
            'css', 'css3', 'scss', 'sass', 'less', 'tailwind', 'bootstrap',
            'html', 'html5', 'semantic html', 'aria', 'accessibility', 'a11y',
            'core web vitals', 'lighthouse', 'performance optimization', 'bundle size',
            'webpack', 'vite', 'rollup', 'parcel', 'babel',
            'storybook', 'design system', 'component library',
            'responsive design', 'cross browser', 'testing library', 'jest', 'cypress',
            'rest', 'restful', 'graphql', 'apis',
            'oop', 'functional programming', 'data structures', 'algorithms',
            'pandas', 'numpy', 'scipy', 'statsmodels', 'polars',
            'data cleaning', 'data wrangling', 'data preprocessing',
            'sql', 'nosql', 'database', 'data warehouse', 'data lake',
            'postgresql', 'mysql', 'sqlite', 'oracle', 'sql server',
            'mongodb', 'cassandra', 'dynamodb', 'redis', 'elasticsearch',
            'tableau', 'power bi', 'excel', 'looker', 'superset',
            'matplotlib', 'seaborn', 'plotly', 'dash',
            'dashboard', 'reporting', 'data visualization', 'business intelligence', 'bi',
            'fastapi', 'django', 'flask', 'spring boot',
            'rest', 'restful', 'api', 'apis', 'grpc', 'graphql',
            'microservices', 'monolith', 'backend development',
            'aws', 'gcp', 'azure',
            'ec2', 's3', 'lambda', 'cloud functions',
            'docker', 'kubernetes', 'helm', 'terraform',
            'ci/cd', 'github actions', 'gitlab ci', 'jenkins',
            'spark', 'pyspark', 'hadoop', 'hive',
            'kafka', 'flink', 'streaming', 'real-time processing',
            'etl', 'elt', 'pipeline', 'data pipeline',
            'airflow', 'dbt', 'prefect', 'dag',
            'data modeling', 'schema design', 'normalization',
            'machine learning', 'ml', 'artificial intelligence', 'ai',
            'supervised learning', 'unsupervised learning', 'reinforcement learning',
            'deep learning', 'neural networks',
            'tensorflow', 'pytorch', 'keras',
            'scikit-learn', 'xgboost', 'lightgbm', 'catboost',
            'feature engineering', 'feature selection',
            'model training', 'model evaluation', 'model deployment',
            'hyperparameter tuning', 'cross validation',
            'overfitting', 'underfitting',
            'mlops', 'model monitoring', 'drift detection',
            'statistics', 'probability', 'hypothesis testing',
            'a/b testing', 'experimentation',
            'regression', 'classification', 'clustering',
            'forecasting', 'time series', 'trend analysis',
            'credit risk', 'fraud detection', 'churn prediction',
            'customer segmentation', 'recommendation system',
            'demand forecasting', 'anomaly detection',
            'performance tuning', 'optimization', 'scalability',
            'latency', 'throughput', 'fault tolerance', 'high availability',
            'prototype', 'poc', 'deploy', 'release',
            'monitoring', 'logging', 'observability',
            'version control', 'git'
        }

        # Business/soft keywords
        business_terms = {
            'stakeholder', 'stakeholder management',
            'business', 'business requirements',
            'communication', 'presentation', 'documentation',
            'storytelling', 'data storytelling',
            'leadership', 'ownership', 'accountability',
            'mentoring', 'coaching', 'code review',
            'knowledge sharing', 'team building',
            'collaboration', 'collaborate',
            'cross-functional', 'interdisciplinary',
            'agile', 'scrum', 'kanban',
            'sprint', 'standup', 'retrospective',
            'insight', 'insights',
            'decision making', 'data-driven decisions',
            'strategic thinking', 'strategy',
            'roadmap', 'vision', 'planning',
            'impact', 'value creation', 'business impact',
            'efficiency', 'productivity',
            'cost reduction', 'revenue growth',
            'optimization', 'scalability',
            'integrity', 'accuracy', 'data quality',
            'governance', 'compliance',
            'security', 'privacy',
            'culture', 'ownership mindset',
            'continuous improvement',
            'problem solving', 'critical thinking',
            'analytical thinking', 'innovation'
        }

        # Extract from JD using word boundary matching to avoid false positives
        keywords = set()

# Technical terms (no cap)
        for term in tech_terms:
            pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
            if re.search(pattern, self.jd):
                keywords.add(term)

        # Business / soft terms (capped)
        for term in business_terms:
            pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
            if re.search(pattern, self.jd):
                if len(keywords) < 60:
                    keywords.add(term)

        return keywords

    
    def _extract_target_role(self) -> str:
        """Extract target role/title from JD."""
        # Common role patterns
        role_patterns = [
            r'hiring (?:a|an) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
            r'seeking (?:a|an) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
            r'looking for (?:a|an) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?: [A-Z][a-z]+)*) position',
            r'role: ([A-Z][a-z]+(?: [A-Z][a-z]+)*)'
        ]
        
        for pattern in role_patterns:
            match = re.search(pattern, self.jd_original)
            if match:
                return match.group(1)
        
        # Fallback: look for common role titles
        common_roles = [
            'Data Analyst',
            'Senior Data Analyst',
            'Business Data Analyst',
            'BI Analyst',
            'Business Intelligence Analyst',
            'Reporting Analyst',
            'Product Analyst',
            'Operations Analyst',
            'Analytics Engineer',

            'Frontend Developer', 'Front-End Developer', 'Front End Developer',
            'Senior Frontend Developer', 'Senior Front-End Developer',
            'Frontend Engineer', 'Front-End Engineer', 'UI Engineer', 'React Developer',
            'Senior UI Engineer', 'Software Engineer, Frontend',

            'Data Scientist',
            'Senior Data Scientist',
            'Applied Data Scientist',
            'Research Data Scientist',
            'Decision Scientist',
            'Quantitative Analyst',

            'Machine Learning Engineer',
            'ML Engineer',
            'Senior Machine Learning Engineer',
            'AI Engineer',
            'Applied Machine Learning Engineer',
            'Deep Learning Engineer',
            'MLOps Engineer',

            'Data Engineer',
            'Senior Data Engineer',
            'Analytics Engineer',
            'Big Data Engineer',
            'ETL Developer',
            'Data Platform Engineer',

            'Backend Engineer',
            'Senior Backend Engineer',
            'Software Engineer',
            'Senior Software Engineer',
            'Python Developer',
            'Senior Python Developer',
            'Java Developer',
            'Full Stack Developer',
            'Senior Full Stack Developer',

            'Cloud Engineer',
            'Cloud Data Engineer',
            'Platform Engineer',
            'Infrastructure Engineer',
            'DevOps Engineer',

            'Technical Lead',
            'Engineering Lead',
            'Solutions Architect',
            'Data Architect',
            'ML Architect',

            'Product Engineer',
            'Technical Product Manager',
            'Data Product Manager',

            'Research Engineer',
            'AI Research Engineer',
            'Applied Research Scientist'
        ]

        for role in common_roles:
            if role.lower() in self.jd:
                return role
        
        return "Data Professional"
    
    def _extract_responsibilities(self) -> List[str]:
        """Extract key responsibilities from JD."""
        responsibilities = []
        
        # Look for responsibility indicators
        resp_section = ""
        if "responsibilities include" in self.jd:
            resp_section = self.jd.split("responsibilities include")[1].split("requirements")[0]
        elif "responsibilities:" in self.jd:
            resp_section = self.jd.split("responsibilities:")[1].split("requirements")[0]
        elif "you will" in self.jd:
            resp_section = self.jd.split("you will")[1].split("requirements")[0]
        
        # Extract individual responsibilities (split by commas, "and", periods)
        if resp_section:
            # Split by common delimiters
            resp_items = re.split(r'[,;]|\sand\s', resp_section)
            responsibilities = [r.strip() for r in resp_items if len(r.strip()) > 20][:5]
        
        return responsibilities
    
    def _extract_domain_context(self) -> str:
        """Determine the domain/industry context from JD using normalized scoring."""
        domain_keywords = {
            'ml': [
                'machine learning', 'ml', 'artificial intelligence', 'ai',
                'supervised learning', 'unsupervised learning', 'deep learning',
                'model', 'modeling', 'model training', 'model evaluation',
                'feature engineering', 'feature selection',
                'scikit-learn', 'xgboost', 'lightgbm', 'catboost',
                'tensorflow', 'pytorch', 'keras',
                'mlops', 'model deployment', 'model monitoring', 'drift detection'
            ],

            'data_science': [
                'data science', 'data scientist',
                'predictive modeling', 'forecasting', 'time series',
                'regression', 'classification', 'clustering',
                'statistics', 'probability', 'hypothesis testing',
                'experimentation', 'a/b testing',
                'credit risk', 'fraud detection', 'churn prediction',
                'customer segmentation', 'recommendation system',
                'decision making', 'data-driven decisions'
            ],

            'analytics': [
                'analytics', 'data analytics', 'business analytics',
                'dashboard', 'reporting', 'data visualization',
                'tableau', 'power bi', 'excel', 'looker', 'superset',
                'business intelligence', 'bi',
                'insights', 'data storytelling',
                'kpi', 'metrics', 'trend analysis',
                'stakeholder communication'
            ],

            'data_engineering': [
                'data engineering', 'data engineer',
                'etl', 'elt', 'data pipeline', 'pipeline',
                'airflow', 'dbt', 'prefect',
                'spark', 'pyspark', 'hadoop', 'kafka',
                'streaming', 'real-time processing',
                'data modeling', 'schema design',
                'data warehouse', 'data lake',
                'sql', 'nosql'
            ],

            'backend': [
                'backend', 'backend development',
                'software engineering',
                'api', 'apis', 'rest', 'restful',
                'fastapi', 'django', 'flask', 'spring boot',
                'microservices', 'monolith',
                'grpc', 'graphql',
                'performance optimization', 'latency',
                'scalability', 'high availability',
                'docker', 'kubernetes'
            ],

            'frontend': [
                'frontend', 'front-end', 'ui engineer', 'web developer',
                'react', 'react.js', 'reactjs', 'next.js', 'nextjs',
                'vue', 'vue.js', 'vuejs', 'nuxt', 'angular', 'svelte', 'astro',
                'javascript', 'typescript', 'css', 'css3', 'sass', 'scss', 'tailwind', 'bootstrap',
                'html', 'html5', 'semantic html', 'aria', 'accessibility', 'a11y',
                'design system', 'component library', 'storybook',
                'responsive', 'cross browser', 'core web vitals', 'lighthouse', 'performance', 'bundle size',
                'webpack', 'vite', 'rollup', 'parcel'
            ],

            'cloud': [
                'cloud computing', 'cloud engineer',
                'aws', 'gcp', 'azure',
                'ec2', 's3', 'lambda',
                'docker', 'kubernetes', 'helm', 'terraform',
                'ci/cd', 'github actions', 'jenkins',
                'monitoring', 'logging', 'observability'
            ],

            'fintech': [
                'fintech', 'financial services',
                'credit', 'credit risk', 'lending',
                'fraud', 'fraud detection',
                'payments', 'banking',
                'risk modeling', 'compliance',
                'regulatory', 'data governance'
            ],

            'business_strategy': [
                'stakeholder management',
                'business requirements',
                'strategy', 'strategic thinking',
                'roadmap', 'vision',
                'decision making',
                'business impact', 'value creation',
                'cross-functional collaboration',
                'leadership', 'mentoring',
                'communication', 'presentation'
            ]
        }

        # Use new domain detection logic with normalized scoring
        primary_domain = detect_primary_domain(self.jd_original, domain_keywords)
        
        # Lock domain if JD strongly matches analytics / ML / DE
        if primary_domain == 'general':
            if any(k in self.jd for k in ['dashboard', 'reporting', 'kpi']):
                return 'analytics'
            if any(k in self.jd for k in ['model', 'ml', 'machine learning']):
                return 'ml'
            if any(k in self.jd for k in ['pipeline', 'etl', 'spark']):
                return 'data_engineering'
        
        return primary_domain
    
    def _extract_skills(self) -> Dict[str, List[str]]:
        """Extract and group skills mentioned in JD dynamically."""
        # Define comprehensive skill patterns
        skill_patterns = {
            'Programming Languages': [
                'python', 'r', 'java', 'scala', 'javascript', 'typescript', 'bash'
            ],

            'Data Analysis & Libraries': [
                'pandas', 'numpy', 'scipy', 'statsmodels',
                'data cleaning', 'data wrangling', 'data preprocessing',
                'excel', 'data quality'
            ],

            'Machine Learning & AI': [
                'machine learning', 'ml', 'artificial intelligence', 'ai',
                'supervised learning', 'unsupervised learning', 'deep learning',
                'scikit-learn', 'xgboost', 'lightgbm', 'catboost',
                'tensorflow', 'pytorch', 'keras',
                'feature engineering', 'feature selection',
                'model training', 'model evaluation', 'model deployment',
                'mlops', 'model monitoring'
            ],

            'Statistics & Analytical Methods': [
                'statistics', 'probability', 'hypothesis testing',
                'regression', 'classification', 'clustering',
                'forecasting', 'time series',
                'a/b testing', 'experimentation',
                'trend analysis', 'insights'
            ],

            'Analytics & BI': [
                'data analytics', 'business analytics',
                'tableau', 'power bi', 'looker', 'superset',
                'dashboard', 'reporting',
                'data visualization', 'business intelligence', 'bi',
                'kpi', 'metrics', 'data storytelling'
            ],

            'Data Engineering': [
                'data engineering', 'etl', 'elt',
                'data pipeline', 'pipeline',
                'airflow', 'dbt', 'prefect',
                'spark', 'pyspark', 'hadoop',
                'kafka', 'streaming', 'real-time processing',
                'data modeling', 'schema design',
                'data warehouse', 'data lake'
            ],

            'Backend & Software Engineering': [
                'backend development', 'software engineering',
                'api', 'apis', 'rest', 'restful',
                'fastapi', 'django', 'flask', 'spring boot',
                'microservices', 'monolith',
                'grpc', 'graphql',
                'performance optimization', 'latency',
                'scalability', 'high availability'
            ],

            'Databases & Storage': [
                'sql', 'nosql',
                'postgresql', 'mysql', 'sqlite',
                'mongodb', 'cassandra', 'dynamodb',
                'redis', 'elasticsearch'
            ],

            'Cloud & DevOps': [
                'cloud computing',
                'aws', 'gcp', 'azure',
                'ec2', 's3', 'lambda',
                'docker', 'kubernetes', 'helm', 'terraform',
                'ci/cd', 'github actions', 'jenkins',
                'monitoring', 'logging', 'observability'
            ],

            'Domain & Business Expertise': [
                'fintech', 'financial services',
                'credit risk', 'fraud detection',
                'churn prediction', 'customer segmentation',
                'recommendation systems',
                'risk modeling', 'compliance', 'regulatory'
            ],

            'Business & Product Skills': [
                'stakeholder management',
                'business requirements',
                'decision making', 'data-driven decisions',
                'strategic thinking', 'roadmap', 'vision',
                'business impact', 'value creation'
            ],

            'Soft Skills & Leadership': [
                'communication', 'presentation',
                'cross-functional collaboration',
                'leadership', 'ownership',
                'mentoring', 'coaching',
                'problem solving', 'critical thinking',
                'analytical thinking', 'innovation'
            ]
        }

        
        # Comprehensive proper capitalization
        proper_caps = {
            'python': 'Python',
            'sql': 'SQL',
            'r': 'R',
            'java': 'Java',
            'scala': 'Scala',
            'javascript': 'JavaScript',
            'typescript': 'TypeScript',
            'bash': 'Bash',

            'pandas': 'Pandas',
            'numpy': 'NumPy',
            'scipy': 'SciPy',
            'statsmodels': 'Statsmodels',
            'polars': 'Polars',
            'excel': 'Excel',
            'data cleaning': 'Data Cleaning',
            'data wrangling': 'Data Wrangling',
            'data preprocessing': 'Data Preprocessing',
            'data quality': 'Data Quality',

            'machine learning': 'Machine Learning',
            'ml': 'ML',
            'artificial intelligence': 'Artificial Intelligence',
            'ai': 'AI',
            'supervised learning': 'Supervised Learning',
            'unsupervised learning': 'Unsupervised Learning',
            'deep learning': 'Deep Learning',
            'feature engineering': 'Feature Engineering',
            'feature selection': 'Feature Selection',
            'model training': 'Model Training',
            'model evaluation': 'Model Evaluation',
            'model deployment': 'Model Deployment',
            'mlops': 'MLOps',
            'model monitoring': 'Model Monitoring',

            'scikit-learn': 'Scikit-Learn',
            'xgboost': 'XGBoost',
            'lightgbm': 'LightGBM',
            'catboost': 'CatBoost',
            'tensorflow': 'TensorFlow',
            'pytorch': 'PyTorch',
            'keras': 'Keras',

            'statistics': 'Statistics',
            'probability': 'Probability',
            'hypothesis testing': 'Hypothesis Testing',
            'regression': 'Regression',
            'classification': 'Classification',
            'clustering': 'Clustering',
            'forecasting': 'Forecasting',
            'time series': 'Time Series Analysis',
            'a/b testing': 'A/B Testing',
            'experimentation': 'Experimentation',
            'trend analysis': 'Trend Analysis',
            'insights': 'Insights',

            'analytics': 'Analytics',
            'data analytics': 'Data Analytics',
            'business analytics': 'Business Analytics',
            'tableau': 'Tableau',
            'power bi': 'Power BI',
            'looker': 'Looker',
            'superset': 'Apache Superset',
            'dashboard': 'Dashboards',
            'reporting': 'Reporting',
            'data visualization': 'Data Visualization',
            'business intelligence': 'Business Intelligence',
            'bi': 'BI',
            'kpi': 'KPIs',
            'metrics': 'Metrics',
            'data storytelling': 'Data Storytelling',

            'data engineering': 'Data Engineering',
            'etl': 'ETL',
            'elt': 'ELT',
            'pipeline': 'Data Pipelines',
            'data pipeline': 'Data Pipelines',
            'airflow': 'Apache Airflow',
            'dbt': 'dbt',
            'prefect': 'Prefect',
            'spark': 'Apache Spark',
            'pyspark': 'PySpark',
            'hadoop': 'Hadoop',
            'kafka': 'Apache Kafka',
            'streaming': 'Streaming Data',
            'real-time processing': 'Real-Time Processing',
            'data modeling': 'Data Modeling',
            'schema design': 'Schema Design',
            'data warehouse': 'Data Warehouse',
            'data lake': 'Data Lake',

            'backend': 'Backend Development',
            'backend development': 'Backend Development',
            'software engineering': 'Software Engineering',
            'api': 'API',
            'apis': 'APIs',
            'rest': 'REST',
            'restful': 'RESTful APIs',
            'fastapi': 'FastAPI',
            'django': 'Django',
            'flask': 'Flask',
            'spring boot': 'Spring Boot',
            'microservices': 'Microservices',
            'monolith': 'Monolithic Architecture',
            'grpc': 'gRPC',
            'graphql': 'GraphQL',
            'performance optimization': 'Performance Optimization',
            'latency': 'Low Latency Systems',
            'scalability': 'Scalable Systems',
            'high availability': 'High Availability',

            'database': 'Databases',
            'sql database': 'SQL Databases',
            'nosql': 'NoSQL',
            'postgresql': 'PostgreSQL',
            'mysql': 'MySQL',
            'sqlite': 'SQLite',
            'mongodb': 'MongoDB',
            'cassandra': 'Apache Cassandra',
            'dynamodb': 'Amazon DynamoDB',
            'redis': 'Redis',
            'elasticsearch': 'Elasticsearch',

            'cloud computing': 'Cloud Computing',
            'aws': 'AWS',
            'gcp': 'GCP',
            'azure': 'Azure',
            'ec2': 'Amazon EC2',
            's3': 'Amazon S3',
            'lambda': 'AWS Lambda',
            'docker': 'Docker',
            'kubernetes': 'Kubernetes',
            'helm': 'Helm',
            'terraform': 'Terraform',
            'ci/cd': 'CI/CD',
            'github actions': 'GitHub Actions',
            'jenkins': 'Jenkins',
            'monitoring': 'Monitoring',
            'logging': 'Logging',
            'observability': 'Observability',

            'fintech': 'FinTech',
            'financial services': 'Financial Services',
            'credit risk': 'Credit Risk',
            'fraud detection': 'Fraud Detection',
            'churn prediction': 'Churn Prediction',
            'customer segmentation': 'Customer Segmentation',
            'recommendation system': 'Recommendation Systems',
            'risk modeling': 'Risk Modeling',
            'compliance': 'Compliance',
            'regulatory': 'Regulatory Standards',

            'stakeholder': 'Stakeholder Management',
            'stakeholder management': 'Stakeholder Management',
            'business requirements': 'Business Requirements',
            'decision making': 'Decision Making',
            'data-driven decisions': 'Data-Driven Decision Making',
            'strategic thinking': 'Strategic Thinking',
            'strategy': 'Strategy',
            'roadmap': 'Product Roadmap',
            'vision': 'Product Vision',
            'business impact': 'Business Impact',
            'value creation': 'Value Creation',

            'communication': 'Communication',
            'presentation': 'Presentation Skills',
            'cross-functional collaboration': 'Cross-Functional Collaboration',
            'leadership': 'Leadership',
            'ownership': 'Ownership',
            'mentoring': 'Mentoring',
            'coaching': 'Coaching',
            'problem solving': 'Problem Solving',
            'critical thinking': 'Critical Thinking',
            'analytical thinking': 'Analytical Thinking',
            'innovation': 'Innovation'
        }

        
        skills_from_jd = {}
        for category, skill_list in skill_patterns.items():
            matched = []
            for s in skill_list:
                # Use word boundary matching to avoid false positives (e.g., 'r' matching 'developer')
                if re.search(r'\b' + re.escape(s) + r'\b', self.jd):
                    matched.append(proper_caps.get(s, s.title()))
            if matched:
                skills_from_jd[category] = matched
        
        # Deduplicate across categories
        seen = set()
        for category in list(skills_from_jd.keys()):
            unique = []
            for skill in skills_from_jd[category]:
                if skill not in seen:
                    unique.append(skill)
                    seen.add(skill)
            if unique:
                skills_from_jd[category] = unique
            else:
                del skills_from_jd[category]
        
        return skills_from_jd
    
    def generate_summary(self, personal_info: Dict[str, Any]) -> str:
        """Deprecated - summary is now generated by LLM master prompt. Return empty string."""
        logger.warning("ATS Optimizer generate_summary called - this is deprecated. Use LLM master prompt instead.")
        return ""
    
    def generate_experience_bullets(self, role: Dict[str, Any], role_index: int = 0) -> List[str]:
        """Delegate to LLM-generated bullets; no template math."""
        return []
    
    def _get_domain_use_cases(self) -> str:
        """Get domain-specific use cases from JD."""
        if 'credit risk' in self.jd:
            return "credit risk assessment, fraud detection, and customer scoring"
        elif 'fraud' in self.jd:
            return "fraud detection, anomaly identification, and risk scoring"
        elif 'churn' in self.jd:
            return "churn prediction, customer retention, and lifecycle modeling"
        else:
            return "business critical applications"
    
    def _get_scale_term(self) -> str:
        """Get appropriate scale term based on experience level."""
        return "100K+"
    
    def _get_dashboard_count(self) -> str:
        """Get dashboard count."""
        return "5+"
    
    def _get_query_count(self) -> str:
        """Get query count."""
        return "50+"
    
    def generate_project_bullets(self, project: Dict[str, Any], project_index: int = 0) -> List[str]:
        """Delegate to LLM-generated bullets; no template math."""
        return []
    
    def get_skills_grouped(self, personal_skills: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Return JD-only skills to keep narrative fully driven by the job description."""
        return dict(self.skills_from_jd)
    
    def get_certification_line(self, cert: Dict[str, Any]) -> str:
        """Generate 1 ATS-optimized line per certification."""
        cert_name = cert.get("name", "")
        issuer = cert.get("issuer", cert.get("organization", ""))
        date = cert.get("date", cert.get("year", ""))
        
        # Ensure cert mentions relevant keywords
        cert_line = f"{cert_name}"
        if issuer:
            cert_line += f" | {issuer}"
        if date:
            cert_line += f" | {date}"
        
        return cert_line

    def get_award_cert_description(self, entry: Dict[str, Any], target_role: str = None, entry_index: int = 0) -> str:
        """Create a JD-aligned certification/award description dynamically without stored templates."""
        if target_role is None:
            target_role = self.target_role
        
        # Deprecated: LLM provides certification lines; keep empty fallback
        return ""


__all__ = ["ATSOptimizer"]
