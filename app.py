import streamlit as st
import pandas as pd

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Athenasia Pricing Calculator", layout="wide")

st.title("Athenasia Pricing Calculator 2026")
st.markdown("### 🇭🇰 Package Recommender & Quote Generator")
st.divider()

# --- DATA TABLES (SOURCED FROM PRICE LIST 2026) ---

# BRONZE: Max Turnover -> Total Package Price (Accounting + Audit + Tax) [cite: 13]
BRONZE_TIERS = {
    0: 5800, 250000: 9800, 500000: 12800, 1000000: 16800,
    2000000: 21300, 3000000: 25800, 4000000: 28800, 5000000: 37800,
    7000000: 42800, 8000000: 46600, 10000000: 55600, 12000000: 60600,
    15000000: 68600, 20000000: 76100, 25000000: 82600
}

# SECONDARY AUDIT: Max Turnover -> Audit Fee (Sign + Work) [cite: 19]
SECONDARY_AUDIT_TIERS = {
    0: 2600, 250000: 4000, 500000: 5000, 1000000: 5000,
    2000000: 7000, 3000000: 7500, 4000000: 8000, 5000000: 12000,
    7000000: 13000, 8000000: 14000, 10000000: 21000, 12000000: 25000,
    15000000: 32000, 20000000: 38500, 25000000: 45000
}

# SILVER: Max Entries -> Monthly Fee 
SILVER_TIERS = {
    600: 1500, 1800: 2000, 3000: 3000, 6000: 4000,
    9000: 5000, 12000: 6000, 18000: 8000, 24000: 10000
}

FIXED_FEES = {
    "TAX_REP": 2600,       # Standard Tax Rep Fee
    "BANK_CONF": 500,      # Bank Confirmation per account
    "BRONZE_LIMIT": 1200,  # Max entries for Bronze
    "SILVER_OVERAGE": 5,   # Cost per entry over 24,000 
    "GOLD_BASE_YR": 240000,# Gold starts at 20k/month 
    "PLATINUM_BASE_YR": 600000 # Platinum starts at 50k/month 
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
        annual_entries = (sales_tx * 12) + (expense_tx * 12)
        
    else:
        with col2:
            payouts = st.number_input("Payouts per Month", value=2, help="e.g. Amazon bi-weekly = 2")
        annual_entries = (payouts * 12) + (expense_tx * 12)

    st.info(f"**Calculated Annual Entries:** {annual_entries:,}")

# --- LOGIC FUNCTIONS ---

def get_bronze_price(turnover, entries):
    if entries > FIXED_FEES["BRONZE_LIMIT"]:
        return None, "Too many entries (>1,200)"
    
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

    # 2. Audit Fee (Secondary List)
    audit_fee = 0
    # Use the max tier if turnover exceeds list, or find correct tier
    if turnover > 25000000:
        audit_fee = 45000 # Cap at max listed or custom
    else:
        for limit, price in SECONDARY_AUDIT_TIERS.items():
            if turnover <= limit:
                audit_fee = price
                break
            
    total = accounting_annual + audit_fee + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]
    return total, accounting_annual, audit_fee

# --- MAIN CALCULATION & DISPLAY ---

bronze_price, bronze_msg = get_bronze_price(turnover, annual_entries)
silver_total, silver_acct, silver_audit = get_silver_price(turnover, annual_entries)

# Calculate Gold Total (Base + Audit + Tax + Bank)
# Gold uses the same Audit/Tax fees as Silver/Secondary list
gold_total = FIXED_FEES["GOLD_BASE_YR"] + silver_audit + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]

# DECISION ENGINE
recommended_package = "Silver" # Default fallback
rec_reason = ""

if bronze_price and silver_total < bronze_price:
    recommended_package = "Silver"
    rec_reason = f"Silver is **HKD {bronze_price - silver_total:,.0f} cheaper** than Bronze due to low volume."
elif bronze_price:
    recommended_package = "Bronze"
    rec_reason = "Client fits Bronze limits (Best Price)."
elif annual_entries > 48000:
    recommended_package = "Gold"
    rec_reason = "Volume (>48k) makes Gold cheaper than Silver surcharges."
elif turnover > 20000000:
    recommended_package = "Gold"
    rec_reason = "High Turnover (>20M) requires Gold for Tax Optimization."
else:
    recommended_package = "Silver"
    rec_reason = "Client exceeds Bronze limits (1,200 entries)."

# --- UI DISPLAY ---

if recommended_package == "Gold":
    st.warning(f"### 🏆 Recommendation: GOLD Package")
    st.markdown(f"**Reason:** {rec_reason}")
elif recommended_package == "Bronze":
    st.success(f"### 💡 Recommendation: BRONZE Package")
    st.markdown(f"**Reason:** {rec_reason}")
else:
    st.info(f"### 💡 Recommendation: SILVER Package")
    st.markdown(f"**Reason:** {rec_reason}")

st.divider()

col1, col2, col3 = st.columns(3)

# 1. BRONZE CARD
with col1:
    st.subheader("🥉 Bronze")
    if bronze_price:
        is_winner = (recommended_package == "Bronze")
        st.metric(label="Total Annual Cost", value=f"HKD {bronze_price:,.0f}", delta="Recommended" if is_winner else None)
        st.caption("Bundled Fee (Acct + Audit + Tax)")
    else:
        st.error(f"Not Eligible")
        st.caption(f"Reason: {bronze_msg}")

# 2. SILVER CARD
with col2:
    st.subheader("🥈 Silver")
    is_winner = (recommended_package == "Silver")
    st.metric(label="Total Annual Cost", value=f"HKD {silver_total:,.0f}", delta="Recommended" if is_winner else None)
    
    with st.expander("Breakdown"):
        st.write(f"Acct: {silver_acct:,.0f}")
        st.write(f"Audit: {silver_audit:,.0f}")
        st.write(f"Tax: {FIXED_FEES['TAX_REP']:,.0f}")
        st.write(f"Bank: {FIXED_FEES['BANK_CONF']:,.0f}")
        if annual_entries > 24000:
            st.warning(f"⚠️ High Volume Surcharge applied! (+{(annual_entries-24000)*5:,.0f})")

# 3. GOLD CARD
with col3:
    st.subheader("🥇 Gold")
    is_winner = (recommended_package == "Gold")
    st.metric(label="Total Annual Cost", value=f"HKD {gold_total:,.0f}", delta="Best Value" if is_winner else None)
    st.caption("Includes Tax Optimization & Forecasts")
    
    with st.expander("Breakdown"):
        st.write(f"Acct (Base): {FIXED_FEES['GOLD_BASE_YR']:,.0f}")
        st.write(f"Audit: {silver_audit:,.0f}")
        st.write("Includes Tax Advisory")

# --- PLATINUM TRIGGER ---
if turnover > 50000000: # Only show Platinum for >50M Turnover
    st.divider()
    st.error("💎 **PLATINUM TIER ELIGIBLE**")
    st.markdown(f"Turnover is **HKD {turnover:,.0f}**. Recommended for Dr. Timmermans' oversight.")
    st.metric("Platinum Starting Price", f"HKD {FIXED_FEES['PLATINUM_BASE_YR'] + silver_audit:,.0f} +")
