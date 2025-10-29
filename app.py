"""
Streamlit dashboard for YouTube Shorts moderation review
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime
from schemas import ShortMetadata, ModerationResult
from engine import get_engine
from decision import decision_logic
import traceback

st.set_page_config(
    page_title="YouTube Shorts Moderator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🛡️ YouTube Shorts Content Moderator")
st.markdown("**AI-powered Trust & Safety content classification system**")

# ============ SIDEBAR CONTROLS ============
with st.sidebar:
    st.header("⚙️ Controls")
    mode = st.radio("Mode", ["Single Short", "Batch Upload", "Results Viewer"])

    st.divider()
    st.subheader("📊 System Info")
    st.info("""
    - **Model:** facebook/bart-large-mnli (Zero-Shot)
    - **Categories:** 7 policy types
    - **Processing:** Rule-Based + NLI
    - **Device:** CPU
    """)

# ============ SINGLE SHORT MODE ============
if mode == "Single Short":
    st.subheader("📹 Single Short Analysis")

    col1, col2 = st.columns(2)

    with col1:
        short_id = st.text_input("Short ID", value="short_demo_001")
        title = st.text_area("Title", value="Free money method! Click now!!!", height=50)

    with col2:
        description = st.text_area("Description", value="DM for details", height=50)
        transcript = st.text_area("Transcript", value="Send $50 and I'll double it", height=50)

    col3, col4 = st.columns(2)
    with col3:
        channel_name = st.text_input("Channel Name", value="QuickMoney123")
        upload_date = st.date_input("Upload Date")

    with col4:
        view_count = st.number_input("View Count", value=5000)
        language = st.selectbox("Language", ["en", "es", "hi", "pt"])

    comments_text = st.text_area("Top Comments (one per line)", value="This is a scam!\nReported.", height=80)
    top_comments = [c.strip() for c in comments_text.split("\n") if c.strip()]

    if st.button("🔍 Analyze", key="analyze_single", type="primary"):
        try:
            st.info("⏳ Processing...")

            # Create input
            short_data = {
                "short_id": short_id,
                "title": title,
                "description": description,
                "transcript": transcript,
                "top_comments": top_comments,
                "channel_name": channel_name,
                "upload_date": str(upload_date),
                "view_count": int(view_count),
                "language": language
            }

            # Validate
            validated = ShortMetadata(**short_data)

            # Process
            engine = get_engine()
            moderation_result = engine.moderate(validated.dict())
            result = decision_logic.create_result(validated.dict(), moderation_result)

            # Display results
            st.success("✓ Analysis complete")

            # Summary cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                decision_color = {
                    "APPROVED": "🟢",
                    "AGE_RESTRICT": "🟡",
                    "REMOVE": "🔴",
                    "ESCALATE_TO_HUMAN": "🟠",
                    "NEED_MORE_CONTEXT": "⚪"
                }
                st.metric("Decision", decision_color.get(result.overall_decision, "") + " " + result.overall_decision)

            with col2:
                st.metric("Confidence", f"{result.confidence_score:.1%}")

            with col3:
                st.metric("Primary Violation", result.primary_violation)

            with col4:
                st.metric("Escalation", result.escalation_priority)

            st.divider()

            # Category breakdown
            st.subheader("📊 Category Scores")
            category_data = []
            for cat, score_obj in result.categories.items():
                category_data.append({
                    "Category": cat,
                    "Risk Level": score_obj.risk_level,
                    "Score": f"{score_obj.score:.2%}",
                    "Evidence": ", ".join(score_obj.evidence) if score_obj.evidence else "—"
                })

            df = pd.DataFrame(category_data)
            st.dataframe(df, use_container_width=True)

            # Detailed analysis
            st.subheader("📝 Human Reviewer Notes")
            st.info(result.notes_for_human_reviewer)

            # Action recommendation
            st.subheader("✏️ Action Recommendation")
            st.success(result.action_recommendation)

            # JSON output
            with st.expander("📄 Raw JSON Output"):
                st.json(result.dict())

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.error(traceback.format_exc())

# ============ BATCH UPLOAD MODE ============
elif mode == "Batch Upload":
    st.subheader("📦 Batch Processing")

    uploaded_file = st.file_uploader("Upload JSON file", type=["json"])

    if uploaded_file and st.button("🚀 Process Batch"):
        try:
            st.info("⏳ Processing batch...")

            # Load JSON
            batch_data = json.load(uploaded_file)
            shorts = batch_data if isinstance(batch_data, list) else batch_data.get("shorts", [])

            # Process each
            engine = get_engine()
            results = []

            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, short in enumerate(shorts):
                status_text.text(f"Processing {idx+1}/{len(shorts)}...")

                try:
                    validated = ShortMetadata(**short)
                    mod_result = engine.moderate(validated.dict())
                    result = decision_logic.create_result(validated.dict(), mod_result)
                    results.append(result)
                except Exception as e:
                    st.warning(f"Skipped {short.get('short_id', '?')}: {str(e)}")

                progress_bar.progress((idx + 1) / len(shorts))

            status_text.text(f"✓ Processed {len(results)}/{len(shorts)}")

            # Summary stats
            col1, col2, col3, col4, col5 = st.columns(5)
            decisions = [r.overall_decision for r in results]

            with col1:
                st.metric("Total", len(results))
            with col2:
                st.metric("Approved", decisions.count("APPROVED"))
            with col3:
                st.metric("Removed", decisions.count("REMOVE"))
            with col4:
                st.metric("Age Restrict", decisions.count("AGE_RESTRICT"))
            with col5:
                st.metric("Escalate", decisions.count("ESCALATE_TO_HUMAN"))

            st.divider()

            # Results table
            st.subheader("📋 Results")
            result_data = []
            for r in results:
                result_data.append({
                    "Short ID": r.short_id,
                    "Decision": r.overall_decision,
                    "Confidence": f"{r.confidence_score:.1%}",
                    "Primary Violation": r.primary_violation,
                    "Escalation": r.escalation_priority
                })

            result_df = pd.DataFrame(result_data)
            st.dataframe(result_df, use_container_width=True)

            # Download results
            output_json = [r.dict() for r in results]
            st.download_button(
                label="📥 Download Results (JSON)",
                data=json.dumps(output_json, indent=2),
                file_name=f"moderation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============ RESULTS VIEWER MODE ============
elif mode == "Results Viewer":
    st.subheader("📊 Previous Results Viewer")

    uploaded_file = st.file_uploader("Upload results JSON", type=["json"])

    if uploaded_file:
        results_data = json.load(uploaded_file)

        if isinstance(results_data, list):
            results_list = results_data
        else:
            results_list = results_data.get("results", [])

        st.success(f"Loaded {len(results_list)} results")

        # Filter
        col1, col2, col3 = st.columns(3)

        with col1:
            decision_filter = st.multiselect("Decision", 
                ["APPROVED", "REMOVE", "AGE_RESTRICT", "ESCALATE_TO_HUMAN"],
                default=["REMOVE", "ESCALATE_TO_HUMAN"])

        with col2:
            priority_filter = st.multiselect("Escalation Priority",
                ["P0", "P1", "P2", "P3"],
                default=["P0", "P1"])

        with col3:
            min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.5)

        # Filter results
        filtered = [r for r in results_list 
                   if r.get("overall_decision") in decision_filter 
                   and r.get("escalation_priority") in priority_filter
                   and r.get("confidence_score", 0) >= min_confidence]

        st.subheader(f"Filtered Results ({len(filtered)})")

        for result in filtered[:20]:  # Show max 20
            with st.expander(f"{result.get('short_id')} - {result.get('overall_decision')} ({result.get('confidence_score'):.1%})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Decision:** {result.get('overall_decision')}")
                    st.write(f"**Confidence:** {result.get('confidence_score'):.1%}")
                    st.write(f"**Primary Violation:** {result.get('primary_violation')}")

                with col2:
                    st.write(f"**Escalation:** {result.get('escalation_priority')}")
                    st.write(f"**Action:** {result.get('action_recommendation')}")

                st.info(result.get('notes_for_human_reviewer'))

                with st.expander("View Full JSON"):
                    st.json(result)

st.divider()
st.markdown("---")
st.markdown("""
**Disclaimer:** This is a prototype moderation system. Final decisions should involve human review.
Not for production use without additional validation and legal review.
""")
