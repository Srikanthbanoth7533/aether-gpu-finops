# AetherFin GPU Ops: GenAI GPU FinOps & Carbon Sustainability Platform

AetherFin GPU Ops is an enterprise-grade, recruiter-ready **Product, Business, and Data Analytics platform** designed to monitor, optimize, and audit generative AI GPU clusters. It bridges the gap between infrastructure engineering, financial operations (FinOps), and carbon sustainability by providing actionable recommendations and real-time anomaly detection.

---

## 🚀 Key Features

1. **Executive Insights Engine**: Automatically evaluates compute sizing and recommends operations (e.g., decommissioning, cluster right-sizing) to generate weekly cost savings and carbon footprint reductions.
2. **Trend & Cohort Analytics**: Visualizes historical cost, GPU utilization, SLA breach severity, and compute efficiency trends over customizable time windows (7d, 30d, custom).
3. **Z-Score Anomaly Detection**: Statistical anomaly detection identifying latency spikes, idle waste, SLA violations, and thermal/power anomalies.
4. **KPI Drill-Down Details**: Interactive metric cards that open breakdowns by cloud provider (AWS, GCP, On-Prem) and identify contributing nodes.
5. **AI FinOps Optimization Agent**: A conversational AI advisor answering natural language queries about cost optimization and node performance.
6. **Enterprise Security & Audit Logs**: Secured with JWT Authentication, Role-Based Access Control (Admin/User), and an immutable User Activity Audit Log.
7. **Production-Ready Database**: Dynamic support for SQLite (development) and PostgreSQL (production) with Docker Compose files.
8. **Analytical Case Study**: Built-in product case study explaining the data collection methodology, custom indices, and strategic recommendations.
9. **Automated Exporter Service**: One-click extraction of dashboard summaries and audit trails into CSV and executive-friendly text reports.

---

## 📊 Custom KPI Framework

Rather than basic system-level charts, AetherFin GPU Ops introduces a custom financial-environmental KPI framework:

*   **GPU Idle Cost Penalty (GICP)**: Calculates the percentage of total GPU spend wasted on idle or severely underutilized nodes (utilization < 15%).
    $$\text{GICP (\%)} = \frac{\sum(\text{Idle Hours} \times \text{Hourly Cost})}{\text{Total Spend}} \times 100$$
*   **Model Compute Efficiency Score (MCES)**: Measures aggregate throughput relative to power consumption (Tokens per Watt-hour).
    $$\text{MCES} = \frac{\text{Prompt Tokens} + \text{Completion Tokens}}{\sum \text{Power Draw (Watts)} \times 1\text{ Hour}}$$
*   **SLA Violation Exposure Index (SLA-VEI)**: A non-linear penalty index that measures the severity of SLA latency breaches, rather than just raw counts.
    $$\text{SLA-VEI} = \frac{\sum \max\left(0, \frac{\text{Actual Latency} - \text{Target Latency}}{\text{Target Latency}}\right)}{\text{Total Requests}} \times 100$$
*   **Carbon Offset ROI (COROI)**: Quantifies the dollars saved per kilogram of $CO_2$ reduced, demonstrating the synergy of green IT policies.

---

## 🛠️ Technology Stack

*   **Frontend**: React (TypeScript), Vite, Vanilla CSS Zinc Dark Mode (glassmorphism UI), custom SVG timelines & Canvas charts.
*   **Backend**: FastAPI (Python 3.11+), SQLAlchemy, Uvicorn, PyJWT (JWT tokens), NumPy (for Z-Score analysis).
*   **Database**: PostgreSQL (production), SQLite (local testing).
*   **DevOps**: Docker, Docker Compose, Virtual Environment (venv).

---

## 📐 System Architecture

```mermaid
graph TD
    subgraph Client [React Frontend]
        UI[Zinc Dark-Mode Dashboard]
        Drill[KPI Drill-Down Panel]
        AIChat[AI FinOps Agent Chat]
        AuditView[Security Logs Audit]
    end

    subgraph Server [FastAPI Backend]
        API[FastAPI Router]
        Auth[JWT Auth Guard]
        Sizing[Executive Sizing Engine]
        Anomaly[Z-Score Anomaly Detector]
        Agent[Gemini Data Analytics Agent]
        Export[CSV/Text Exporter]
    end

    subgraph Storage [Databases]
        DB[(SQLite / PostgreSQL)]
        Compose[Docker Compose Postgres]
    end

    UI -->|API Requests with JWT| API
    API --> Auth
    API --> Sizing
    API --> Anomaly
    API --> Agent
    API --> Export
    
    Sizing --> DB
    Anomaly --> DB
    Agent --> DB
    Export --> DB
    Compose -->|Provisions| DB
```

---

## 🖥️ Screen Previews

### 1. Dashboard View
Comprehensive monitoring of financial waste (GICP), performance indices (SLA-VEI), and compute efficiency (MCES).
![Dashboard](screenshots/sizing.png)

### 2. Anomaly Detection
Statistical outlier analysis tracking high-latency transactions and idle resources.
![Anomaly Detection](screenshots/anomalies.png)

### 3. Drill-Down KPI Breakdowns
Detailed breakdown of costs by Cloud Provider, Region, and Instance Type.
![Drill Down](screenshots/drilldown.png)

### 4. Admin Audit Trail & Logs
Immutable JWT-secured logs tracking user sessions and system resource exports.
![Admin Logs](screenshots/admin_logs.png)

---

## 🚀 Quick Start

### 1. Run the Backend
```bash
cd backend
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend server
uvicorn app.main:app --port 8001 --reload
```

*The backend runs on `http://127.0.0.1:8001`. You can view the Interactive OpenAPI Docs at `http://127.0.0.1:8001/docs`.*

### 2. Run the Database (Optional Postgres Upgrade)
```bash
cd backend
docker-compose up -d
```
Set environment variable `DATABASE_URL=postgresql://aetherfin_admin:aetherfin_secure_password_2026@localhost:5432/aetherfin_gpu_finops` in your shell, and run the backend to automatically migrate and seed data into PostgreSQL.

### 3. Run the Frontend
```bash
cd frontend
# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

*The frontend runs on `http://localhost:3000` (configured with Vite proxy pointing to port 8001).*

---

## 🔒 Production Audits & Tests

Run backend unit and load tests:
```bash
cd backend
python -m pytest   # Runs python tests
python audit_tests.py # Performs edge case, security injection, and simulated concurrency audits
```

---

## 🧑‍💻 Creator Portfolio Details
This project demonstrates:
*   **Data Analytics**: Statistical anomaly calculation (Z-score), pre-fetching optimization, time-series timeline aggregation.
*   **Business Analytics**: Sizing models, SLA penalties, and $CO_2$ footprint metrics mapped to dollar savings.
*   **Enterprise Architecture**: Token access controls, PostgreSQL support, database connection pooling safeguards, and robust error handlers.
