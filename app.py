import streamlit as st
import pandas as pd

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Athenasia Pricing Calculator", layout="wide")

st.title("Athenasia Pricing Calculator")
st.markdown("⚠️ FOR INTERNAL USE ONLY ⚠️")
st.divider()

# --- DATA TABLES (SOURCED FROM PRICE LIST 2026) ---

# BRONZE: Max Turnover -> Total Package Price (Accounting + Audit + Tax)
# Source: Page 5 "AAT PACKAGE YEARLY"
BRONZE_TIERS = {
    0: 5800, 250000: 9800, 500000: 12800, 1000000: 16800,
    2000000: 21300, 3000000: 25800, 4000000: 28800, 5000000: 37800,
    7000000: 42800, 8000000: 46600, 10000000: 55600, 12000000: 60600,
    15000000: 68600, 20000000: 76100, 25000000: 82600
}

# SECONDARY AUDIT: Max Turnover -> Audit Fee (Sign + Work)
# Source: Page 6 & 19 "Secondary list" for Silver/Gold
SECONDARY_AUDIT_TIERS = {
    0: 2600, 250000: 4000, 500000: 5000, 1000000: 5000,
    2000000: 7000, 3000000: 7500, 4000000: 8000, 5000000: 12000,
    7000000: 13000, 8000000: 14000, 10000000: 21000, 12000000: 25000,
    15000000: 32000, 20000000: 38500, 25000000: 45000
}

# SILVER: Max Entries -> Monthly Fee
# Source: Page 8 & 24 "Silver" Table
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
    if turnover > 25000000:
        audit_fee = 45000 # Cap or custom
    else:
        for limit, price in SECONDARY_AUDIT_TIERS.items():
            if turnover <= limit:
                audit_fee = price
                break
            
    total = accounting_annual + audit_fee + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]
    return total, accounting_annual, audit_fee

# --- MAIN CALCULATION ---

bronze_price, bronze_msg = get_bronze_price(turnover, annual_entries)
silver_total, silver_acct, silver_audit = get_silver_price(turnover, annual_entries)

# Calculate Gold Total (for upsell comparison)
gold_total = FIXED_FEES["GOLD_BASE_YR"] + silver_audit + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]

# DECISION ENGINE (The "Value Upgrade" Logic)
recommended_package = "Silver"
rec_reason = ""
upsell_bullets = []

if bronze_price and silver_total < bronze_price:
    # 1. Silver is CHEAPER than Bronze (Smart Save)
    recommended_package = "Silver"
    rec_reason = f"Silver is **HKD {bronze_price - silver_total:,.0f} cheaper** than Bronze due to low volume."

elif bronze_price and (silver_total - bronze_price) <= 3000:
    # 2. STRATEGIC UPGRADE: Silver is slightly more expensive (<3k), but better value
    recommended_package = "Silver"
    diff = silver_total - bronze_price
    rec_reason = f"**Great Value Upgrade:** Silver is only HKD {diff:,.0f} more than Bronze."
    
    # Detailed Selling Points (Why upgrade?)
    upsell_bullets = [
        "**Peace of Mind:** In Silver, Athenasia pays fines if we are at fault. In Bronze, YOU pay the fines.",
        "**Dedicated Human:** You get a specific dedicated accountant, not a 'random assignment' pool.",
        "**Higher Priority:** Silver clients jump the queue ahead of Bronze.",
        "**Visibility:** Monthly reports (Xero) vs just once a year (Bronze)."
    ]

elif bronze_price:
    # 3. Bronze is significantly cheaper (>3k difference)
    recommended_package = "Bronze"
    rec_reason = "Client fits Bronze limits (Best Price)."

else:
    # 4. Client doesn't qualify for Bronze
    recommended_package = "Silver"
    rec_reason = "Client exceeds Bronze limits (1,200 entries)."

# --- DISPLAY RECOMMENDATION ---

if recommended_package == "Bronze":
    st.success(f"### 💡 Recommendation: BRONZE Package")
    st.markdown(f"**Reason:** {rec_reason}")
else:
    st.info(f"### 💡 Recommendation: SILVER Package")
    st.markdown(f"**Reason:** {rec_reason}")
    
    # Show the "Sales Pitch" if it's a strategic upgrade
    if upsell_bullets:
        diff = silver_total - bronze_price
        st.warning(f"**Bronze is HKD {diff:,.0f} cheaper, but we recommend Silver because:**")
        for bullet in upsell_bullets:
            st.markdown(f"- {bullet}")

st.divider()

# --- MAIN COMPARISON COLUMNS ---
col1, col2 = st.columns(2)

# 1. BRONZE CARD
with col1:
    st.subheader("🥉 Bronze (Standard)")
    if bronze_price:
        is_winner = (recommended_package == "Bronze")
        st.metric(label="Total Annual Cost", value=f"HKD {bronze_price:,.0f}", delta="Lowest Price" if not is_winner else "Recommended")
        st.write("Yearly Reporting | Standard Priority")
        st.markdown("**Software:** Excel or Xero")
        st.caption("Includes: Accounting, Audit, Tax, Bank Conf.")
    else:
        st.error(f"Not Eligible")
        st.caption(f"Reason: {bronze_msg}")

# 2. SILVER CARD
with col2:
    st.subheader("🥈 Silver (Monthly)")
    is_winner = (recommended_package == "Silver")
    st.metric(label="Total Annual Cost", value=f"HKD {silver_total:,.0f}", delta="Recommended Upgrade" if is_winner else None)
    st.write("Monthly Reporting | Dedicated Accountant")
    st.markdown("**Software:** Xero (Charged Separately)")
    
    with st.expander("Silver Breakdown"):
        st.write(f"Acct: {silver_acct:,.0f}")
        st.write(f"Audit: {silver_audit:,.0f}")
        st.write(f"Tax: {FIXED_FEES['TAX_REP']:,.0f}")
        st.write(f"Bank: {FIXED_FEES['BANK_CONF']:,.0f}")
        st.caption("*Plus Xero Subscription fee (billed separately)*")
        if annual_entries > 24000:
            st.warning(f"⚠️ Volume Surcharge: +{(annual_entries-24000)*5:,.0f}")

# --- PREMIUM UPGRADES SECTION ---
st.markdown("---")
st.subheader("🚀 Premium Upgrades")

# Calculate price gap
upgrade_gap = gold_total - silver_total

col_gold, col_plat = st.columns(2)

with col_gold:
    st.markdown("#### 🥇 Upgrade to Gold")
    
    if gold_total < silver_total:
        st.success(f"**PRO TIP:** Gold is actually **CHEAPER** than Silver for this volume!")
        st.metric("Gold Total", f"HKD {gold_total:,.0f}", delta=f"Save {silver_total - gold_total:,.0f}")
    else:
        st.metric("Gold Total", f"HKD {gold_total:,.0f}", delta=f"+ HKD {upgrade_gap:,.0f} vs Silver", delta_color="off")
    
    st.markdown("""
    **Why Upgrade?**
    * ✅ **Financial Forecasts** (Yearly)
    * ✅ **Tax Optimization Review**
    * ✅ **Higher Priority** (Jump Queue)
    * ℹ️ *Xero charged separately*
    """)

with col_plat:
    st.markdown("#### 💎 Upgrade to Platinum")
    plat_price = FIXED_FEES["PLATINUM_BASE_YR"] + silver_audit
    st.metric("Starting Price", f"HKD {plat_price:,.0f}+")
    st.markdown("""
    **Why Upgrade?**
    * ✅ **Dr. Timmermans Oversight**
    * ✅ **Highest Priority**
    * ✅ **Complex Tax Advisory**
    """)


