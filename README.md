# Autonomous Data Scientist Application

An enterprise-ready platform featuring a **FastAPI** backend with database persistence, a local statistical calculation engine, and a premium **React (Vite + TypeScript)** frontend following the specialized **"Violet + Black + Light Ash"** design system.

The application allows users to upload custom CSV datasets, enter analytical queries, watch a multi-phased autonomous investigation progress in real-time, inspect analytical calculations (ANOVA, regression, grouping, trends), simulate alternative scenarios dynamically, and export executive PDF reports.

---

## 🌟 Key Features

1. **Autonomous Analytical Pipeline**: Multistage agent loop that profiles data, generates hypotheses, executes calculations, evaluates evidence, and synthesizes reports.
2. **Deterministic Failover Engine**: If external LLM service keys are unavailable, the system automatically redirects execution paths to local python calculations, ensuring zero workflow outages.
3. **Interactive Evidence Graph**: Visualizes group relationships, variable trends, and analytical nodes along with conflicts/contradictions detection.
4. **Audit Trail Logger**: Displays a chronological timeline detailing dataset profiling, prioritized hypotheses, executions, and validations.
5. **What-If Simulation Scenario Builder**: Simulates percentage adjustments on numerical metrics and estimates simulated business impacts.
6. **Executive PDF Export**: Dynamically compiles findings and recommendations for user download.

---

## 📁 Repository Structure

```
AUTONOMOUS DATA SCIENTIST/
│
├── frontend/                     # React Vite app
│   ├── src/                      # UI components, pages, styles, services
│   ├── package.json              # Client dependencies
│   └── vite.config.ts            # Vite compiler configuration
│
├── backend/                      # FastAPI python app
│   ├── app/                      # Backend routers, DB models, agents, analytics
│   ├── tests/                    # Pytest test suite modules
│   ├── requirements.txt          # Python packages list
│   └── autonomous_data_scientist.db  # Sqlite database persistence
│
├── demo_sales.csv                # Demonstration CSV dataset
├── .env.example                  # Template configuration setting file
├── .gitignore                    # Global git ignore configurations
└── README.md                     # Project documentation (this file)
```

---

## ⚙️ Running Locally

### 1. Setup Backend
1. Navigate to directory: `cd backend`
2. Create environment file `.env` by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start FastAPI server using Uvicorn:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

### 2. Setup Frontend
1. Navigate to directory: `cd frontend`
2. Install npm pack dependencies:
   ```bash
   npm install
   ```
3. Start local development server:
   ```bash
   npm run dev
   ```
4. Open the application in your browser at `http://localhost:5173`.
