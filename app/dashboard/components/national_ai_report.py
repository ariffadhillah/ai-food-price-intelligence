import streamlit as st

from app.ai.executive_ai import generate_national_ai_report


def show_national_ai_report(
    scores,
    provinces,
    analytics,
):
    st.subheader("🤖 National AI Analyst")

    st.caption(
        "Analisis nasional otomatis berdasarkan commodity scores, "
        "province analytics, dan volatility metrics."
    )

    report = generate_national_ai_report(
        scores=scores,
        provinces=provinces,
        analytics=analytics,
    )

    status = report["market_status"]

    if status == "HIGH PRESSURE":
        st.error(f"National Market Status: **{status}**")
    elif status == "WATCHLIST":
        st.warning(f"National Market Status: **{status}**")
    else:
        st.success(f"National Market Status: **{status}**")

    st.markdown(report["headline"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Critical Provinces")

        for index, province in enumerate(
            report["critical_provinces"],
            start=1,
        ):
            st.markdown(f"{index}. **{province}**")

    with col2:
        st.markdown("### Critical Commodities")

        for index, commodity in enumerate(
            report["critical_commodities"],
            start=1,
        ):
            st.markdown(f"{index}. **{commodity}**")

    st.markdown("### Key Findings")

    for finding in report["key_findings"]:
        st.markdown(f"- {finding}")

    st.markdown("### Recommendations")

    for recommendation in report["recommendations"]:
        st.markdown(f"- {recommendation}")