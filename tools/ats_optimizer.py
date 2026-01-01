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
        """Generate 2-3 line ATS-optimized summary fully derived from JD."""
        # Extract actual experience from personal_info
        experience_list = personal_info.get("experience", [])
        
        # Determine actual experience level
        if len(experience_list) == 0:
            years_exp = "entry-level"
        elif len(experience_list) == 1:
            # Check if intern or junior
            title = experience_list[0].get("title", "").lower()
            if "intern" in title:
                years_exp = "aspiring"
            else:
                years_exp = "1+ years"
        else:
            years_exp = f"{len(experience_list)}+ years"
        
        # Extract top 3 technologies from JD-derived skills
        flat_skills = [s for lst in self.skills_from_jd.values() for s in lst]
        matched_techs = flat_skills[:3] if flat_skills else ["Python", "SQL"]
        
        # Extract key responsibilities from JD for summary
        resp_keywords = []
        if 'ml' in self.domain_context or 'data_science' in self.domain_context:
            ml_keywords = [k for k in ['modeling', 'ml', 'machine learning', 'prediction', 'deployment'] if k in self.jd]
            resp_keywords.extend(ml_keywords[:2])
        if 'analytics' in self.domain_context:
            analytics_keywords = [k for k in ['analytics', 'dashboard', 'reporting', 'visualization'] if k in self.jd]
            resp_keywords.extend(analytics_keywords[:2])
        if 'data_engineering' in self.domain_context:
            de_keywords = [k for k in ['pipeline', 'etl', 'data engineering', 'spark'] if k in self.jd]
            resp_keywords.extend(de_keywords[:2])
        
        # Build domain-specific summary
        if self.domain_context in ['ml', 'data_science']:
            if years_exp == "aspiring":
                summary = f"Aspiring {self.target_role} with hands-on experience in {', '.join(matched_techs)}. Completed projects in model development, experimentation, and deployment. Strong foundation in ML frameworks and statistical methods with proven ability to deliver data-driven solutions."
            elif years_exp == "entry-level":
                summary = f"Entry-level {self.target_role} with practical experience in {', '.join(matched_techs)}. Demonstrated skills through ML projects covering model building, evaluation, and deployment. Eager to contribute to predictive modeling and data science initiatives."
            else:
                summary = f"Impact-focused {self.target_role} with {years_exp} of experience building ML models and data-driven solutions using {', '.join(matched_techs)}. Proven track record in model development, deployment, and cross-functional collaboration. Strong expertise in Python, ML frameworks, and translating business problems into scalable solutions."
        elif self.domain_context == 'analytics':
            if years_exp == "aspiring":
                summary = f"Aspiring {self.target_role} with hands-on experience in {', '.join(matched_techs)}. Completed internship focused on data analysis, reporting, and data quality. Strong foundation in Python, SQL, and modern analytics practices with proven ability to deliver insights for stakeholders."
            elif years_exp == "entry-level":
                summary = f"Entry-level {self.target_role} with strong technical foundation in {', '.join(matched_techs)}. Demonstrated experience through academic and personal analytics projects. Eager to contribute to data quality, reporting, and insight generation."
            else:
                summary = f"Impact-focused {self.target_role} with {years_exp} of expertise in data analysis, modeling, and reporting using {', '.join(matched_techs)}. Proven track record building dashboards, ensuring data accuracy, and delivering stakeholder-ready insights. Strong background in SQL, Python, and modern BI tooling."
        elif self.domain_context == 'data_engineering':
            if years_exp == "aspiring":
                summary = f"Aspiring {self.target_role} with hands-on experience in {', '.join(matched_techs)}. Built data pipelines and ETL workflows in academic and project settings. Strong foundation in Python, SQL, and pipeline orchestration."
            else:
                summary = f"Impact-focused {self.target_role} with {years_exp} of experience designing and building scalable data pipelines using {', '.join(matched_techs)}. Expertise in ETL/ELT, data modeling, and ensuring data quality. Proven ability to deliver reliable infrastructure supporting analytics and ML workflows."
        else:
            # General summary
            if years_exp == "aspiring":
                summary = f"Aspiring {self.target_role} with hands-on experience in {', '.join(matched_techs)}. Strong technical foundation with proven ability to learn quickly and deliver results."
            else:
                summary = f"JD-aligned {self.target_role} with {years_exp} of experience in {', '.join(matched_techs)}. Proven track record of delivering high-quality solutions and collaborating with cross-functional teams."
        
        return summary
    
    def generate_experience_bullets(self, role: Dict[str, Any]) -> List[str]:
        """Generate 4 unique JD-aligned bullets for experience role using actual JD keywords and responsibilities."""
        bullets = []
        title = role.get("title", "").lower()
        
        # Determine role level
        is_intern = "intern" in title
        is_junior = "junior" in title or ("analyst" in title and "senior" not in title)
        is_senior = "senior" in title or "lead" in title
        
        # Extract JD-specific technologies and methods
        jd_tech = [s for lst in self.skills_from_jd.values() for s in lst][:5]
        jd_tech_str = ", ".join(jd_tech[:2]) if jd_tech else "Python and SQL"
        
        # Generate bullets based on domain context and JD content
        if self.domain_context in ['ml', 'data_science']:
            # ML/Data Science focused bullets
            if is_intern:
                bullets.extend([
                    f"Built and evaluated ML models using {jd_tech_str}, achieving 85%+ accuracy on validation datasets for business use cases.",
                    f"Conducted feature engineering and data preprocessing on {self._get_scale_term()} records, improving model performance and reducing overfitting.",
                    f"Collaborated with data engineers and product teams to define modeling requirements and deploy proof-of-concept models.",
                    f"Documented model architecture, hyperparameters, and evaluation metrics, enabling reproducibility and knowledge transfer."
                ])
            elif is_junior or is_senior:
                impact_scale = "10+ models" if is_senior else "5+ models"
                stakeholder_scope = "C-suite and business leaders" if is_senior else "product and analytics teams"
                bullets.extend([
                    f"Designed, prototyped, and deployed {impact_scale} for {self._get_domain_use_cases()}, using {jd_tech_str} to drive measurable business impact.",
                    f"Performed feature engineering, experimentation, and hyperparameter tuning, improving model accuracy by 15-20% and reducing false positives.",
                    f"Collaborated with {stakeholder_scope} to identify high-impact ML opportunities, prioritize use cases, and translate business problems into technical solutions.",
                    f"Established MLOps best practices including model monitoring, versioning, and A/B testing, ensuring production reliability and continuous improvement."
                ])
            else:
                bullets.extend([
                    f"Developed predictive models using {jd_tech_str} to support {self._get_domain_use_cases()}, achieving measurable improvements in business KPIs.",
                    f"Conducted exploratory data analysis and feature engineering on large datasets, uncovering actionable insights and improving model performance.",
                    f"Collaborated with engineering and product teams to deploy models to production, ensuring scalability and monitoring.",
                    f"Documented modeling methodology, results, and recommendations, enabling data-driven decision-making across the organization."
                ])
        
        elif self.domain_context == 'analytics':
            # Analytics focused bullets
            if is_intern:
                bullets.extend([
                    f"Cleaned and validated datasets using {jd_tech_str}, improving data accuracy by 25% for core reporting dashboards.",
                    f"Conducted exploratory analyses on {self._get_scale_term()} records to identify operational trends and cost-saving anomalies, sharing weekly insights with stakeholders.",
                    f"Built {self._get_dashboard_count()} interactive dashboards tracking KPIs across sales, operations, and marketing functions.",
                    f"Automated data quality checks reducing manual validation time by 30% and improving dashboard refresh reliability."
                ])
            else:
                impact_scale = "15+ dashboards" if is_senior else "8+ dashboards"
                stakeholder_scope = "executive leadership" if is_senior else "department stakeholders"
                bullets.extend([
                    f"Designed and built {impact_scale} using {jd_tech_str}, delivering real-time insights to {stakeholder_scope} and supporting data-driven decisions.",
                    f"Wrote and optimized {self._get_query_count()} SQL queries and data models, improving query performance by 35% and enabling self-service analytics.",
                    f"Collaborated with business teams to define metrics, identify trends, and deliver on-time analytics solutions aligned to strategic initiatives.",
                    f"Established data quality frameworks and automated validation pipelines, reducing reporting errors by 60% and earning stakeholder trust."
                ])
        
        elif self.domain_context == 'data_engineering':
            # Data Engineering focused bullets
            if is_intern:
                bullets.extend([
                    f"Built data ingestion pipelines using {jd_tech_str}, processing {self._get_scale_term()} records daily with 99%+ uptime.",
                    f"Implemented data validation and quality checks, reducing data loss incidents and improving downstream analytics reliability.",
                    f"Collaborated with analytics and ML teams to understand data requirements and optimize pipeline performance.",
                    f"Documented pipeline architecture and deployment procedures, enabling team reproducibility and maintenance."
                ])
            else:
                scale = "10M+ daily records" if is_senior else "1M+ daily records"
                bullets.extend([
                    f"Designed and deployed end-to-end data pipelines using {jd_tech_str}, ingesting and transforming {scale} with 99.5%+ uptime and SLA compliance.",
                    f"Optimized ETL workflows and data models, reducing pipeline execution time by 45% and cutting infrastructure costs by 20%.",
                    f"Collaborated with ML and analytics teams to improve data collection, schema design, and modeling signals, enabling high-quality downstream use cases.",
                    f"Implemented comprehensive monitoring, alerting, and error handling, reducing incidents by 70% and ensuring data reliability."
                ])
        
        else:
            # General/Backend focused bullets
            if is_intern:
                bullets.extend([
                    f"Developed backend features and APIs using {jd_tech_str}, supporting core product functionality and user workflows.",
                    f"Wrote unit and integration tests achieving 90%+ coverage, ensuring code quality and reducing production bugs.",
                    f"Collaborated with frontend and product teams to define requirements, implement features, and deliver on sprint commitments.",
                    f"Participated in code reviews and pair programming sessions, contributing to team knowledge sharing and best practices."
                ])
            else:
                bullets.extend([
                    f"Designed and implemented scalable backend services using {jd_tech_str}, supporting {self._get_scale_term()} users with 99.9% uptime.",
                    f"Optimized API performance and database queries, reducing latency by 40% and improving user experience.",
                    f"Collaborated with cross-functional teams to architect solutions, define technical roadmaps, and deliver high-impact features.",
                    f"Mentored junior developers through code reviews, pair programming, and technical guidance, fostering a culture of excellence."
                ])
        
        return bullets[:4]  # Return exactly 4 unique bullets
    
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
    
    def generate_project_bullets(self, project: Dict[str, Any]) -> List[str]:
        """Generate 3 unique, JD-aligned bullets dynamically based on project characteristics and JD requirements."""
        bullets = []
        project_name = project.get("name", "Project")
        project_name_lower = project_name.lower()
        technologies = project.get("technologies", [])
        
        # Identify project domain from technologies
        has_ml = any(t.lower() in ['tensorflow', 'keras', 'pytorch', 'scikit-learn', 'xgboost', 'lightgbm'] for t in technologies)
        has_cv = any(t.lower() in ['opencv', 'cv2', 'computer vision'] for t in technologies)
        has_sql = any(t.lower() in ['sql', 'postgresql', 'mysql', 'sqlite'] for t in technologies)
        has_bi = any(t.lower() in ['tableau', 'power bi', 'looker', 'superset', 'dax'] for t in technologies)
        has_java = any(t.lower() in ['java', 'spring', 'spring boot', 'hibernate', 'jpa', 'j2ee'] for t in technologies)
        has_python = any(t.lower() in ['python', 'fastapi', 'flask', 'django', 'pydantic'] for t in technologies)
        has_de = any(t.lower() in ['spark', 'airflow', 'kafka', 'etl'] for t in technologies)
        has_cloud = any(t.lower() in ['aws', 'azure', 'gcp', 'docker', 'kubernetes'] for t in technologies)
        
        # Get JD-relevant technologies (intersection of project tech and JD mentions)
        proj_jd_overlap = [t for t in technologies if re.search(r'\b' + re.escape(t.lower()) + r'\b', self.jd)]
        primary_tech = ', '.join(proj_jd_overlap[:2]) if proj_jd_overlap else ', '.join(technologies[:2])
        
        # Extract project purpose from name keywords
        is_microservices = any(kw in project_name_lower for kw in ['microservice', 'micro-service', 'distributed'])
        is_ecommerce = any(kw in project_name_lower for kw in ['ecommerce', 'e-commerce', 'shop', 'store', 'retail'])
        is_management = any(kw in project_name_lower for kw in ['management', 'admin', 'crm', 'erp'])
        is_analytics = any(kw in project_name_lower for kw in ['analytics', 'dashboard', 'reporting', 'insights', 'bi'])
        is_pipeline = any(kw in project_name_lower for kw in ['pipeline', 'etl', 'data processing', 'ingestion'])
        
        # Get JD priorities from keywords and domain context
        jd_mentions_api = any(kw in self.jd for kw in ['api', 'rest', 'restful', 'endpoint'])
        jd_mentions_scale = any(kw in self.jd for kw in ['scalable', 'scale', 'performance', 'optimize'])
        jd_mentions_testing = any(kw in self.jd for kw in ['test', 'testing', 'quality'])
        jd_mentions_architecture = any(kw in self.jd for kw in ['architect', 'design', 'system design'])
        
        # Generate bullets based on project type and JD alignment
        if has_ml or has_cv:
            # ML/CV Project
            model_type = "computer vision" if has_cv else "machine learning"
            ml_libs = [t for t in technologies if t.lower() in ['tensorflow', 'keras', 'pytorch', 'opencv', 'scikit-learn', 'xgboost', 'lightgbm']]
            bullets.append(f"Developed {model_type} model using {', '.join(ml_libs[:2]) if ml_libs else primary_tech}, achieving 88% accuracy through iterative training, hyperparameter tuning, and cross-validation.")
            bullets.append(f"Engineered data preprocessing and feature extraction pipeline processing 5000+ samples, improving model performance and generalization across test cases.")
            bullets.append(f"Implemented model evaluation framework with performance metrics (precision, recall, F1-score), enabling data-driven optimization and deployment readiness.")
        
        elif has_bi or is_analytics:
            # Analytics/BI Project
            bi_tech = next((t for t in technologies if t.lower() in ['tableau', 'power bi', 'looker', 'superset']), None)
            bullets.append(f"Designed interactive analytics dashboard using {bi_tech or primary_tech} with 10+ visualizations and KPI tracking, enabling data-driven decision making.")
            if has_sql:
                bullets.append(f"Built optimized SQL queries with joins, aggregations, and window functions, supporting real-time data retrieval and metric calculations.")
            else:
                bullets.append(f"Implemented data aggregation and transformation logic, processing 100K+ records with sub-second response times.")
            bullets.append(f"Established automated data refresh workflows and quality validation checks, ensuring accuracy and reliability of insights.")
        
        elif is_pipeline or has_de:
            # Data Pipeline/ETL Project
            bullets.append(f"Engineered end-to-end data pipeline using {primary_tech}, processing and transforming 1M+ daily records with automated error handling and retry logic.")
            bullets.append(f"Implemented data validation, quality checks, and monitoring alerts, reducing data inconsistencies by 90% and improving reliability.")
            bullets.append(f"Optimized pipeline execution through batch processing and parallel operations, reducing runtime by 40% and infrastructure costs.")
        
        elif is_microservices and (has_java or has_python):
            # Microservices Architecture Project
            framework = next((t for t in technologies if t.lower() in ['spring boot', 'spring', 'fastapi', 'flask']), technologies[0])
            bullets.append(f"Architected and implemented microservices using {framework}, enabling independent service deployment, scaling, and fault isolation.")
            if jd_mentions_api or 'api' in self.jd:
                bullets.append(f"Designed RESTful APIs with standardized request/response formats, authentication, and error handling, supporting high-throughput operations.")
            else:
                bullets.append(f"Built service-to-service communication with message queues and event-driven patterns, ensuring loose coupling and resilience.")
            if is_ecommerce:
                bullets.append(f"Integrated payment processing, inventory management, and order fulfillment services with comprehensive transaction handling and rollback mechanisms.")
            else:
                bullets.append(f"Implemented distributed tracing, centralized logging, and health monitoring, enabling observability across microservices ecosystem.")
        
        elif (has_java or has_python) and (is_management or 'management' in project_name_lower):
            # Management System Project
            framework = next((t for t in technologies if t.lower() in ['spring boot', 'spring', 'django', 'flask', 'fastapi']), technologies[0])
            entity_type = "employee" if "employee" in project_name_lower else "resource"
            bullets.append(f"Built {entity_type} management system using {framework}, implementing CRUD operations, role-based access control, and audit logging.")
            if 'hibernate' in [t.lower() for t in technologies] or 'jpa' in [t.lower() for t in technologies]:
                bullets.append(f"Designed normalized database schema with entity relationships and ORM mappings, optimizing query performance and data integrity.")
            else:
                bullets.append(f"Designed relational database schema with normalized tables, foreign keys, and indexing for efficient data operations.")
            if jd_mentions_api:
                bullets.append(f"Developed RESTful API endpoints with input validation, exception handling, and JSON serialization for seamless frontend integration.")
            else:
                bullets.append(f"Implemented business logic layer with transaction management, validation rules, and comprehensive error handling.")
        
        elif has_java or has_python:
            # Generic Backend Project
            framework = next((t for t in technologies if t.lower() in ['spring boot', 'spring', 'fastapi', 'django', 'flask']), primary_tech)
            bullets.append(f"Developed backend application using {framework}, implementing layered architecture with separation of concerns and maintainable code structure.")
            if jd_mentions_api or 'rest' in self.jd or 'api' in self.jd:
                bullets.append(f"Built RESTful API endpoints with request validation, error handling, and response serialization, ensuring robust service layer.")
            else:
                bullets.append(f"Implemented core business logic with modular design, dependency injection, and reusable components.")
            if jd_mentions_testing:
                bullets.append(f"Developed comprehensive test suite with unit and integration tests, achieving 90%+ coverage and ensuring code quality.")
            else:
                bullets.append(f"Integrated database layer with ORM/query builders, implementing efficient data access patterns and transaction management.")
        
        else:
            # Generic fallback - use project name context
            bullets.append(f"Developed {project_name} using {primary_tech}, implementing core functionality with clean code architecture and best practices.")
            if jd_mentions_testing or 'quality' in self.jd:
                bullets.append(f"Built comprehensive testing framework with unit and integration tests, ensuring 95%+ reliability and edge case coverage.")
            else:
                bullets.append(f"Implemented robust error handling, validation, and logging mechanisms, ensuring system stability and debuggability.")
            bullets.append(f"Documented system architecture, API specifications, and deployment workflows, enabling team collaboration and knowledge transfer.")
        
        return bullets[:3]  # Return exactly 3 unique bullets
    
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

    def get_award_cert_description(self, entry: Dict[str, Any], target_role: str = None) -> str:
        """Create a unique, JD-aligned description for awards/certifications based on actual JD requirements."""
        if target_role is None:
            target_role = self.target_role
        
        entry_type = entry.get("type", "").lower()
        cert_name = entry.get("name", "").lower()
        
        # Get top 3 JD skills for this specific JD
        jd_skills = [s for lst in self.skills_from_jd.values() for s in lst][:3]
        jd_skills_str = ", ".join(jd_skills) if jd_skills else "role-critical skills"
        
        # Domain-specific certification descriptions aligned to current JD
        if "google data analytics" in cert_name:
            if self.domain_context in ['ml', 'data_science']:
                return "Completed data analytics certification covering SQL, Python, visualization, and statistical analysis—foundational for feature engineering and EDA."
            elif self.domain_context == 'analytics':
                return "Completed Google's analytics curriculum covering data cleaning, SQL, visualization, dashboards, and stakeholder communication—directly applicable to role requirements."
            else:
                return "Earned certification demonstrating proficiency in SQL, data cleaning, visualization, and analytical thinking relevant to the role."
        
        if "sql" in cert_name and "hackerrank" in cert_name:
            if self.domain_context in ['ml', 'data_science']:
                return "Validated advanced SQL: complex joins, window functions, and optimization—critical for feature engineering and training pipelines."
            elif self.domain_context == 'data_engineering':
                return "Demonstrated expert SQL for data modeling, indexing, and performance tuning—core for reliable pipelines and downstream models."
            else:
                return "Validated advanced SQL including complex queries and optimization—core for analytics and reporting reliability."
        
        if "machine learning" in cert_name or "ml" in cert_name or "ai" in cert_name:
            return "Completed ML certification covering model development, evaluation, deployment, and MLOps—aligned to predictive modeling responsibilities."
        
        if "aws certified developer" in cert_name or ("aws" in cert_name and "developer" in cert_name):
            return "Validated ability to build and deploy services on AWS with CI/CD, monitoring, and secure API practices—supporting production-grade delivery."
        if "aws" in cert_name or "cloud" in cert_name:
            return "Validated cloud expertise for deploying scalable services and data workloads with reliability and security controls."
        
        if "oracle" in cert_name and "java" in cert_name:
            return "Validated Java SE proficiency including core language, OOP, collections, concurrency, and JVM best practices for production services."
        if "java" in cert_name:
            return "Demonstrated strong Java development skills across OOP, collections, exception handling, and performance-conscious coding."
        
        if "tableau" in cert_name or "power bi" in cert_name:
            return "Demonstrated proficiency in dashboard design, data visualization, and storytelling—key for communicating insights to stakeholders."
        
        if "python" in cert_name:
            if self.domain_context in ['ml', 'data_science']:
                return "Completed Python certification covering Pandas, NumPy, and ML libraries—fundamentals for data manipulation and model development."
            else:
                return "Validated Python proficiency for scripting, data processing, and automation supporting role responsibilities."
        
        # Fallback: generic JD-aligned description
        if entry_type == "award":
            return f"Recognized for outstanding achievement aligned to {target_role}, demonstrating impact in {jd_skills_str}."
        else:
            return f"Certification validates core competencies in {jd_skills_str} essential for {target_role} responsibilities."


__all__ = ["ATSOptimizer"]
