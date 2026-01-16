# --- MAIN DISPLAY ---

bronze_price, bronze_msg = get_bronze_price(turnover, annual_entries)
silver_total, silver_acct, silver_audit = get_silver_price(turnover, annual_entries)

# 1. RECOMMENDATION ENGINE
if bronze_price and silver_total < bronze_price:
    # SCENARIO: Silver is actually CHEAPER than Bronze (High Turnover, Low Volume)
    st.warning(f"### ⚠️ SMART SAVE ALERT: SILVER IS CHEAPER!")
    st.markdown(f"""
    **You should recommend SILVER.**
    - It is **HKD {bronze_price - silver_total:,.0f} cheaper** than Bronze.
    - The client gets **Monthly Reporting** (Better value).
    - This happens because their volume is low ({annual_entries} entries), keeping the accounting fee small.
    """)
    recommended_package = "Silver"

elif bronze_price:
    st.success(f"### 💡 Recommendation: BRONZE Package")
    st.markdown("This client fits within the Bronze limits and saves money.")
    recommended_package = "Bronze"

else:
    st.info(f"### 💡 Recommendation: SILVER Package")
    st.markdown("Client exceeds Bronze volume limits (1,200 entries). Silver is required.")
    recommended_package = "Silver"

st.divider()

# 2. PACKAGE CARDS
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("🥉 Bronze")
    if bronze_price:
        st.metric(label="Total Annual Cost", value=f"HKD {bronze_price:,.0f}")
        st.write(f"**Status:** {bronze_msg}")
        st.caption("Bundled Fee (Accounting + Audit + Tax)") # Added caption to explain why no breakdown
    else:
        st.error(f"Not Available: {bronze_msg}")
        st.write("Bronze is capped at 1,200 entries/year.")

with col_b:
    st.subheader("🥈 Silver")
    # Highlight the price green if it's the winner
    if recommended_package == "Silver":
        st.metric(label="Total Annual Cost", value=f"HKD {silver_total:,.0f}", delta="Best Value")
    else:
        st.metric(label="Total Annual Cost", value=f"HKD {silver_total:,.0f}")
    
    with st.expander("See Cost Breakdown"):
        st.write(f"**Accounting:** HKD {silver_acct:,.0f} /yr")
        st.write(f"**Audit:** HKD {silver_audit:,.0f}")
        st.write(f"**Tax Rep:** HKD {FIXED_FEES['TAX_REP']:,.0f}")
        st.write(f"**Bank Confirm:** HKD {FIXED_FEES['BANK_CONF']:,.0f}")
