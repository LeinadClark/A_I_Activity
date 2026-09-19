"""
Script to generate and validate 6+ CS/IT Syllabus JSON files in syllabi_library/
Conforms strictly to CourseMetadataSchema, Bloom's verbs, and 18-week term rules.
"""

import os
import json
from obe_schemas import (
    CourseMetadataSchema,
    CourseOutcomeSchema,
    WeeklyScheduleSchema,
    LessonOutcomeSchema,
    GradingComponentSchema
)

OUTPUT_DIR = "syllabi_library"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def build_syllabus(course_code, title, desc, prereq, units, cos_data, weeks_data, grading_data):
    cos = [CourseOutcomeSchema(**c) for c in cos_data]
    sched = []
    for (wn, per, top, tla, at, ali, kd, sd, ad) in weeks_data:
        sched.append(WeeklyScheduleSchema(
            week_number=wn,
            period=per,
            topic=top,
            teaching_learning_activity=tla,
            assessment_task=at,
            result_evidence="Lab Portfolio / Technical Output",
            aligned_co=ali,
            lesson_outcomes=[
                LessonOutcomeSchema(category="K", description=kd),
                LessonOutcomeSchema(category="S", description=sd),
                LessonOutcomeSchema(category="A", description=ad)
            ]
        ))
    grading = [GradingComponentSchema(**g) for g in grading_data]

    obj = CourseMetadataSchema(
        course_code=course_code,
        course_title=title,
        course_description=desc,
        credit_units=units,
        prerequisites=prereq,
        course_outcomes=cos,
        weekly_schedule=sched,
        grading_breakdown=grading
    )
    return obj


# ---------------------------------------------------------------------------
# 1. CS 311: Data Mining and Knowledge Discovery
# ---------------------------------------------------------------------------
dm_cos = [
    {"co_number": 1, "bloom_level": "Applying", "co_description": "Apply data cleaning, feature scaling, and preprocessing techniques using Python and Pandas.", "mapped_po": [1, 2]},
    {"co_number": 2, "bloom_level": "Analyzing", "co_description": "Analyze frequent itemsets and generate association rules using Apriori and FP-Growth algorithms.", "mapped_po": [2, 3]},
    {"co_number": 3, "bloom_level": "Evaluating", "co_description": "Evaluate classification models including Decision Trees, Naive Bayes, and Random Forests using cross-validation.", "mapped_po": [2, 4]},
    {"co_number": 4, "bloom_level": "Applying", "co_description": "Implement unsupervised clustering techniques such as K-Means and DBSCAN for pattern discovery.", "mapped_po": [3, 4]},
    {"co_number": 5, "bloom_level": "Creating", "co_description": "Synthesize end-to-end data mining pipelines and visualize actionable predictive insights for business intelligence.", "mapped_po": [4, 5, 6]}
]

dm_weeks = [
    (1, "Prelim", "Introduction to Data Mining, KDD Process, and CRISP-DM Framework", "Interactive Lecture and Python Scikit-Learn Setup", "Environment Setup Task", [1],
     "Define the Knowledge Discovery in Databases (KDD) process", "Configure Python data science libraries (Pandas, NumPy, Scikit-Learn)", "Value data integrity and ethical handling of datasets"),
    (2, "Prelim", "Data Types, Attribute Statistics, and Exploratory Data Analysis (EDA)", "EDA Hands-on Lab Session", "Dataset Profiling Report", [1],
     "Identify nominal, binary, ordinal, and numeric attribute types", "Compute descriptive statistical measures and create boxplot distributions", "Appreciate statistical rigor when profiling raw data"),
    (3, "Prelim", "Data Cleaning: Imputation of Missing Values and Noise Smoothing", "Data Cleaning Implementation Lab", "Data Cleaning Script Output", [1],
     "Explain techniques for handling missing data and noisy observations", "Write imputation functions and apply binning smoothing methods", "Demonstrate meticulous care when treating dirty data"),
    (4, "Prelim", "Data Integration, Transformation, Normalization, and Discretization", "Feature Transformation Workshop", "Normalized Feature Dataset", [1],
     "Contrast min-max normalization versus z-score standardization", "Transform skewed distributions using log and power transforms", "Acknowledge the necessity of dimensional consistency"),
    (5, "Prelim", "Dimensionality Reduction: Principal Component Analysis (PCA)", "PCA Coding Session", "PCA Variance Retention Plot", [1, 2],
     "Explain eigenvectors, eigenvalues, and variance explained ratios", "Perform dimensionality reduction using PCA in Scikit-Learn", "Strive for balance between data compression and information loss"),
    (6, "Prelim", "Preliminary Examination: Data Preprocessing and Feature Engineering Exam", "Formal Prelim Written & Practical Exam", "Prelim Examination Score & Code", [1, 2],
     "Recall data preprocessing steps and statistical scaling theorems", "Execute timed ETL and feature transformation pipeline tasks", "Exhibit academic integrity and composure under timed assessment"),

    (7, "Midterm", "Association Rule Mining: Concepts, Support, Confidence, and Lift", "Association Metrics Calculation Workshop", "Market Basket Metric Worksheet", [2],
     "Formulate mathematical definitions of support, confidence, and lift", "Calculate association metrics manually for item transaction matrices", "Recognize market basket insights for retail strategy"),
    (8, "Midterm", "The Apriori Algorithm: Candidate Generation and Pruning", "Apriori Algorithm Implementation Lab", "Frequent Itemset Generator", [2],
     "Explain the downward closure property of frequent itemsets", "Code Apriori candidate generation and support counting loops", "Value computational optimization when generating candidate itemsets"),
    (9, "Midterm", "FP-Growth Algorithm: Constructing FP-Trees and Mining Conditional Trees", "FP-Growth Performance Benchmarking", "Comparative Mining Benchmark", [2],
     "Contrast Apriori candidate bottlenecks with FP-tree compression", "Mine frequent patterns using the mlxtend FP-Growth library", "Appreciate tree compression memory efficiency"),
    (10, "Midterm", "Classification Fundamentals: Supervised Learning, Train/Test Splits, and Confusion Matrices", "Model Evaluation Workshop", "Confusion Matrix Diagnostic Sheet", [3],
     "Explain true positive, false positive, precision, recall, and F1-score", "Compute confusion matrices and ROC-AUC curves programmatically", "Emphasize ethical awareness regarding false negative costs"),
    (11, "Midterm", "Decision Trees: Information Gain, Gini Impurity, and Pruning Techniques", "Decision Tree Modeling Lab", "Decision Tree Classifier Task", [3],
     "Calculate entropy and information gain for candidate split nodes", "Train and visualize decision tree classifiers in Python", "Demonstrate diligence in preventing decision tree overfitting"),
    (12, "Midterm", "Midterm Examination: Association Mining and Supervised Classification Practical Exam", "Formal Midterm Practical Examination", "Midterm Exam Submission & Rubric", [2, 3],
     "Synthesize association rules and classification metrics", "Build and evaluate predictive models under timed exam conditions", "Demonstrate technical competence under formal assessment"),

    (13, "Final", "Probabilistic Classification: Naive Bayes Classifiers and Laplace Smoothing", "Naive Bayes Spam Classification Lab", "Spam Filtering Engine", [3],
     "Explain Bayes theorem and conditional independence assumptions", "Implement Gaussian and Multinomial Naive Bayes classifiers", "Value probabilistic reasoning in uncertainty management"),
    (14, "Final", "Ensemble Methods: Bagging, Random Forests, and Gradient Boosting", "Ensemble Learning Workshop", "Random Forest Benchmark", [3],
     "Differentiate bagging versus boosting variance-reduction mechanics", "Train Random Forest and XGBoost classifiers on complex datasets", "Strive for state-of-the-art predictive accuracy"),
    (15, "Final", "Cluster Analysis: Partitioning Methods (K-Means and K-Medoids)", "K-Means Clustering Lab Session", "Clustering Elbow Plot Task", [4],
     "Explain inertia, Euclidean distance centroids, and elbow method", "Execute K-Means clustering and silhouette score evaluations", "Display curiosity in discovering hidden unsupervised groupings"),
    (16, "Final", "Density-Based Clustering (DBSCAN) and Outlier Detection", "DBSCAN Density Clustering Lab", "Anomaly Detection Report", [4],
     "Contrast centroid clustering with density-reachability (Epsilon, MinPts)", "Implement DBSCAN for arbitrary cluster shapes and noise extraction", "Appreciate noise resilience in real-world sensor streams"),
    (17, "Final", "Big Data Mining Pipelines: Integration, Deployment, and Dashboard Visualization", "Integrated Analytics Capstone Workshop", "Pre-Defense Interactive Dashboard", [1, 2, 3, 4, 5],
     "Design end-to-end predictive pipelines combining ETL and models", "Deploy machine learning pipelines using Streamlit/Gradio", "Collaborate effectively within agile data science teams"),
    (18, "Final", "Final Examination & Capstone Defense: Data Mining Solution Presentation", "Formal Capstone Project Defense", "Final Project Evaluation & Rubric", [1, 2, 3, 4, 5],
     "Synthesize all supervised, unsupervised, and preprocessing methodologies", "Defend an end-to-end data mining project before evaluators", "Exemplify Perpetualite leadership and professional presentation ethics")
]

dm_grading = [
    {"assessment_task": "Hands-on Laboratory Exercises & Jupyter Notebooks", "percentage_weight": 40.0},
    {"assessment_task": "Quizzes & Theoretical Problem Sets", "percentage_weight": 20.0},
    {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
    {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
    {"assessment_task": "Final Examination & Capstone Project Defense", "percentage_weight": 15.0}
]

# ---------------------------------------------------------------------------
# 2. CS 312: Artificial Intelligence and Machine Learning
# ---------------------------------------------------------------------------
ai_cos = [
    {"co_number": 1, "bloom_level": "Applying", "co_description": "Implement classical search algorithms including BFS, DFS, A* heuristic search, and Minimax game playing.", "mapped_po": [1, 2]},
    {"co_number": 2, "bloom_level": "Analyzing", "co_description": "Analyze supervised regression and classification models using gradient descent optimization.", "mapped_po": [2, 3]},
    {"co_number": 3, "bloom_level": "Applying", "co_description": "Construct multi-layer perceptron (MLP) neural networks using PyTorch for pattern recognition.", "mapped_po": [2, 4]},
    {"co_number": 4, "bloom_level": "Evaluating", "co_description": "Evaluate convolutional neural network (CNN) architectures on visual classification tasks.", "mapped_po": [3, 4, 5]},
    {"co_number": 5, "bloom_level": "Creating", "co_description": "Design an intelligent agent solving real-world automated reasoning or computer vision problems.", "mapped_po": [4, 5, 6]}
]

ai_weeks = [
    (1, "Prelim", "Introduction to AI, Turing Test, Rational Agents, and PEAS Descriptions", "Agent Design Workshop and Python Setup", "PEAS Agent Specification", [1],
     "Define intelligence paradigms and rational agent classifications", "Construct PEAS (Performance, Environment, Actuators, Sensors) models", "Acknowledge the ethical considerations of autonomous agents"),
    (2, "Prelim", "Uninformed Search Strategies: Breadth-First, Depth-First, and Uniform-Cost", "Search Algorithm Coding Lab", "State Space Graph Explorer", [1],
     "Formulate state space graphs and search frontier mechanics", "Implement BFS and DFS maze traversal algorithms in Python", "Value algorithmic completeness versus memory space trade-offs"),
    (3, "Prelim", "Informed (Heuristic) Search: Greedy Best-First Search and A* Algorithm", "A* Pathfinding Workshop", "A* Grid Navigation Task", [1],
     "Explain admissible and consistent heuristic properties", "Code the A* algorithm using priority queues and Manhattan distance", "Strive for optimal pathfinding performance"),
    (4, "Prelim", "Adversarial Search: Game Playing, Minimax Algorithm, and Alpha-Beta Pruning", "Game AI Coding Lab (Tic-Tac-Toe / Connect-4)", "Minimax Game Engine", [1],
     "Describe game trees, utility functions, and zero-sum game dynamics", "Implement Minimax decision trees with Alpha-Beta pruning", "Display patience and rigor in debugging recursive game states"),
    (5, "Prelim", "Constraint Satisfaction Problems (CSP): Backtracking and Forward Checking", "CSP Problem Solving Lab (N-Queens / Sudoku)", "Sudoku Solver Program", [1],
     "Explain variables, domains, constraints, and arc consistency", "Write constraint satisfaction backtracking solvers", "Appreciate pruning efficiency in combinatorial spaces"),
    (6, "Prelim", "Preliminary Examination: Problem Formulation and Search Algorithms Exam", "Formal Prelim Written & Practical Exam", "Prelim Exam Rubric & Score", [1],
     "Recall search theorems, heuristic equations, and complexity proofs", "Execute live timed search algorithm implementations", "Demonstrate integrity and professionalism under exam conditions"),

    (7, "Midterm", "Knowledge Representation: Propositional and First-Order Logic Inference", "Logical Inference Coding Workshop", "Knowledge Base Resolution Task", [1, 2],
     "Formulate logical propositions, truth tables, and Horn clauses", "Build simple rule-based inference engines and forward chaining", "Value structured deductive reasoning in AI knowledge systems"),
    (8, "Midterm", "Supervised Learning: Linear Regression, Cost Functions, and Gradient Descent", "Linear Regression Lab from Scratch", "Gradient Descent Visualizer", [2],
     "Derive Mean Squared Error (MSE) and partial derivative update rules", "Code vector-based batch gradient descent in Python and NumPy", "Appreciate mathematical elegance in objective function minimization"),
    (9, "Midterm", "Logistic Regression and Binary Cross-Entropy Loss for Classification", "Logistic Classification Lab", "Sigmoid Decision Boundary Task", [2],
     "Explain sigmoid activation, odds ratios, and log-loss mechanics", "Implement logistic regression decision boundaries", "Commit to thorough verification of false positive rates"),
    (10, "Midterm", "Optimization Algorithms: Stochastic Gradient Descent, Adam, and Learning Rates", "Optimizer Comparison Workshop", "Loss Convergence Benchmark", [2],
     "Contrast batch gradient descent with Adam adaptive momentum", "Tune learning rate hyperparameters to avoid local minima traps", "Exhibit perseverance when troubleshooting non-converging loss"),
    (11, "Midterm", "Multi-Layer Perceptrons (MLP): Forward Propagation and Backpropagation", "Neural Network Coding Lab", "2-Layer Neural Net Task", [3],
     "Formulate backpropagation chain rules for gradient calculation", "Construct basic multi-layer perceptrons with ReLU activations", "Value mathematical depth in artificial neural computation"),
    (12, "Midterm", "Midterm Examination: Optimization and Neural Network Theory Exam", "Formal Midterm Exam Session", "Midterm Practical Defense", [2, 3],
     "Synthesize gradient descent derivations and logical inference", "Execute timed neural network training and validation tasks", "Demonstrate mastery under timed evaluation"),

    (13, "Final", "PyTorch Framework Foundations: Tensors, Autograd, and DataLoader Modules", "PyTorch Deep Learning Setup Lab", "PyTorch Training Loop Script", [3],
     "Explain automatic differentiation and computational graph construction", "Build modular PyTorch training, validation, and testing loops", "Value modular engineering when structuring deep learning code"),
    (14, "Final", "Convolutional Neural Networks (CNN): Convolutions, Pooling, and Strides", "Image Processing and Filter Workshop", "Convolution Filter Output", [4],
     "Describe feature map extraction, kernel weights, and max-pooling", "Implement convolutional filter passes on image tensors", "Display curiosity in computer vision spatial representations"),
    (15, "Final", "CNN Architectures for Image Classification (LeNet, AlexNet, ResNet)", "Image Classification Lab with PyTorch", "Transfer Learning Classifier", [4],
     "Analyze vanishing gradients and residual shortcut connections", "Fine-tune pretrained ResNet backbones using transfer learning", "Uphold scientific rigor when reporting classification metrics"),
    (16, "Final", "Introduction to Natural Language Processing (NLP) and Recurrent Architectures", "Text Tokenization and Embedding Lab", "Sentiment Classification Model", [4],
     "Explain word tokenization, vocabulary building, and embedding vectors", "Train text classification models using LSTM or simple Transformers", "Value linguistic nuances and context in language AI"),
    (17, "Final", "AI Project Integration, Model Explainability, and Ethical Guidelines", "Capstone AI Engine Workshop", "Pre-Defense Integrated AI System", [1, 2, 3, 4, 5],
     "Evaluate algorithmic bias, fairness, and model interpretability", "Package intelligent AI models into accessible web applications", "Practice constructive teamwork and peer code review"),
    (18, "Final", "Final Examination & Capstone Defense: Intelligent Agent Project Presentation", "Formal Capstone Project Defense", "Final Evaluation Score & Rubric", [1, 2, 3, 4, 5],
     "Synthesize classical search, machine learning, and deep neural networks", "Defend a fully functional AI application before a faculty panel", "Demonstrate Perpetualite leadership, communication, and ethical virtue")
]

ai_grading = [
    {"assessment_task": "Hands-on PyTorch Labs & Algorithmic Tasks", "percentage_weight": 40.0},
    {"assessment_task": "Quizzes & Theoretical Problem Sets", "percentage_weight": 20.0},
    {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
    {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
    {"assessment_task": "Final Examination & Capstone Defense", "percentage_weight": 15.0}
]

# ---------------------------------------------------------------------------
# 3. IT 221: Web Systems and Technologies
# ---------------------------------------------------------------------------
web_cos = [
    {"co_number": 1, "bloom_level": "Applying", "co_description": "Implement modern, accessible responsive web user interfaces using HTML5, CSS3, and JavaScript.", "mapped_po": [1, 2]},
    {"co_number": 2, "bloom_level": "Applying", "co_description": "Develop scalable asynchronous frontend applications leveraging component state and API integration.", "mapped_po": [1, 3]},
    {"co_number": 3, "bloom_level": "Analyzing", "co_description": "Analyze client-server architectures, HTTP protocols, RESTful API conventions, and JSON serialization.", "mapped_po": [2, 3]},
    {"co_number": 4, "bloom_level": "Evaluating", "co_description": "Evaluate web security vulnerabilities including XSS, CSRF, and SQL Injection using security audits.", "mapped_po": [3, 4]},
    {"co_number": 5, "bloom_level": "Creating", "co_description": "Design and deploy full-stack database-driven web applications integrating secure authentication and cloud hosting.", "mapped_po": [4, 5, 6]}
]

web_weeks = [
    (1, "Prelim", "Web Architecture, Client-Server Model, HTTP Protocols, and Tooling", "Interactive Lecture and VSCode Web Extension Setup", "Developer Environment Setup Task", [1, 3],
     "Explain request-response lifecycles, DNS resolution, and HTTP headers", "Configure modern web developer tools, Git, and live servers", "Appreciate web standards set forth by the W3C"),
    (2, "Prelim", "Semantic HTML5 Elements, Document Outlines, and Web Accessibility (a11y)", "Accessible Page Construction Lab", "WCAG Compliant Page Prototype", [1],
     "Identify semantic markup tags (header, nav, main, section, footer)", "Build accessible form controls and ARIA attributes for screen readers", "Value inclusivity and accessibility for diverse user groups"),
    (3, "Prelim", "Modern CSS3: Box Model, Flexbox Layouts, and CSS Grid Systems", "Responsive Layout Workshop", "Multi-Column Layout Grid", [1],
     "Contrast block, inline, flex, and grid CSS formatting models", "Implement responsive flexbox navigation and grid content cards", "Strive for aesthetic balance and clean typographic hierarchy"),
    (4, "Prelim", "Responsive Web Design: Mobile-First Strategy and Media Queries", "Mobile-First Design Lab Session", "Responsive Multi-Device Site", [1],
     "Explain viewport configurations, responsive breakpoints, and REM units", "Construct responsive layouts adapting fluidly to mobile and desktop", "Demonstrate empathy for mobile users with limited bandwidth"),
    (5, "Prelim", "Core JavaScript: ES6+ Syntax, DOM Manipulation, and Event Handling", "Interactive DOM Scripting Lab", "Dynamic UI Component Task", [1],
     "Describe closures, arrow functions, destructuring, and event bubbling", "Write JavaScript manipulating the DOM in response to user events", "Display diligence when validating user inputs on the frontend"),
    (6, "Prelim", "Preliminary Examination: Frontend Architecture and Responsive Design Exam", "Formal Prelim Written & Practical Exam", "Prelim Practical Submission & Rubric", [1, 3],
     "Recall HTTP response codes, CSS layout algorithms, and DOM hierarchy", "Code a timed responsive web interface from design mockups", "Exhibit professionalism and academic honesty under timed assessment"),

    (7, "Midterm", "Asynchronous JavaScript: Promises, Async/Await, and Fetch API", "Async Data Fetching Workshop", "Weather Dashboard App", [2, 3],
     "Explain single-threaded event loops, call stacks, and callback queues", "Fetch and parse remote JSON payloads using async/await patterns", "Value graceful error handling during network latencies"),
    (8, "Midterm", "Frontend Framework Concepts: Component-Based Architecture and Virtual DOM", "Component Structure Lab Session", "Reusable UI Component Suite", [2],
     "Differentiate imperative DOM manipulation versus declarative components", "Construct reusable UI components passing dynamic properties (props)", "Commit to modular, reusable software architecture"),
    (9, "Midterm", "Component State Management, Lifecycle Hooks, and Forms", "Interactive State Management Workshop", "Reactive Todo Application", [2],
     "Explain unidirectional data flow and reactive state mutation rules", "Manage local component state and handle controlled form inputs", "Appreciate immediate feedback loops in user interfaces"),
    (10, "Midterm", "Backend Engineering: Node.js/Python Servers and RESTful Route Handlers", "REST API Development Lab", "CRUD REST Endpoint Suite", [3],
     "Define REST architectural constraints, idempotency, and URI schemes", "Build HTTP GET, POST, PUT, DELETE routes handling JSON requests", "Emphasize clean API documentation and uniform route naming"),
    (11, "Midterm", "Database Integration: Connecting Web Servers to Relational/NoSQL Stores", "Database Connection Workshop", "Database-Driven API Service", [3, 5],
     "Contrast SQL relational queries with document collection paradigms", "Perform CRUD database operations through server-side connection pools", "Value ACID transactions and data consistency in web stores"),
    (12, "Midterm", "Midterm Examination: Full-Stack API Integration Practical Exam", "Formal Midterm Exam Session", "Midterm Full-Stack Project Defense", [2, 3],
     "Synthesize asynchronous frontend requests and backend API controllers", "Deploy and test integrated client-server data flows under inspection", "Demonstrate technical competence under formal assessment"),

    (13, "Final", "Web Security Essentials: OWASP Top 10, Cross-Site Scripting (XSS), and CSRF", "Security Audit and Penetration Lab", "Vulnerability Audit Report", [4],
     "Explain XSS vectors, CSRF tokens, and Content Security Policies (CSP)", "Audit and patch vulnerable client-side input reflection points", "Uphold ethical responsibility in safeguarding user privacy"),
    (14, "Final", "Authentication & Authorization: Password Hashing, JWT, and Sessions", "JWT Authentication Coding Workshop", "Secure Login/Register Engine", [4, 5],
     "Describe cryptographic salting, bcrypt hashing, and JWT signatures", "Implement secure login routes issuing signed JSON Web Tokens", "Commit to zero plain-text credential persistence in databases"),
    (15, "Final", "SQL Injection Prevention and Server-Side Input Sanitization", "SQLi Remediation Lab Session", "Sanitized Database Layer Task", [4],
     "Analyze raw query vulnerabilities versus parameterized statements", "Refactor vulnerable database queries to use prepared parameters", "Demonstrate vigilance in defensive coding practices"),
    (16, "Final", "Web Performance Optimization: Asset Minification, Caching, and CDN", "Performance Profiling Workshop", "Lighthouse Audit Optimization", [1, 2, 4],
     "Explain browser caching headers, gzip compression, and tree-shaking", "Profile website performance using Chrome Lighthouse and optimize assets", "Strive for excellence in sub-second page loading speeds"),
    (17, "Final", "Full-Stack Deployment: Containerization, CI/CD, and Cloud Hosting", "Cloud Deployment Lab (Vercel / Render)", "Production Live URL Submission", [5],
     "Outline environmental variables, production builds, and continuous delivery", "Deploy full-stack web applications to live cloud hosting environments", "Practice constructive team coordination during release cycles"),
    (18, "Final", "Final Examination & Capstone Defense: Enterprise Web Solution Showcase", "Formal Capstone Project Defense", "Final Project Evaluation & Rubric", [1, 2, 3, 4, 5],
     "Synthesize all frontend, backend, security, and deployment domains", "Present and defend a live, responsive full-stack web application", "Exemplify Perpetualite leadership and professional presentation ethics")
]

web_grading = [
    {"assessment_task": "Full-Stack Web Coding Labs & Milestones", "percentage_weight": 40.0},
    {"assessment_task": "Quizzes & Security Assessments", "percentage_weight": 20.0},
    {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
    {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
    {"assessment_task": "Final Examination & Web Capstone Defense", "percentage_weight": 15.0}
]

# ---------------------------------------------------------------------------
# 4. IT 213: Advanced Database Management Systems
# ---------------------------------------------------------------------------
db_cos = [
    {"co_number": 1, "bloom_level": "Applying", "co_description": "Design normalized relational schemas achieving 3NF and BCNF to eliminate data redundancies.", "mapped_po": [1, 2]},
    {"co_number": 2, "bloom_level": "Analyzing", "co_description": "Analyze complex SQL queries, execution plans, and B-Tree indexing strategies to optimize query performance.", "mapped_po": [2, 3]},
    {"co_number": 3, "bloom_level": "Evaluating", "co_description": "Evaluate transaction management protocols, ACID guarantees, and concurrency control locking mechanisms.", "mapped_po": [3, 4]},
    {"co_number": 4, "bloom_level": "Applying", "co_description": "Implement NoSQL document databases and distributed data pipelines for unstructured enterprise data.", "mapped_po": [2, 4, 5]},
    {"co_number": 5, "bloom_level": "Creating", "co_description": "Architect an enterprise database system incorporating automated backups, replication, and role-based security.", "mapped_po": [4, 5, 6]}
]

db_weeks = [
    (1, "Prelim", "Relational Model Review, Relational Algebra, and DBMS Architecture", "Interactive Lecture and PostgreSQL/MySQL Setup", "DBMS Tooling Setup Task", [1],
     "Define relational algebra operators (select, project, join, union)", "Configure enterprise DBMS instances and SQL query workbenches", "Acknowledge the vital role of persistent storage in computing"),
    (2, "Prelim", "Conceptual Design: Enhanced Entity-Relationship (EER) Modeling", "EER Modeling Workshop", "EER Diagram Specification", [1],
     "Identify superclasses, subclasses, specialization, and generalization", "Construct comprehensive EER diagrams for complex enterprise domains", "Appreciate precise conceptual abstractions before physical schema design"),
    (3, "Prelim", "Functional Dependencies and Relational Normalization (1NF, 2NF, 3NF)", "Normalization Problem Solving Lab", "Schema Normalization Proof", [1],
     "Define functional dependencies, candidate keys, and transitive dependencies", "Decompose unnormalized data tables into 1NF, 2NF, and 3NF", "Value mathematical rigor in eliminating update anomalies"),
    (4, "Prelim", "Boyce-Codd Normal Form (BCNF) and Multi-Valued Dependencies (4NF)", "Advanced Normalization Workshop", "BCNF Decomposition Task", [1],
     "Differentiate 3NF from BCNF and identify multi-valued dependencies", "Perform lossless-join and dependency-preserving BCNF decompositions", "Demonstrate precision when assessing non-trivial functional constraints"),
    (5, "Prelim", "Advanced SQL: Window Functions, Common Table Expressions (CTEs), and Subqueries", "Advanced SQL Coding Session", "Complex Analytics Query Task", [1, 2],
     "Explain window partitions, ranking functions, and recursive CTEs", "Write multi-table SQL queries leveraging CTEs and analytical partitions", "Display diligence in formatting readable, modular SQL scripts"),
    (6, "Prelim", "Preliminary Examination: EER Modeling and Advanced Normalization Exam", "Formal Prelim Written & Practical Exam", "Prelim Exam Rubric & Score", [1, 2],
     "Recall relational algebra equations and normalization theorems", "Execute timed schema normalization and complex SQL query tasks", "Exhibit academic integrity and professional composure under evaluation"),

    (7, "Midterm", "Storage Architecture: File Organization, Page Slots, and Buffer Pools", "Storage Internals Workshop", "Buffer Management Simulation", [2],
     "Describe slotted page architectures, free space maps, and LRU eviction", "Calculate disk I/O overheads across differing buffer cache allocations", "Appreciate low-level hardware constraints in data storage"),
    (8, "Midterm", "Index Structures: B-Tree and B+ Tree Fundamentals and Mechanics", "B+ Tree Calculation Workshop", "B+ Tree Node Traversal Task", [2],
     "Explain search key distributions, fan-out, and split/merge mechanics", "Trace index lookups, range scans, and node insertions in B+ trees", "Value algorithmic logarithmic efficiency in data access"),
    (9, "Midterm", "Query Processing: Parsing, Translation, and Relational Optimization", "Query Execution Plan Lab", "EXPLAIN Query Plan Analysis", [2],
     "Describe cost estimation formulas for sequential scans versus index scans", "Generate and interpret EXPLAIN ANALYZE execution plans in SQL", "Strive for optimal query execution efficiency"),
    (10, "Midterm", "Index Tuning Strategies: Clustered vs Non-Clustered and Covering Indexes", "Database Index Tuning Workshop", "Query Acceleration Benchmark", [2],
     "Differentiate clustered primary indexes from secondary covering indexes", "Create targeted composite indexes that eliminate table lookups", "Demonstrate prudence in managing index write-penalty overheads"),
    (11, "Midterm", "Stored Procedures, User-Defined Functions, and Automated Triggers", "Database Programmability Lab", "Audit Trigger Implementation", [1, 2],
     "Explain PL/SQL block structures, cursor loops, and event triggers", "Program database triggers enforcing automated auditing and data integrity", "Commit to defensive validation at the database layer"),
    (12, "Midterm", "Midterm Examination: Query Tuning and Index Optimization Practical Exam", "Formal Midterm Practical Exam", "Midterm Practical Submission & Rubric", [1, 2],
     "Synthesize index architecture, execution plans, and PL/SQL triggers", "Profile and optimize poorly performing queries under timed inspection", "Demonstrate technical competence under formal assessment"),

    (13, "Final", "Transaction Processing: ACID Properties and Concurrency Anomalies", "Transaction Anomaly Simulation Lab", "ACID Anomaly Verification Sheet", [3],
     "Explain dirty reads, non-repeatable reads, phantom reads, and atomicity", "Simulate concurrent transaction conflicts using multi-session terminals", "Recognize the severe financial impact of transactional data corruption"),
    (14, "Final", "Concurrency Control: Two-Phase Locking (2PL), Deadlocks, and Isolation Levels", "Locking and Deadlock Workshop", "Deadlock Detection Task", [3],
     "Contrast Read Committed, Repeatable Read, and Serializable isolations", "Resolve deadlock cycles using wait-for graphs and timeout configurations", "Value data consistency over raw concurrent throughput"),
    (15, "Final", "Database Recovery Protocols: Write-Ahead Logging (WAL) and Checkpointing", "Recovery Protocol Simulation Lab", "ARIES Recovery Trace Report", [3],
     "Describe the ARIES recovery algorithm (Analysis, Redo, Undo phases)", "Trace WAL log sequences to recover consistent database states", "Emphasize disaster preparedness and fault tolerance in systems"),
    (16, "Final", "NoSQL Document Databases: MongoDB Schema Design and Aggregation Pipelines", "MongoDB Querying Workshop", "NoSQL Aggregation Pipeline", [4],
     "Contrast relational table models with flexible BSON document collections", "Write multi-stage aggregation pipelines for nested document filtering", "Appreciate scalability trade-offs in distributed data models"),
    (17, "Final", "Database Security, Role-Based Access Control (RBAC), and Replication", "Security Hardening Workshop", "Hardened Database Deployment", [4, 5],
     "Outline column-level privileges, encryption at rest, and replica sets", "Configure role-based access control and read-replica failovers", "Practice constructive team coordination during enterprise setup"),
    (18, "Final", "Final Examination & Capstone Defense: Enterprise Database Architecture Showcase", "Formal Capstone Defense Session", "Final Evaluation & Rubric", [1, 2, 3, 4, 5],
     "Synthesize normalization, index tuning, transaction recovery, and NoSQL", "Present and defend an enterprise database solution before evaluators", "Exemplify Perpetualite leadership and professional presentation ethics")
]

db_grading = [
    {"assessment_task": "Advanced SQL & Database Tuning Labs", "percentage_weight": 40.0},
    {"assessment_task": "Quizzes & Theoretical Problem Sets", "percentage_weight": 20.0},
    {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
    {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
    {"assessment_task": "Final Examination & Database Capstone Defense", "percentage_weight": 15.0}
]

# ---------------------------------------------------------------------------
# 5. CS 323: Information Assurance and Cybersecurity
# ---------------------------------------------------------------------------
sec_cos = [
    {"co_number": 1, "bloom_level": "Applying", "co_description": "Apply cryptographic algorithms including symmetric encryption, asymmetric ciphers, and hash functions.", "mapped_po": [1, 2]},
    {"co_number": 2, "bloom_level": "Analyzing", "co_description": "Analyze network attack vectors, packet payloads, and port scans using Wireshark and Nmap.", "mapped_po": [2, 3]},
    {"co_number": 3, "bloom_level": "Evaluating", "co_description": "Evaluate system vulnerabilities, attack surfaces, and risk exposure using industry security frameworks.", "mapped_po": [3, 4]},
    {"co_number": 4, "bloom_level": "Applying", "co_description": "Configure intrusion detection systems (IDS) and firewall access control lists (ACLs) to block cyber threats.", "mapped_po": [2, 4, 5]},
    {"co_number": 5, "bloom_level": "Creating", "co_description": "Design an organizational cybersecurity defense architecture integrating zero-trust principles and incident response.", "mapped_po": [4, 5, 6]}
]

sec_weeks = [
    (1, "Prelim", "Cybersecurity Foundations: CIA Triad, Threat Actors, and Defense-in-Depth", "Interactive Lecture and Security Tooling Setup", "Security Lab Environment Setup", [1],
     "Define Confidentiality, Integrity, Availability, and non-repudiation", "Configure isolated virtualized security labs (Kali Linux / Wireshark)", "Acknowledge legal frameworks, ethics, and computer misuse laws"),
    (2, "Prelim", "Classical Cryptography: Caesar, Vigenère, and Transposition Ciphers", "Cipher Cracking Hands-on Lab", "Frequency Analysis Report", [1],
     "Explain substitution principles, cipher keys, and frequency distributions", "Perform frequency analysis to crack monoalphabetic substitution ciphers", "Appreciate historical cryptanalysis evolution"),
    (3, "Prelim", "Symmetric Cryptography: DES, AES, Block Cipher Modes (CBC vs GCM)", "AES Implementation Workshop", "AES File Encryption Script", [1],
     "Contrast symmetric block ciphers with stream ciphers", "Encrypt and decrypt confidential files using Python cryptography and AES-GCM", "Value cryptographic strength and proper initialization vectors"),
    (4, "Prelim", "Asymmetric Cryptography: RSA, Diffie-Hellman Key Exchange, and ECC", "RSA Key Generation Lab Session", "Public-Private Key Exchange Task", [1],
     "Explain prime factorization, trapdoor functions, and public/private keys", "Generate RSA keypairs and exchange encrypted messages securely", "Demonstrate meticulous care in safeguarding private keys"),
    (5, "Prelim", "Cryptographic Hashes and Message Integrity: SHA-256 and HMAC", "Hash Verification Lab Session", "File Integrity Checker Tool", [1],
     "Describe avalanche effects, collision resistance, and preimage resistance", "Implement file integrity monitoring tools using SHA-256 and HMAC", "Uphold zero tolerance for unauthorized digital tampering"),
    (6, "Prelim", "Preliminary Examination: Applied Cryptography and Math Foundations Exam", "Formal Prelim Written & Practical Exam", "Prelim Exam Rubric & Score", [1],
     "Recall cryptographic formulas, modular arithmetic, and cipher modes", "Execute timed file encryption and key generation coding problems", "Exhibit professionalism and academic honesty under timed assessment"),

    (7, "Midterm", "Digital Signatures, Public Key Infrastructure (PKI), and X.509 Certificates", "Digital Certificate Authority Lab", "Signed Certificate Workflow", [1, 2],
     "Explain digital signatures, Certificate Authorities (CAs), and CRLs", "Generate self-signed SSL/TLS certificates and verify digital signatures", "Value trust hierarchies and authentication infrastructures"),
    (8, "Midterm", "Network Reconnaissance: OSINT, Footprinting, and DNS Enumeration", "Passive Reconnaissance Workshop", "Footprinting Intelligence Brief", [2],
     "Differentiate passive reconnaissance from active network scanning", "Execute open-source intelligence gathering and WHOIS/DNS analysis", "Emphasize ethical boundaries during security reconnaissance"),
    (9, "Midterm", "Active Scanning: Port Scanning with Nmap and Banner Grabbing", "Nmap Port Scanning Lab Session", "Network Attack Surface Report", [2],
     "Explain TCP three-way handshakes, SYN stealth scans, and UDP scanning", "Perform comprehensive Nmap scans to detect open ports and OS versions", "Display discipline in scanning only authorized sandbox targets"),
    (10, "Midterm", "Packet Analysis: Sniffing Protocols, ARP Poisoning, and Wireshark", "Packet Capture Analysis Lab", "Network Sniffing Incident Report", [2],
     "Identify plaintext credential leaks in HTTP, FTP, and Telnet traffic", "Capture and analyze malicious packet payloads using Wireshark filters", "Respect privacy rights and adhere strictly to ethical sniffing mandates"),
    (11, "Midterm", "Web Application Attacks: SQL Injection and Cross-Site Scripting (XSS)", "OWASP Vulnerability Lab Session", "Vulnerability Exploitation Log", [2, 3],
     "Analyze reflected XSS scripts and SQL authentication bypass payloads", "Identify vulnerable web parameters and remediate code vulnerabilities", "Commit to defense-first security engineering"),
    (12, "Midterm", "Midterm Examination: Network Scanning and Vulnerability Audit Exam", "Formal Midterm Exam Session", "Midterm Practical Defense", [1, 2, 3],
     "Synthesize reconnaissance data, packet capture analysis, and web attacks", "Identify and audit network vulnerabilities under timed inspection", "Demonstrate technical competence under formal assessment"),

    (13, "Final", "Authentication Protocols: Multi-Factor Authentication (MFA) and Biometrics", "MFA Implementation Workshop", "TOTP Authenticator Integration", [3, 4],
     "Contrast knowledge, ownership, and inherence authentication factors", "Integrate Time-based One-Time Password (TOTP) protocols in Python", "Value multi-layered defenses in identity verification"),
    (14, "Final", "Endpoint Security: Malware Classification (Viruses, Trojans, Ransomware)", "Malware Analysis Sandbox Lab", "Malware Behavioral Profile", [3],
     "Describe static versus dynamic malware behavioral analysis techniques", "Analyze executable file hashes and inspect sandbox system calls safely", "Maintain strict containment when inspecting suspicious artifacts"),
    (15, "Final", "Firewalls, Access Control Lists (ACL), and Network Segmentation", "Firewall Configuration Workshop", "Firewall Rule Hardening Task", [4],
     "Differentiate packet filtering, stateful inspection, and next-gen firewalls", "Configure Linux iptables / UFW firewall rules blocking unauthorized ports", "Appreciate defense-in-depth principles through segmentation"),
    (16, "Final", "Intrusion Detection Systems (IDS): Snort and Suricata Rule Engineering", "Snort IDS Rule Deployment Lab", "IDS Alert Analysis Log", [4],
     "Explain signature-based versus anomaly-based intrusion detection", "Write Snort detection rules alerting on malicious ICMP and port scans", "Strive for high true-positive detection without alert fatigue"),
    (17, "Final", "Incident Response, Computer Forensics, and Disaster Recovery Planning", "Cyber Incident Response Simulation", "Incident Response Playbook", [4, 5],
     "Outline the 6 phases of incident response (NIST SP 800-61)", "Acquire volatile RAM artifacts and preserve forensic chain of custody", "Demonstrate calm leadership during simulated security breaches"),
    (18, "Final", "Final Examination & Capstone Defense: Cybersecurity Defense Architecture", "Formal Capstone Project Defense", "Final Evaluation Score & Rubric", [1, 2, 3, 4, 5],
     "Synthesize applied cryptography, network defense, IDS, and incident response", "Defend an enterprise zero-trust security architecture before a panel", "Exemplify Perpetualite leadership and professional presentation ethics")
]

sec_grading = [
    {"assessment_task": "Hands-on Security & Penetration Labs", "percentage_weight": 40.0},
    {"assessment_task": "Quizzes & Cryptographic Problem Sets", "percentage_weight": 20.0},
    {"assessment_task": "Preliminary Examination", "percentage_weight": 10.0},
    {"assessment_task": "Midterm Examination", "percentage_weight": 15.0},
    {"assessment_task": "Final Examination & Security Defense Showcase", "percentage_weight": 15.0}
]


# ---------------------------------------------------------------------------
# Compilation and Ingestion Loop
# ---------------------------------------------------------------------------
courses_to_build = [
    ("CS 311", "Data Mining and Knowledge Discovery", "Comprehensive study of the Knowledge Discovery in Databases (KDD) process, data preprocessing, association rule mining (Apriori, FP-Growth), classification algorithms (Decision Trees, Naive Bayes, Random Forests), clustering techniques (K-Means, DBSCAN), and practical data science applications using Python.", "CS 211, MATH 201", "3 Units (2 Units Lecture, 1 Unit Laboratory)", dm_cos, dm_weeks, dm_grading),
    ("CS 312", "Artificial Intelligence and Machine Learning", "Foundational study of intelligent agents, problem solving via heuristic search (A*, Minimax), knowledge representation, supervised learning, neural network architectures, PyTorch implementation, and computer vision with convolutional neural networks.", "CS 211, MATH 202", "3 Units (2 Units Lecture, 1 Unit Laboratory)", ai_cos, ai_weeks, ai_grading),
    ("IT 221", "Web Systems and Technologies", "Comprehensive study of modern client-server web architectures, responsive frontend development (HTML5/CSS3/JavaScript), RESTful API engineering, backend services, database persistence, web security vulnerabilities, and cloud deployment.", "CS 102", "3 Units (2 Units Lecture, 1 Unit Laboratory)", web_cos, web_weeks, web_grading),
    ("IT 213", "Advanced Database Management Systems", "Advanced relational database engineering, 3NF and BCNF normalization, physical storage architectures, B+ tree indexing strategies, query execution optimization, ACID transaction guarantees, concurrency control, and NoSQL document databases.", "IT 104", "3 Units (2 Units Lecture, 1 Unit Laboratory)", db_cos, db_weeks, db_grading),
    ("CS 323", "Information Assurance and Cybersecurity", "Fundamental principles of digital information assurance, applied cryptography (AES, RSA, SHA-256), network reconnaissance, packet analysis, web application security (OWASP), firewalls, intrusion detection systems (Snort), and incident response.", "IT 212, CS 211", "3 Units (2 Units Lecture, 1 Unit Laboratory)", sec_cos, sec_weeks, sec_grading)
]

for (code, title, desc, prereq, units, cos, weeks, grading) in courses_to_build:
    syllabus = build_syllabus(code, title, desc, prereq, units, cos, weeks, grading)
    file_name = f"{code.replace(' ', '_')}_Syllabus.json"
    target_path = os.path.join(OUTPUT_DIR, file_name)
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(syllabus.model_dump_json(indent=2))
    print(f"Generated and validated: {target_path}")

print("\nALL 5+ COMPUTER SCIENCE SYLLABUS JSON FILES GENERATED AND VALIDATED SUCCESSFULLY!")
