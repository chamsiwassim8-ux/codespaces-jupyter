import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Page Configuration
st.set_page_config(
    page_title="CIF & FOC Calculator", page_icon="📦", layout="wide"
)

st.title(" Logistics Cost & FOC Calculator")

# Main page parameter input for Total Freight Cost
st.subheader("1. Shipment Parameters")
total_freight = st.number_input(
    "Total Freight Cost ($)",
    min_value=0.0,
    value=1500.0,
    step=100.0,
    help="Enter the total freight cost for the entire shipment.",
)

# Main page parameter input for Total Insurance Cost
total_insurance = st.number_input(
    "Total Insurance Cost ($)",
    min_value=0.0,
    value=150.0,
    step=10.0,
    help="Enter the total insurance cost for the entire shipment.",
)

st.subheader("2. Enter Product Data")

# Default data using strings so commas and formatting from Excel paste cleanly
default_data = pd.DataFrame({
    "Product Name": ["Item A", "Item B", "Item C"],
    "Quantity": ["100", "250", "50"],
    "CIF/Unit ($)": ["45.50", "20.00", "120.00"],
})

# Interactive Data Editor configured with Text columns to handle Excel copy-paste safely
edited_df = st.data_editor(
    default_data,
    num_rows="dynamic",
    width="stretch",
    column_config={
        "Product Name": st.column_config.TextColumn("Product Name"),
        "Quantity": st.column_config.TextColumn(
            "Quantity", help="Paste quantities here"
        ),
        "CIF/Unit ($)": st.column_config.TextColumn(
            "CIF/Unit ($)", help="Paste CIF per unit here"
        ),
    },
)


# Helper function to clean text inputs (handles commas, spaces, dollar signs)
def clean_to_float(val):
  if pd.isna(val) or str(val).strip() == "":
    return 0.0
  # Convert to string and clean formatting symbols
  val_str = str(val).strip().replace("$", "").replace(" ", "")

  # Handle commas (remove thousand separator commas, or convert European decimal commas)
  if "," in val_str and "." in val_str:
    val_str = val_str.replace(",", "")  # e.g., 1,250.50 -> 1250.50
  elif "," in val_str:
    # If comma is used as decimal (e.g., 45,50) vs thousand (e.g., 1,250)
    parts = val_str.split(",")
    if len(parts) == 2 and len(parts[1]) <= 2:
      val_str = val_str.replace(",", ".")
    else:
      val_str = val_str.replace(",", "")

  try:
    return float(val_str)
  except ValueError:
    return 0.0


# Calculation Button
if st.button("Calculate Costs", type="primary"):
  if edited_df.empty:
    st.error("The table is empty. Please add at least one product.")
  else:
    df = edited_df.copy()

    # Clean the input columns to ensure proper numeric calculations
    df["Clean_Qty"] = df["Quantity"].apply(clean_to_float)
    df["Clean_CIF_Unit"] = df["CIF/Unit ($)"].apply(clean_to_float)

    # Core Calculations
    # 1. CIF of product line = Quantity * CIF/unit
    df["CIF of Product Line"] = df["Clean_Qty"] * df["Clean_CIF_Unit"]
    total_cif = df["CIF of Product Line"].sum()

    if total_cif > 0:
      # 2. Apportion Freight and Insurance proportionally based on CIF share
      df["Cost of Freight"] = (
          df["CIF of Product Line"] / total_cif
      ) * total_freight
      df["Cost of Insurance"] = (
          df["CIF of Product Line"] / total_cif
      ) * total_insurance
    else:
      df["Cost of Freight"] = 0.0
      df["Cost of Insurance"] = 0.0

    # 3. FOC of product line = CIF - Freight - Insurance
    df["FOC of Product Line"] = (
        df["CIF of Product Line"] - df["Cost of Freight"] - df["Cost of Insurance"]
    )

    # 4. FOC/u = FOC of product line / Quantity
    df["FOC/Unit"] = df.apply(
        lambda row: (
            row["FOC of Product Line"] / row["Clean_Qty"]
            if row["Clean_Qty"] > 0
            else 0
        ),
        axis=1,
    )

    # Prepare final clean output DataFrame
    output_df = pd.DataFrame({
        "Product Name": df["Product Name"],
        "Quantity": df["Clean_Qty"],
        "CIF/Unit ($)": df["Clean_CIF_Unit"],
        "CIF of Product Line": df["CIF of Product Line"],
        "Cost of Freight": df["Cost of Freight"],
        "Cost of Insurance": df["Cost of Insurance"],
        "FOC of Product Line": df["FOC of Product Line"],
        "FOC/Unit": df["FOC/Unit"],
    })

    # --- Results Display ---
    st.markdown("---")
    st.subheader("3. Calculation Results")

    # Display Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Shipment CIF", f"${total_cif:,.2f}")
    col2.metric("Total Freight", f"${total_freight:,.2f}")
    col3.metric("Total Insurance", f"${total_insurance:,.2f}")
    col4.metric(
        "Total Shipment FOC", f"${output_df['FOC of Product Line'].sum():,.2f}"
    )

    total_foc = output_df["FOC of Product Line"].sum()
    if total_cif > 0 and total_foc >= 0:
        st.subheader("CIF Composition")
        amounts = [total_foc, total_freight, total_insurance]
        labels = ["FOC", "Freight", "Insurance"]
        fig, (ax, legend_ax) = plt.subplots(
            1, 2, figsize=(5, 3), gridspec_kw={"width_ratios": [1, 1.4]}
        )
        wedges, _ = ax.pie(amounts, startangle=90, radius=0.8)
        ax.axis("equal")
        legend_ax.axis("off")
        legend_ax.legend(
            wedges,
            [
                f"{label}: ${amount:,.2f} ({amount / total_cif:.1%})"
                for label, amount in zip(labels, amounts)
            ],
            loc="center left",
            frameon=False,
            fontsize=9,
        )
        st.pyplot(fig, width="content")
        plt.close(fig)
    else:
        st.info(
            "A CIF composition pie chart is unavailable because the total CIF "
            "must be positive and FOC must be non-negative."
        )

    # Rounding for display
    display_df = output_df.copy()
    cols_to_round_2 = [
        "CIF/Unit ($)",
        "CIF of Product Line",
        "Cost of Freight",
        "Cost of Insurance",
        "FOC of Product Line",
    ]
    display_df[cols_to_round_2] = display_df[cols_to_round_2].round(2)
    display_df["FOC/Unit"] = display_df["FOC/Unit"].round(3)

    st.dataframe(display_df, width="stretch")

    # Download button for results
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name="FOC_cif_calculations.csv",
        mime="text/csv",
    )
