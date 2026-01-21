import streamlit as st
import pandas as pd

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Athenasia Pricing Calculator", layout="wide")

st.title("ATHENASIA Pricing Calculator")
st.markdown("⚠️⚠️⚠️ FOR INTERNAL USE ONLY ⚠️⚠️⚠️")
st.divider()

# --- DATA TABLES (SOURCED FROM PRICE LIST 2026) ---

# BRONZE STANDARD: Max Turnover -> {Total, Accounting, Audit, Tax}
# Source: Page 5 "AAT PACKAGE YEARLY" Breakdown
# Note: "Total" in PDF matches sum of components.
BRONZE_TIERS = {
    0:        {"Limit": 0,        "Total": 5800,  "Acct": 2600,  "Audit": 600,   "Tax": 2600},
    250000:   {"Limit": 250000,   "Total": 9800,  "Acct": 3200,  "Audit": 4000,  "Tax": 2600},
    500000:   {"Limit": 500000,   "Total": 12800, "Acct": 5200,  "Audit": 5000,  "Tax": 2600},
    1000000:  {"Limit": 1000000,  "Total": 16800, "Acct": 9200,  "Audit": 5000,  "Tax": 2600},
    2000000:  {"Limit": 2000000,  "Total": 21300, "Acct": 11700, "Audit": 7000,  "Tax": 2600},
    3000000:  {"Limit": 3000000,  "Total": 25800, "Acct": 15700, "Audit": 7500,  "Tax": 2600},
    4000000:  {"Limit": 4000000,  "Total": 28800, "Acct": 18200, "Audit": 8000,  "Tax": 2600},
    5000000:  {"Limit": 5000000,  "Total": 37800, "Acct": 23200, "Audit": 12000, "Tax": 2600},
    7000000:  {"Limit": 7000000,  "Total": 42800, "Acct": 27200, "Audit": 13000, "Tax": 2600},
    8000000:  {"Limit": 8000000,  "Total": 46600, "Acct": 30000, "Audit": 14000, "Tax": 2600},
    10000000: {"Limit": 10000000, "Total": 55600, "Acct": 32000, "Audit": 21000, "Tax": 2600},
    12000000: {"Limit": 12000000, "Total": 60600, "Acct": 33000, "Audit": 25000, "Tax": 2600},
    15000000: {"Limit": 15000000, "Total": 68600, "Acct": 34000, "Audit": 32000, "Tax": 2600},
    20000000: {"Limit": 20000000, "Total": 76100, "Acct": 35000, "Audit": 38500, "Tax": 2600},
    25000000: {"Limit": 25000000, "Total": 82600, "Acct": 35000, "Audit": 45000, "Tax": 2600}
}

# SECONDARY AUDIT: Max Turnover -> Audit Fee (Sign + Work)
# Source: Page 6 & 19 "Secondary list" for Silver/Gold/Secondary Bronze
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
    "PLATINUM_BASE_YR": 600000, # Platinum starts at 50k/month
    [cite_start]"SEC_BRONZE_BASE": 8000, # Secondary Bronze Base Fee [cite: 18]
    [cite_start]"SEC_BRONZE_PER_TX": 25  # Secondary Bronze Per Entry Fee [cite: 18]
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
    # 1. Check Standard Bronze (AAT Package)
    std_price = None
    std_breakdown = {}
    
    if entries <= FIXED_FEES["BRONZE_LIMIT"]:
        for limit, data in BRONZE_TIERS.items():
            if turnover <= limit:
                # Calculate Breakdown
                std_price = data["Total"] + FIXED_FEES["BANK_CONF"]
                std_breakdown = {
                    "Acct": data["Acct"],
                    "Audit": data["Audit"],
                    "Tax": data["Tax"],
                    "Bank": FIXED_FEES["BANK_CONF"]
                }
                break

    # [cite_start]2. Check Secondary Bronze (Per Tx) [cite: 17, 18]
    # Formula: 8000 + (25 * Entries) + Audit + Tax + Bank
    sec_audit = 0
    if turnover > 25000000:
        sec_audit = 45000
    else:
        for limit, price in SECONDARY_AUDIT_TIERS.items():
            if turnover <= limit:
                sec_audit = price
                break
    
    sec_acct = FIXED_FEES["SEC_BRONZE_BASE"] + (FIXED_FEES["SEC_BRONZE_PER_TX"] * entries)
    sec_total = sec_acct + sec_audit + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]
    
    sec_breakdown = {
        "Acct": sec_acct,
        "Audit": sec_audit,
        "Tax": FIXED_FEES["TAX_REP"],
        "Bank": FIXED_FEES["BANK_CONF"]
    }

    # 3. Compare and Return Best Bronze Option
    # If Standard is eligible and cheaper, return Standard.
    # If Standard is NOT eligible (>1200 entries) or Secondary is cheaper, return Secondary.
    
    if std_price and std_price <= sec_total:
        return std_price, "Standard", std_breakdown
    else:
        # Return Secondary if it makes sense
        return sec_total, "Secondary (Per Tx)", sec_breakdown

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

bronze_price, bronze_type, bronze_bk = get_bronze_price(turnover, annual_entries)
silver_total, silver_acct, silver_audit = get_silver_price(turnover, annual_entries)
gold_total = FIXED_FEES["GOLD_BASE_YR"] + silver_audit + FIXED_FEES["TAX_REP"] + FIXED_FEES["BANK_CONF"]

# DECISION ENGINE
recommended_package = "Silver"
rec_reason = ""
upsell_bullets = []
upsell_note = ""

# 1. GOLD CHEAPER THAN SILVER
if gold_total < silver_total:
    recommended_package = "Gold"
    rec_reason = f"**Gold is HKD {silver_total - gold_total:,.0f} CHEAPER** than Silver due to high volume."

# 2. GOLD UPGRADE (<10k)
elif (gold_total - silver_total) <= 10000:
    recommended_package = "Gold"
    diff = gold_total - silver_total
    rec_reason = f"**VIP Upgrade Opportunity:** Gold is only HKD {diff:,.0f} more than Silver."
    upsell_note = f"⚠️ **Note:** Silver is HKD {silver_total:,.0f}, but we recommend Gold for advanced advisory."
    upsell_bullets = [
        "**Tax Optimization:** Includes yearly review.",
        "**Financial Forecasts:** Yearly forecasting included.",
        "**Senior Oversight:** Dedicated Senior Accountant.",
        "**Priority:** Jump Silver queue."
    ]

# 3. SILVER CHEAPER (Smart Save)
elif bronze_price and silver_total < bronze_price:
    recommended_package = "Silver"
    rec_reason = f"Silver is **HKD {bronze_price - silver_total:,.0f} cheaper** than Bronze due to low volume."

# 4. SILVER UPGRADE (<3k)
elif bronze_price and (silver_total - bronze_price) <= 3000:
    recommended_package = "Silver"
    diff = silver_total - bronze_price
    rec_reason = f"**Great Value Upgrade:** Silver is only HKD {diff:,.0f} more than Bronze."
    upsell_note = f"⚠️ **Note:** Bronze is technically cheaper (HKD {bronze_price:,.0f}), but we recommend Silver for monthly reporting."
    upsell_bullets = [
        "**Peace of Mind:** Athenasia pays fines if at fault.",
        "**Dedicated Human:** Dedicated accountant (Not random).",
        "**Higher Priority:** Silver jumps Bronze queue.",
        "**Visibility:** Monthly Xero reports."
    ]

# 5. BRONZE (Standard)
elif bronze_price:
    recommended_package = "Bronze"
    rec_reason = "Client fits Bronze limits and is cost-sensitive."

else:
    recommended_package = "Silver"
    rec_reason = "Client exceeds Bronze limits (1,200 entries)."

# --- DISPLAY RECOMMENDATION ---

if recommended_package == "Gold":
    st.warning(f"### 🏆 Recommendation: GOLD Package")
elif recommended_package == "Bronze":
    st.success(f"### 💡 Recommendation: BRONZE Package")
else: # Silver
    st.info(f"### 💡 Recommendation: SILVER Package")

st.markdown(f"**Reason:** {rec_reason}")

if upsell_note:
    st.info(upsell_note)
if upsell_bullets:
     st.markdown("**Why pay the extra?**")
     for bullet in upsell_bullets:
        st.markdown(f"- {bullet}")

st.divider()

# --- MAIN COMPARISON COLUMNS ---
col1, col2 = st.columns(2)

# 1. BRONZE CARD
with col1:
    st.subheader("🥉 Bronze")
    if bronze_price:
        is_winner = (recommended_package == "Bronze")
        st.metric(label="Total Annual Cost", value=f"HKD {bronze_price:,.0f}", delta="Lowest Price" if not is_winner else "Recommended")
        
        # Display Type (Standard vs Secondary)
        if bronze_type == "Secondary (Per Tx)":
            st.warning("Using 'Secondary List' (Per Transaction) Pricing")
            st.caption("Reason: Standard Bronze is capped at 1,200 entries OR Secondary is cheaper for high turnover.")
        else:
            st.write("Standard AAT Package")

        st.write("Yearly Reporting | Standard Priority")
        st.markdown("**Software:** Excel or Xero")
        
        # BRONZE BREAKDOWN
        with st.expander("Bronze Breakdown", expanded=False):
            st.write(f"Acct: {bronze_bk['Acct']:,.0f}")
            st.write(f"Audit: {bronze_bk['Audit']:,.0f}")
            st.write(f"Tax: {bronze_bk['Tax']:,.0f}")
            st.write(f"Bank: {bronze_bk['Bank']:,.0f}")
            if bronze_type == "Secondary (Per Tx)":
                st.caption(f"*Calc: 8000 Base + (25 x {annual_entries} entries)*")
    else:
        st.error(f"Not Eligible")

# 2. SILVER CARD
with col2:
    st.subheader("🥈 Silver")
    is_winner = (recommended_package == "Silver")
    st.metric(label="Total Annual Cost", value=f"HKD {silver_total:,.0f}", delta="Recommended" if is_winner else None)
    st.write("Monthly Reporting | Dedicated Accountant")
    st.markdown("**Software:** Xero (Charged Separately)")
    
    with st.expander("Silver Breakdown", expanded=False):
        st.write(f"Acct: {silver_acct:,.0f}")
        st.write(f"Audit: {silver_audit:,.0f}")
        st.write(f"Tax: {FIXED_FEES['TAX_REP']:,.0f}")
        st.write(f"Bank: {FIXED_FEES['BANK_CONF']:,.0f}")
        st.caption("*Plus Xero Subscription fee (billed separately)*")
        if annual_entries > 24000:
            st.warning(f"⚠️ Volume Surcharge: +{(annual_entries-24000)*5:,.0f}")

# --- PREMIUM UPGRADES ---
st.markdown("---")
st.subheader("🚀 Premium Upgrades")
upgrade_gap = gold_total - silver_total
col_gold, col_plat = st.columns(2)

with col_gold:
    st.markdown("#### 🥇 Upgrade to Gold")
    
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
    * ✅ **Financial Forecasts** (Yearly)
    * ✅ **Tax Optimization Review**
    * ✅ **Higher Priority** (Jump Queue)
    """)

with col_plat:
    st.markdown("#### 💎 Upgrade to Platinum")
    plat_price = FIXED_FEES["PLATINUM_BASE_YR"] + silver_audit
    st.metric("Starting Price", f"HKD {plat_price:,.0f}+")
    st.markdown("""
    * ✅ **Dr. Timmermans Oversight**
    * ✅ **Highest Priority**
    * ✅ **Complex Tax Advisory**
    """)
