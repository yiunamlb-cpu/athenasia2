import streamlit as st
import pandas as pd

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Athenasia Pricing Calculator", layout="centered")

st.title("Athenasia Pricing Calculator 2026")
st.markdown("### 🇭🇰 Package Recommender & Quote Generator")
st.divider()

# --- DATA TABLES (HARDCODED FROM PRICE LIST) ---

# BRONZE: Max Turnover -> Total Package Price (Accounting + Audit + Tax)
# Source: Page 5
BRONZE_TIERS = {
    0: 5800, 250000: 9800, 500000: 12800, 1000000: 16800,
    2000000: 21300, 3000000: 25800, 4000000: 28800, 5000000: 37800,
    7000000: 42800, 8000000: 46600, 10000000: 55600, 12000000: 60600,
    15000000: 68600, 20000000: 76100, 25000000: 82600
}

# SECONDARY AUDIT: Max Turnover -> Audit Fee (Sign + Work)
# Source: Page 6 / 19 (Used for Silver/Gold)
SECONDARY_AUDIT_TIERS = {
    0: 2600, 250000: 4000, 500000: 5000, 1000000: 5000,
    2000000: 7000, 3000000: 7500, 4000000: 8000, 5000000: 12000,
    7000000: 13000, 8000000: 14000, 10000000: 21000, 12000000: 25000,
    15000000: 32000, 20000000: 38500, 25000000: 45000
}

# SILVER: Max Entries -> Monthly Fee
# Source: Page 8
SILVER_TIERS = {
    600: 1500, 1800: 2000, 3000: 3000, 6000: 4000,
    9000: 5000, 12000: 6000, 18000: 8000, 24000: 10000
}

FIXED_FEES = {
    "TAX_REP": 2600,       # Standard Tax Rep Fee
    "BANK_CONF": 500,      # Bank Confirmation (assuming 1 account)
    "BRONZE_LIMIT": 1200,  # Max entries for Bronze
    "SILVER_OVERAGE": 5    # Cost per entry over 24,000
}

# --- SIDEBAR: CLIENT INPUTS ---
with st.sidebar:
    st.header("1. Client Details")
    turnover = st.number_input("Est. Annual Turnover (HKD)", value=500000, step=10000)
    
    st.header("2. Volume Estimates")
    business_type = st.radio("Business Model", ["Standard / Service", "E-commerce (Consolidated Payouts)"])
    
    col1, col2 = st.columns(2)
    with col1:
        expense_tx = st.number_input("Monthly Expenses", value=20)
    
    if business_type == "Standard / Service":
        with col2:
            sales_tx = st.number_input("Monthly Sales Inv.", value=10)
        # Calculation for Standard
        annual_entries = (sales_tx * 12) + (expense_tx * 12)
        display_tx_note = "Standard: Sales + Expenses"
        
    else:
        with col2:
            payouts = st.number_input("Payouts per Month", value=2, help="e.g. Amazon bi-weekly = 2")
            raw_sales = st.number_input("Raw Sales Tx (Optional)", value=1000)
        # Calculation for Ecommerce
        annual_entries = (payouts * 12) + (expense_tx * 12)
        display_tx_note = f"Optimized: ({payouts} payouts x 12) + Expenses"

    st.info(f"**Calculated Annual Entries:** {annual_entries:,}")

# --- LOGIC FUNCTIONS ---

def get_bronze_price(turnover, entries):
    if entries > FIXED_FEES["BRONZE_LIMIT"]:
        return None, "Too many entries (>1,200)"
    
    # Find Tier
    for limit, price in BRONZE_TIERS.items():
        if turnover <= limit:
            return price + FIXED_FEES["BANK_CONF"], "Eligible"
    return None, "Turnover too high"

def get_silver_price(turnover, entries):
    # 1. Accounting Fee
    monthly_fee = 0
    if entries > 24000:
        base_annual = 10000 * 12
        overage = (entries - 24000) * FIXED_FEES["SILVER_OVERAGE"]
        accounting_annual = base_annual + overage
    else:
        for limit, price in SILVER_TIERS.items():
            if entries <= limit:
                monthly_fee = price
                break
        accounting_annual = monthly_fee * 12

    # 2. Audit Fee (Secondary)
    audit_fee = 0
    for limit, price in SECONDARY_AUDIT_TIERS.items():
        if turnover <= limit:
            audit_fee = price
            break
            
    # 3. Total
    total = accounting_annual + audit_fee + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]
    return total, accounting_annual, audit_fee

# --- MAIN DISPLAY ---

bronze_price, bronze_msg = get_bronze_price(turnover, annual_entries)
silver_total, silver_acct, silver_audit = get_silver_price(turnover, annual_entries)

# 1. RECOMMENDATION ENGINE
if bronze_price:
    st.success(f"### 💡 Recommendation: BRONZE Package")
    st.markdown("This client fits within the Bronze limits and saves money.")
else:
    st.info(f"### 💡 Recommendation: SILVER Package")
    st.markdown("Client exceeds Bronze volume limits (1,200 entries). Silver is required.")

st.divider()

# 2. PACKAGE CARDS
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🥉 Bronze")
    if bronze_price:
        st.metric(label="Total Annual Cost", value=f"HKD {bronze_price:,.0f}")
        st.write("Includes: Accounting (Yearly), Audit, Tax, Bank Confirm.")
    else:
        st.error(f"Not Available: {bronze_msg}")
        st.write("Bronze is capped at 1,200 entries/year.")

with col_b:
    st.subheader("🥈 Silver")
    st.metric(label="Total Annual Cost", value=f"HKD {silver_total:,.0f}")
    
    # Silver Breakdown Expander
    with st.expander("See Cost Breakdown"):
        st.write(f"**Accounting:** HKD {silver_acct:,.0f} /yr")
        st.write(f"**Audit:** HKD {silver_audit:,.0f}")
        st.write(f"**Tax Rep:** HKD {FIXED_FEES['TAX_REP']:,.0f}")
        st.write(f"**Bank Confirm:** HKD {FIXED_FEES['BANK_CONF']:,.0f}")
        if annual_entries > 24000:
            st.warning("Includes surcharge for >24k entries")

# 3. GOLD / PLATINUM UPSELL
st.divider()
st.subheader("💎 Upsell Options")
gold_base = (20000 * 12) + silver_audit + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]
st.markdown(f"""
- **Gold Package:** ~HKD {gold_base:,.0f} / year
    - *Pitch:* Includes Financial Forecasts & Tax Optimization Review.
- **Platinum:** Starts at HKD 50k/month.
    - *Pitch:* Dr. Timmermans personal oversight.
""")