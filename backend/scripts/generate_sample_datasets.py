import os
import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

np.random.seed(42)

# 1. Sales Dataset
def create_sales():
    n = 500
    dates = pd.date_range(start="2023-01-01", periods=n, freq="D")
    regions = np.random.choice(["North", "South", "East", "West"], size=n, p=[0.3, 0.25, 0.25, 0.2])
    categories = np.random.choice(["Electronics", "Furniture", "Clothing", "Office Supplies"], size=n)
    
    base_sales = np.where(regions == "North", 1500, np.where(regions == "West", 1800, 1200))
    sales = base_sales + np.random.normal(200, 150, n) + np.sin(np.arange(n) / 10) * 100
    sales = np.maximum(sales, 100)
    
    units = np.random.randint(1, 20, size=n)
    discount = np.round(np.random.uniform(0.0, 0.3, size=n), 2)
    profit = sales * (1 - discount) * np.random.uniform(0.15, 0.35, size=n)
    
    df = pd.DataFrame({
        "order_id": [f"ORD-{1000+i}" for i in range(n)],
        "date": dates.strftime("%Y-%m-%d"),
        "region": regions,
        "category": categories,
        "sales_amount": np.round(sales, 2),
        "units_sold": units,
        "discount_rate": discount,
        "profit": np.round(profit, 2)
    })
    
    # Introduce minor missingness & duplicate for quality check testing
    df.loc[10, "discount_rate"] = np.nan
    df.loc[25, "profit"] = np.nan
    df = pd.concat([df, df.iloc[[5]]], ignore_index=True) # duplicate row 5
    
    path = os.path.join(OUTPUT_DIR, "sales.csv")
    df.to_csv(path, index=False)
    print(f"Generated {path} ({len(df)} rows, {len(df.columns)} cols)")

# 2. Customer Churn Dataset
def create_churn():
    n = 600
    customer_ids = [f"CUST-{5000+i}" for i in range(n)]
    tenure = np.random.randint(1, 72, size=n)
    contract = np.random.choice(["Month-to-month", "One year", "Two year"], size=n, p=[0.55, 0.25, 0.20])
    monthly_charges = np.round(np.random.uniform(20.0, 120.0, size=n), 2)
    total_charges = np.round(tenure * monthly_charges + np.random.normal(0, 50, size=n), 2)
    total_charges = np.maximum(total_charges, monthly_charges)
    
    # Churn probability based on contract & charges
    churn_prob = np.where(contract == "Month-to-month", 0.4, 0.1) + (monthly_charges / 300)
    churn_prob = np.clip(churn_prob, 0.05, 0.85)
    churn = np.random.binomial(1, churn_prob)
    
    payment_method = np.random.choice(
        ["Electronic check", "Mailed check", "Bank transfer", "Credit card"], size=n
    )
    
    df = pd.DataFrame({
        "customer_id": customer_ids,
        "tenure_months": tenure,
        "contract_type": contract,
        "payment_method": payment_method,
        "monthly_charges": monthly_charges,
        "total_charges": total_charges,
        "churn": churn
    })
    
    path = os.path.join(OUTPUT_DIR, "customer_churn.csv")
    df.to_csv(path, index=False)
    print(f"Generated {path} ({len(df)} rows, {len(df.columns)} cols)")

# 3. Employee Data
def create_employee():
    n = 450
    dept = np.random.choice(["Engineering", "Sales", "Marketing", "HR", "Finance"], size=n)
    salary_base = np.where(dept == "Engineering", 110000, np.where(dept == "Sales", 90000, 75000))
    salary = salary_base + np.random.normal(15000, 8000, size=n)
    
    years_exp = np.random.randint(1, 20, size=n)
    performance = np.random.choice(["Low", "Medium", "High", "Exceeds"], size=n, p=[0.1, 0.4, 0.35, 0.15])
    satisfaction = np.round(np.random.uniform(1.0, 5.0, size=n), 1)
    hire_dates = pd.date_range(start="2015-01-01", periods=n, freq="W").strftime("%Y-%m-%d")
    
    df = pd.DataFrame({
        "employee_id": [f"EMP-{200+i}" for i in range(n)],
        "department": dept,
        "hire_date": hire_dates,
        "years_experience": years_exp,
        "salary": np.round(salary, 2),
        "performance_rating": performance,
        "satisfaction_score": satisfaction
    })
    
    path = os.path.join(OUTPUT_DIR, "employee_data.csv")
    df.to_csv(path, index=False)
    print(f"Generated {path} ({len(df)} rows, {len(df.columns)} cols)")

# 4. E-commerce Dataset
def create_ecommerce():
    n = 700
    dates = pd.date_range(start="2024-01-01", periods=n, freq="h").strftime("%Y-%m-%d %H:%M:%S")
    device = np.random.choice(["Desktop", "Mobile", "Tablet"], size=n, p=[0.45, 0.45, 0.10])
    session_duration = np.round(np.random.exponential(scale=180, size=n) + 10, 1)
    pages_viewed = np.random.randint(1, 25, size=n)
    order_val = np.where(np.random.rand(n) > 0.6, np.round(np.random.uniform(15.0, 350.0, size=n), 2), 0.0)
    converted = (order_val > 0).astype(int)
    
    df = pd.DataFrame({
        "session_id": [f"SES-{10000+i}" for i in range(n)],
        "timestamp": dates,
        "device_type": device,
        "session_duration_sec": session_duration,
        "pages_viewed": pages_viewed,
        "order_value": order_val,
        "converted": converted
    })
    
    path = os.path.join(OUTPUT_DIR, "ecommerce.csv")
    df.to_csv(path, index=False)
    print(f"Generated {path} ({len(df)} rows, {len(df.columns)} cols)")

if __name__ == "__main__":
    create_sales()
    create_churn()
    create_employee()
    create_ecommerce()
