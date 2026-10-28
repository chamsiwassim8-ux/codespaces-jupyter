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

# Global discount applied to CIF/Unit price
cif_discount_pct = st.number_input(
    "CIF Discount (%)",
    min_value=0.0,
    max_value=100.0,
    value=0.0,
    step=0.1,
    help="Discount applied to the CIF/Unit for all products.",
)

st.subheader("2. Enter Product Data")

# Default data using strings so commas and formatting from Excel paste cleanly
default_data = pd.DataFrame(
    {
        "Product Name": ["Item A", "Item B", "Item C"],
        "Quantity": ["100", "250", "50"],
        "CIF/Unit ($)": ["45.50", "20.00", "120.00"],
    }
)

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

    val_str = str(val).strip().replace("$", "").replace(" ", "")

    if "," in val_str and "." in val_str:
        val_str = val_str.replace(",", "")
    elif "," in val_str:
        parts = val_str.split(",")
        if len(parts) == 2 and len(parts[1]) <= 2:
            val_str = val_str.replace(",", ".")
        else:
            val_str = val_str.replace(",", "")

    try:
        return float(val_str)
    except ValueError:
        return 0.0


def floor_to_cents(value):
    return float(
        Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_FLOOR,
        )
    )


# Calculation Button
if st.button("Calculate Costs", type="primary"):

    if edited_df.empty:
        st.error("The table is empty. Please add at least one product.")

    else:
        df = edited_df.copy()

        # Clean numeric inputs
        df["Clean_Qty"] = df["Quantity"].apply(clean_to_float)
        df["Original CIF/Unit ($)"] = df["CIF/Unit ($)"].apply(clean_to_float)

        # 1. Apply discount to CIF/Unit first
        discount_factor = 1 - (cif_discount_pct / 100)
        df["Discounted CIF/Unit ($)"] = (
            df["Original CIF/Unit ($)"] * discount_factor
        )

        # 2. Calculate Discounted CIF Product Line using the discounted unit price
        df["CIF of Product Line"] = (
            df["Clean_Qty"] * df["Discounted CIF/Unit ($)"]
        )
        total_cif = df["CIF of Product Line"].sum()

        # 3. Freight allocation based on discounted CIF share
        if total_cif > 0:
            df["Cost of Freight"] = (
                df["CIF of Product Line"] / total_cif
            ) * total_freight
        else:
            df["Cost of Freight"] = 0.0

        # 4. Insurance handling
        if total_insurance is None:

            df["FOC/Unit"] = df.apply(
                lambda row: (
                    floor_to_cents(
                        row["Discounted CIF/Unit ($)"]
                        - row["Cost of Freight"] / row["Clean_Qty"]
                    )
                    if row["Clean_Qty"] > 0
                    else 0
                ),
                axis=1,
            )

            df["FOC of Product Line"] = (
                df["FOC/Unit"] * df["Clean_Qty"]
            ).round(2)

            df["Cost of Insurance"] = (
                df["CIF of Product Line"].round(2)
                - df["Cost of Freight"].round(2)
                - df["FOC of Product Line"]
            )

        else:

            if total_cif > 0:
                df["Cost of Insurance"] = (
                    df["CIF of Product Line"] / total_cif
                ) * total_insurance
            else:
                df["Cost of Insurance"] = 0.0

            df["FOC of Product Line"] = (
                df["CIF of Product Line"]
                - df["Cost of Freight"]
                - df["Cost of Insurance"]
            )

            df["FOC/Unit"] = df.apply(
                lambda row: (
                    row["FOC of Product Line"] / row["Clean_Qty"]
                    if row["Clean_Qty"] > 0
                    else 0
                ),
                axis=1,
            )

        # Exact Unrounded FOC for comparison
        df["Exact FOC of Product Line"] = (
            df["CIF of Product Line"]
            - df["Cost of Freight"]
            - df["Cost of Insurance"]
        )

        # Final Output Table
        output_df = pd.DataFrame(
            {
                "Product Name": df["Product Name"],
                "Quantity": df["Clean_Qty"],
                "Original CIF/Unit ($)": df["Original CIF/Unit ($)"],
                "Discounted CIF/Unit ($)": df["Discounted CIF/Unit ($)"],
                "CIF of Product Line": df["CIF of Product Line"],
                "Cost of Freight": df["Cost of Freight"],
                "Cost of Insurance": df["Cost of Insurance"],
                "Exact FOC of Product Line": df["Exact FOC of Product Line"],
                "Calculated FOC of Product Line": df["FOC of Product Line"],
                "FOC/Unit": df["FOC/Unit"],
            }
        )

        # Results
        st.markdown("---")
        st.subheader("3. Calculation Results")

        total_calculated_insurance = output_df[
            "Cost of Insurance"
        ].sum()
        total_exact_foc = output_df["Exact FOC of Product Line"].sum()
        total_calculated_foc = output_df["Calculated FOC of Product Line"].sum()
        foc_difference = total_calculated_foc - total_exact_foc

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Total CIF",
            f"${total_cif:,.2f}",
        )

        col2.metric(
            "Total Freight",
            f"${total_freight:,.2f}",
        )

        col3.metric(
            "Total Insurance",
            f"${total_calculated_insurance:,.2f}",
        )

        col4.metric(
            "Total Calculated FOC",
            f"${total_calculated_foc:,.2f}",
        )

        col5.metric(
            "Exact vs Calculated FOC",
            f"${total_exact_foc:,.2f}",
            delta=f"${foc_difference:,.2f} variance",
            delta_color="off",
        )

        if (
            total_cif > 0
            and total_calculated_foc >= 0
            and total_freight >= 0
            and total_calculated_insurance >= 0
        ):
            st.subheader("CIF Composition")

            amounts = [
                total_calculated_foc,
                total_freight,
                total_calculated_insurance,
            ]

            labels = [
                "Calculated FOC",
                "Freight",
                "Insurance",
            ]

            fig, (ax, legend_ax) = plt.subplots(
                1,
                2,
                figsize=(5, 3),
                gridspec_kw={"width_ratios": [1, 1.4]},
            )

            wedges, _ = ax.pie(
                amounts,
                startangle=90,
                radius=0.8,
            )

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
                "must be positive and FOC, freight, and insurance must be non-negative."
            )

        # Display formatting
        display_df = output_df.copy()

        cols_to_round = [
            "Original CIF/Unit ($)",
            "Discounted CIF/Unit ($)",
            "CIF of Product Line",
            "Cost of Freight",
            "Cost of Insurance",
            "Exact FOC of Product Line",
            "Calculated FOC of Product Line",
            "FOC/Unit",
        ]

        display_df[cols_to_round] = display_df[cols_to_round].round(2)
        display_df["FOC/Unit"] = display_df["FOC/Unit"].round(3)

        st.dataframe(display_df, width="stretch")

        # Download CSV
        csv = display_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="FOC_cif_calculations.csv",
            mime="text/csv",
        )
