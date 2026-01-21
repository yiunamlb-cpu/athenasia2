import streamlit as st
import pandas as pd

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Athenasia Pricing Calculator", layout="wide")

# --- HEADER ---
st.title("ATHENASIA Pricing Calculator")
st.markdown("⚠️⚠️⚠️ FOR INTERNAL USE ONLY ⚠️⚠️⚠️")
st.divider()

# --- DATA TABLES (SOURCED FROM PRICE LIST 2026) ---

# BRONZE BREAKDOWN DATA
# Format: Max Turnover : (Total AAT, Accounting, Audit Total, Tax Rep)
# Source: Page 5 Table 
# Audit Total = Audit Signing + Audit Work
BRONZE_DETAILED = {
    0:        {"total": 5800,  "acct": 2600,  "audit": 600,   "tax": 2600}, # Non-Commenced
    250000:   {"total": 9800,  "acct": 3200,  "audit": 4000,  "tax": 2600}, # Seed
    500000:   {"total": 12800, "acct": 5200,  "audit": 5000,  "tax": 2600}, # Seed+
    1000000:  {"total": 16800, "acct": 9200,  "audit": 5000,  "tax": 2600}, # Starter
    2000000:  {"total": 21300, "acct": 11700, "audit": 7000,  "tax": 2600}, # Starter+
    3000000:  {"total": 25800, "acct": 15700, "audit": 7500,  "tax": 2600}, # Business
    4000000:  {"total": 28800, "acct": 18200, "audit": 8000,  "tax": 2600}, # Business+
    5000000:  {"total": 37800, "acct": 23200, "audit": 12000, "tax": 2600}, # Enterprise
    7000000:  {"total": 42800, "acct": 27200, "audit": 13000, "tax": 2600}, # Enterprise+
    8000000:  {"total": 46600, "acct": 30000, "audit": 14000, "tax": 2600}, # Venture
    10000000: {"total": 55600, "acct": 32000, "audit": 21000, "tax": 2600}, # Venture+
    12000000: {"total": 60600, "acct": 33000, "audit": 25000, "tax": 2600}, # Growth
    15000000: {"total": 68600, "acct": 34000, "audit": 32000, "tax": 2600}, # Growth+
    20000000: {"total": 76100, "acct": 35000, "audit": 38500, "tax": 2600}, # Ascend
    25000000: {"total": 82600, "acct": 35000, "audit": 45000, "tax": 2600}, # Ascend+
}

# SECONDARY AUDIT: Max Turnover -> Audit Fee (Sign + Work)
# Source: Page 6 & 19 "Secondary list" for Silver/Gold [cite: 19]
SECONDARY_AUDIT_TIERS = {
    0: 2600, 250000: 4000, 500000: 5000, 1000000: 5000,
    2000000: 7000, 3000000: 7500, 4000000: 8000, 5000000: 12000,
    7000000: 13000, 8000000: 14000, 10000000: 21000, 12000000: 25000,
    15000000: 32000, 20000000: 38500, 25000000: 45000
}

# SILVER: Max Entries -> Monthly Fee
# Source: Page 8 & 24 "Silver" Table [cite: 24]
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
        return None, "Too many entries (>1,200)", {}
    
    for limit, details in BRONZE_DETAILED.items():
        if turnover <= limit:
            # We found the tier. Return total price + breakdown dictionary
            total_price = details["total"] + FIXED_FEES["BANK_CONF"]
            return total_price, "Eligible", details
            
    return None, "Turnover too high", {}

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

bronze_price, bronze_msg, bronze_details = get_bronze_price(turnover, annual_entries)
silver_total, silver_acct, silver_audit = get_silver_price(turnover, annual_entries)

# Calculate Gold Total (for upsell comparison)
gold_total = FIXED_FEES["GOLD_BASE_YR"] + silver_audit + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]

# DECISION ENGINE (PRIORITY ORDER)
recommended_package = "Silver"
rec_reason = ""
upsell_bullets = []
upsell_note = ""

# 1. GOLD CHEAPER THAN SILVER (High Volume Anomaly)
if gold_total < silver_total:
    recommended_package = "Gold"
    rec_reason = f"**Gold is HKD {silver_total - gold_total:,.0f} CHEAPER** than Silver due to high volume surcharges."

# 2. GOLD STRATEGIC UPGRADE (Within HKD 10,000)
elif (gold_total - silver_total) <= 10000:
    recommended_package = "Gold"
    diff = gold_total - silver_total
    rec_reason = f"**VIP Upgrade Opportunity:** Gold is only HKD {diff:,.0f} more than Silver."
    upsell_note = f"⚠️ **Note:** Silver is HKD {silver_total:,.0f}, but we recommend Gold for the advanced advisory services."
    upsell_bullets = [
        "**Tax Optimization:** Includes a yearly review to optimize Hong Kong tax position.",
        "**Financial Forecasts:** Yearly forecasting included (Critical for growth/banking).",
        "**Senior Oversight:** Account managed by a dedicated Senior Accountant.",
        "**Priority:** Highest priority processing (Jump Silver queue)."
    ]

# 3. SILVER CHEAPER THAN BRONZE (High Turnover / Low Volume)
elif bronze_price and silver_total < bronze_price:
    recommended_package = "Silver"
    rec_reason = f"Silver is **HKD {bronze_price - silver_total:,.0f} cheaper** than Bronze due to low volume."

# 4. SILVER STRATEGIC UPGRADE (Within HKD 3,000)
elif bronze_price and (silver_total - bronze_price) <= 3000:
    recommended_package = "Silver"
    diff = silver_total - bronze_price
    rec_reason = f"**Great Value Upgrade:** Silver is only HKD {diff:,.0f} more than Bronze."
    upsell_note = f"⚠️ **Note:** Bronze is technically cheaper (HKD {bronze_price:,.0f}), but we recommend Silver for superior monthly reporting."
    upsell_bullets = [
        "**Peace of Mind:** Athenasia pays fines if we are at fault (Bronze: You pay).",
        "**Dedicated Human:** Specific dedicated accountant (Bronze: Random assignment).",
        "**Higher Priority:** Silver clients jump the queue ahead of Bronze.",
        "**Visibility:** Monthly reports on Xero vs just once a year."
    ]

# 5. STANDARD BRONZE
elif bronze_price:
    recommended_package = "Bronze"
    rec_reason = "Client fits Bronze limits (Best Price)."

# 6. STANDARD SILVER (Fallback)
else:
    recommended_package = "Silver"
    rec_reason = "Client exceeds Bronze limits (1,200 entries)."

# --- DISPLAY RECOMMENDATION ---

if recommended_package == "Gold":
    st.warning(f"### 🏆 Recommendation: GOLD Package")
    st.markdown(f"**Reason:** {rec_reason}")
    if upsell_note:
        st.info(upsell_note)
    if upsell_bullets:
         st.markdown("**Why pay the extra?**")
         for bullet in upsell_bullets:
            st.markdown(f"- {bullet}")

elif recommended_package == "Bronze":
    st.success(f"### 💡 Recommendation: BRONZE Package")
    st.markdown(f"**Reason:** {rec_reason}")

else: # Silver
    st.info(f"### 💡 Recommendation: SILVER Package")
    st.markdown(f"**Reason:** {rec_reason}")
    if upsell_note:
        st.warning(upsell_note)
    if upsell_bullets:
        st.markdown(f"**Why pay the extra HKD {silver_total - (bronze_price if bronze_price else 0):,.0f}?**")
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
        
        # BRONZE BREAKDOWN
        with st.expander("Bronze Breakdown"):
            st.write(f"Acct: {bronze_details['acct']:,.0f}")
            st.write(f"Audit: {bronze_details['audit']:,.0f}")
            st.write(f"Tax: {bronze_details['tax']:,.0f}")
            st.write(f"Bank: {FIXED_FEES['BANK_CONF']:,.0f}")
            
    else:
        st.error(f"Not Eligible")
        st.caption(f"Reason: {bronze_msg}")

# 2. SILVER CARD
with col2:
    st.subheader("🥈 Silver (Monthly)")
    is_winner = (recommended_package == "Silver")
    st.metric(label="Total Annual Cost", value=f"HKD {silver_total:,.0f}", delta="Recommended" if is_winner else None)
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
    
    # Logic: Show GREEN if recommended, else normal
    is_gold_rec = (recommended_package == "Gold")
    
    if gold_total < silver_total:
        st.success(f"**PRO TIP:** Gold is actually **CHEAPER** than Silver!")
        st.metric("Gold Total", f"HKD {gold_total:,.0f}", delta=f"Save {silver_total - gold_total:,.0f}")
    elif is_gold_rec:
        st.success(f"**STRATEGIC UPGRADE RECOMMENDED**")
        st.metric("Gold Total", f"HKD {gold_total:,.0f}", delta=f"+ HKD {upgrade_gap:,.0f} vs Silver", delta_color="off")
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
