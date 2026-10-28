from decimal import Decimal, ROUND_FLOOR
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(
    page_title="CIF & FOC Calculator",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Logistics Cost & FOC Calculator")

# Shipment Parameters
st.subheader("1. Shipment Parameters")

total_freight = st.number_input(
    "Total Freight Cost ($)",
    min_value=0.0,
    value=1500.0,
    step=100.0,
    help="Enter the total freight cost for the entire shipment.",
)

total_insurance = st.number_input(
    "Total Insurance Cost ($)",
    min_value=0.0,
    value=None,
    step=10.0,
    format="%.2f",
    placeholder="Leave blank to calculate",
    help="Enter the total insurance cost, or leave blank to calculate it from CIF, FOC, and freight.",
)

# Global discount applied to all products
foc_discount_pct = st.number_input(
    "FOC Discount (%)",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=0.1,
    help="Discount applied to the calculated FOC/Unit for all products.",
)

st.subheader("2. Enter Product Data")

# Default data using strings so commas and formatting from Excel paste cleanly
default_data = pd.DataFrame(
    {
        "Product Name": ["Item A", "Item B", "Item C"],
        "Quantity": ["100", "250", "50"],
        "CIF/Unit ($)": ["45.50", "20.00",
