import pytest
import pandas as pd
from app.agent.chat_engine import AIChatEngine

def test_compute_dataset_evidence_targeted_queries():
    # Create sample DataFrame simulating uploaded CSV dataset
    df = pd.DataFrame({
        "Region": ["East", "West", "East", "North", "West", "East"],
        "Product": ["Laptop", "Mouse", "Laptop", "Monitor", "Keyboard", "Mouse"],
        "Category": ["Electronics", "Accessories", "Electronics", "Electronics", "Accessories", "Accessories"],
        "Sales": [1200.0, 50.0, 1200.0, 300.0, 80.0, 50.0],
        "Quantity": [2, 5, 2, 1, 4, 5],
        "Status": ["Completed", "Completed", "Pending", "Completed", "Completed", "Completed"]
    })

    engine = AIChatEngine()

    # 1. Test subgroup query for West region
    evidence_west = engine._compute_dataset_evidence(df, "What are total sales in West region?", [], {})
    calc_text_west = evidence_west["summary_text"]

    assert "West" in calc_text_west
    assert "Sales" in calc_text_west

    # 2. Test top product query
    evidence_top = engine._compute_dataset_evidence(df, "Which product generated highest sales?", [], {})
    calc_text_top = evidence_top["summary_text"]

    assert "Laptop" in calc_text_top

    # 3. Test total sales computation
    evidence_tot = engine._compute_dataset_evidence(df, "What is the total sales across all regions?", [], {})
    calc_text_tot = evidence_tot["summary_text"]

    # Total sales sum is 1200 + 50 + 1200 + 300 + 80 + 50 = 2880
    assert "2,880.00" in calc_text_tot


def test_format_llm_output_markdown_transformation():
    engine = AIChatEngine()

    raw_llm_text = """
ANSWER
Total sales in East region is $2,450.00 across 3 orders.

EVIDENCE
- Sales Total: $2,450.00 (85.1% of total)
- Order Count: 3

ANALYSIS
East region is the primary revenue driver for the dataset.

CONFIDENCE
High
"""

    formatted = engine._format_llm_output(raw_llm_text, {})

    assert "### 📌 **Direct Answer**" in formatted
    assert "### 📊 **Calculated Data Evidence**" in formatted
    assert "### 🔍 **Analytical Insight**" in formatted
    assert "⚡ **Data Verification**" in formatted


