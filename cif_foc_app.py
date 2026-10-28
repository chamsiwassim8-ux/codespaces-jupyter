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
        df["Clean_CIF_Unit"] = df["CIF/Unit ($)"].apply(clean_to_float)

        # CIF Product Line
        df["CIF of Product Line"] = (
            df["Clean_Qty"] * df["Clean_CIF_Unit"]
        )

        total_cif = df["CIF of Product Line"].sum()

        # Freight allocation
        if total_cif > 0:
            df["Cost of Freight"] = (
                df["CIF of Product Line"] / total_cif
            ) * total_freight
        else:
            df["Cost of Freight"] = 0.0

        # Insurance handling
        if total_insurance is None:

            df["FOC/Unit"] = df.apply(
                lambda row: (
                    floor_to_cents(
                        row["Clean_CIF_Unit"]
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

        # Apply global FOC discount
        discount_factor = 1 - (foc_discount_pct / 100)

        df["Discounted FOC/Unit"] = (
            df["FOC/Unit"] * discount_factor
        )

        df["Discounted FOC of Product Line"] = (
            df["Discounted FOC/Unit"] * df["Clean_Qty"]
        )

        # Final Output Table
        output_df = pd.DataFrame(
            {
                "Product Name": df["Product Name"],
                "Quantity": df["Clean_Qty"],
                "Original CIF/Unit ($)": df["Clean_CIF_Unit"],
                "Discounted CIF/Unit ($)": df["Discounted FOC/Unit"],
                "CIF of Product Line": df["CIF of Product Line"],
                "Cost of Freight": df["Cost of Freight"],
                "Cost of Insurance": df["Cost of Insurance"],
                "Original FOC of Product Line": df[
                    "FOC of Product Line"
                ],
                "Discounted FOC of Product Line": df[
                    "Discounted FOC of Product Line"
                ],
                "Original FOC/Unit": df["FOC/Unit"],
                "Discounted FOC/Unit": df["Discounted FOC/Unit"],
            }
        )

        # Results
        st.markdown("---")
        st.subheader("3. Calculation Results")

        total_calculated_insurance = output_df[
            "Cost of Insurance"
        ].sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Shipment CIF",
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
            "Total Shipment FOC (Discounted)",
            f"${output_df['Discounted FOC of Product Line'].sum():,.2f}",
        )

        total_foc = output_df[
            "Discounted FOC of Product Line"
        ].sum()

        if (
            total_cif > 0
            and total_foc >= 0
            and total_freight >= 0
            and total_calculated_insurance >= 0
        ):
            st.subheader("CIF Composition")

            amounts = [
                total_foc,
                total_freight,
                total_calculated_insurance,
            ]

            labels = [
                "Discounted FOC",
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
            "Original FOC of Product Line",
            "Discounted FOC of Product Line",
            "Original FOC/Unit",
            "Discounted FOC/Unit",
        ]

        display_df[cols_to_round] = display_df[cols_to_round].round(
            2
        )

        st.dataframe(display_df, width="stretch")

        # Download CSV
        csv = display_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name="FOC_cif_calculations.csv",
            mime="text/csv",
        )
