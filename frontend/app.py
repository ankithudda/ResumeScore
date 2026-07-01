import streamlit as st
import requests
import plotly.graph_objects as go
import json
import os

# ==========================================
# CONFIGURATION & HELPERS
# ==========================================
st.set_page_config(page_title="ResumeScore", page_icon="📄", layout="wide")

API_BASE_URL = os.getenv("RESUMESCORE_API_URL", "http://127.0.0.1:8000")

def fetch_from_api(endpoint: str, files: dict = None, data: dict = None):
    """Centralized API network handler to prevent DRY violations across tabs."""
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", files=files, data=data)
        if response.status_code == 200:
            return response.json(), None
        return None, f"Server Error {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Connection Failure: {str(e)}"

def render_fit_verdict(verdict: str, feedback: str):
    label = f"**AI Fit Verdict:** {verdict or 'Unknown'}"
    body = f"{label}\n\n{feedback}" if feedback else label
    verdict_lower = (verdict or "").lower()
    if "strong" in verdict_lower:
        st.success(body)
    elif "moderate" in verdict_lower:
        st.warning(body)
    elif "weak" in verdict_lower:
        st.error(body)
    else:
        st.info(body)

# ==========================================
# UI HEADER
# ==========================================
st.title("📄 ResumeScore")
st.markdown("AI-powered resume screening and career preparation platform")
st.divider()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Resume Analysis", 
    "✍️ Cover Letter Generator", 
    "🎯 Interview Prep",
    "🛣️ Learning Roadmap",
    "⚖️ Job Matcher",
    "📋 Batch Candidate Ranking"
])

# ==========================================
# TAB 1: RESUME ANALYSIS 
# ==========================================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"], key="analysis_pdf")
        
    with col2:
        st.subheader("Job Description")
        job_description = st.text_area("Paste the job description here", height=200, key="analysis_jd")
        analyze_btn = st.button("🔍 Analyze Resume", type="primary", use_container_width=True)

        if analyze_btn:
            if not uploaded_file or not job_description.strip():
                st.error("Please provide both a PDF resume and a job description.")
            else:
                with st.spinner("Analyzing resume... this may take 10-15 seconds"):
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    data = {"job_description": job_description}
                    
                    result, error = fetch_from_api("/api/analysis/full", files=files, data=data)
                    
                    if error:
                        st.error(error)
                    else:
                        tfidf = result.get("tfidf_analysis", {})
                        ai = result.get("ai_analysis", {})
                        score = tfidf.get("match_score", 0)

                        st.divider()
                        st.subheader("📊 Analysis Results")
                        render_fit_verdict(ai.get("fit_verdict", ""), ai.get("overall_feedback", ""))

                        col1_res, col2_res = st.columns(2)
                        with col1_res:
                            fig = go.Figure(go.Indicator(
                                mode="gauge+number", 
                                value=score, 
                                title={"text":"Match Score"},
                                gauge={
                                    "axis": {"range": [0, 100]},
                                    "bar": {"color": "royalblue"},
                                    "steps": [
                                        {"range": [0, 40], "color": "red"},
                                        {"range": [40, 70], "color": "orange"},
                                        {"range": [70, 100], "color": "green"}
                                    ]
                                }
                            ))
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})
                            
                        with col2_res:
                            st.subheader("✅ Strengths")
                            for s in ai.get("strengths", []): st.success(s)
                            st.subheader("⚠️ Improvements Needed")
                            for i in ai.get("improvements", []): st.warning(i)
                                
                        st.subheader("🔍 Missing Keywords")
                        keywords = tfidf.get("missing_keywords", [])
                        if keywords:
                            st.write(" ".join([f"`{k}`" for k in keywords]))
                        else:
                            st.success("No critical keywords missing!")

                        st.subheader("📋 ATS Optimization Tips")
                        ats_tips = ai.get("ats_tips", [])
                        if ats_tips:
                            for tip in ats_tips:
                                st.info(tip)
                        else:
                            st.caption("No ATS tips returned.")

# ==========================================
# TAB 2: COVER LETTER GENERATOR
# ==========================================
with tab2:
    st.header("✍️Generate a Tailored Cover Letter")
    cl_col1, cl_col2 = st.columns(2)
    
    with cl_col1:
        cl_file = st.file_uploader("Upload your PDF resume", type=["pdf"], key="cl_pdf")
        cl_company = st.text_input("Target Company Name", key="cl_comp")
        
    with cl_col2:
        cl_jd = st.text_area("Target Job Description", height=230, key="cl_jd")
        
    generate_cl_btn = st.button("✨ Generate Cover Letter", type="primary", use_container_width=True)
    
    if generate_cl_btn:
        if not cl_file or not cl_company.strip() or not cl_jd.strip():
            st.error("Please complete all fields.")
        else:
            with st.spinner("Drafting your personalized cover letter..."):
                files = {"file": (cl_file.name, cl_file.getvalue(), "application/pdf")}
                data = {"job_description": cl_jd, "company_name": cl_company}
                
                payload, error = fetch_from_api("/api/cover-letter", files=files, data=data)
                
                if error:
                    st.error(error)
                else:
                    cl_result = payload.get("cover_letter_result", {})
                    st.success(f"Generated successfully! (Word count: {cl_result.get('word_count', 0)})")
                    st.text_area(label="Copy Output:", value=cl_result.get("cover_letter", ""), height=400)

# ==========================================
# TAB 3: INTERVIEW PREPARATION
# ==========================================
with tab3:
    st.header("🎯 Customized Interview Simulator")
    int_col1, int_col2 = st.columns(2)
    
    with int_col1:
        int_file = st.file_uploader("Upload your PDF resume", type=["pdf"], key="interview_pdf")
    with int_col2:
        int_jd = st.text_area("Target Job Description", height=200, key="interview_jd")
        
    generate_int_btn = st.button("🚀 Generate Interview Practice Questions", type="primary", use_container_width=True)
    
    if generate_int_btn:
        if not int_file or not int_jd.strip():
            st.error("Please provide both a PDF resume and a job description.")
        else:
            with st.spinner("Analyzing profile alignment and creating questions..."):
                files = {"file": (int_file.name, int_file.getvalue(), "application/pdf")}
                data = {"job_description": int_jd}
                
                payload, error = fetch_from_api("/api/interview-prep", files=files, data=data)
                
                if error:
                    st.error(error)
                else:
                    questions_list = payload.get("interview_prep", [])
                    if not questions_list:
                        st.warning("The model did not return any structured questions. Try again.")
                    else:
                        st.success("Practice set ready!")
                        st.divider()
                        for item in questions_list:
                            with st.expander(f"Q{item.get('id')}: [{item.get('type')}] — {item.get('question')}"):
                                st.markdown(f"**💡 Evaluator Intent:** *{item.get('intent')}*")
                                st.info(f"**🎯 Recommended Talking Points:**\n{item.get('suggested_talking_points')}")

# ==========================================
# TAB 4: LEARNING ROADMAP
# ==========================================
with tab4:
    st.header("🛣️ Personalized Learning Roadmap")
    rd_col1, rd_col2 = st.columns(2)
    
    with rd_col1:
        rd_pdf = st.file_uploader("Upload your PDF resume", type=["pdf"], key="roadmap_pdf")
    with rd_col2:
        rd_jd = st.text_area("Target Job Description Layout", height=200, key="roadmap_jd")
        
    generate_rd_btn = st.button("🗺️ Generate Custom Execution Roadmap", type="primary", use_container_width=True)
    
    if generate_rd_btn:
        if not rd_pdf or not rd_jd.strip():
            st.warning("Please provide both a PDF resume and a job description.")
        else:
            with st.spinner("Assembling 90-day execution plan..."):
                files = {"file": (rd_pdf.name, rd_pdf.getvalue(), "application/pdf")}
                data = {"job_description": rd_jd}
                
                payload, error = fetch_from_api("/api/roadmap", files=files, data=data)
                
                if error:
                    st.error(error)
                else:
                    st.success("90-Day Roadmap generated successfully!")
                    st.divider()
                    
                    st.subheader("🏁 Phase-by-Phase Upskilling Path")
                    for step in payload.get("milestones", []):
                        with st.container(border=True):
                            st.markdown(f"### ⚡ {step.get('phase')}: **{step.get('focus_area')}**")
                            for action in step.get("action_items", []): st.markdown(f"- {action}")
                                    
                    st.divider()
                    st.subheader("📚 Curated Cross-Sector Resources")
                    for resource in payload.get("resources", []):
                        st.info(f"**{resource.get('name')}**: {resource.get('reasoning')}")

# ==========================================
# TAB 5: JOB MATCHER
# ==========================================
with tab5:
    st.header("⚖️ Multi-Role Fit Analyzer")
    jm_col1, jm_col2 = st.columns([1, 1.5])
    
    with jm_col1:
        jm_pdf = st.file_uploader("Upload your PDF resume", type=["pdf"], key="jm_pdf")
    with jm_col2:
        jd_list = []
        with st.expander("Job Description 1 (Required)", expanded=True):
            jd1_label = st.text_input("Role Title", key="jd1_label")
            jd1_text = st.text_area("Description", height=100, key="jd1_text")
            if jd1_label and jd1_text: jd_list.append({"label": jd1_label, "text": jd1_text})
                
        with st.expander("Job Description 2 (Optional)"):
            jd2_label = st.text_input("Role Title", key="jd2_label")
            jd2_text = st.text_area("Description", height=100, key="jd2_text")
            if jd2_label and jd2_text: jd_list.append({"label": jd2_label, "text": jd2_text})

    match_jobs_btn = st.button("🏆 Find My Best Match", type="primary", use_container_width=True)
    
    if match_jobs_btn:
        if not jm_pdf or len(jd_list) == 0:
            st.warning("Please upload a resume and provide at least one valid Job Description.")
        else:
            with st.spinner("Running cascade ranking..."):
                files = {"file": (jm_pdf.name, jm_pdf.getvalue(), "application/pdf")}
                data = {"jobs_json": json.dumps(jd_list)}
                
                payload, error = fetch_from_api("/api/job-matcher", files=files, data=data)
                
                if error:
                    st.error(error)
                else:
                    rankings = payload.get("rankings", [])
                    best_match = payload.get("best_match_analysis", {})
                    
                    st.success("Cascade Ranking Complete!")
                    st.divider()
                    
                    res_col1, res_col2 = st.columns([1, 2])
                    with res_col1:
                        st.subheader("📊 Leaderboard")
                        for idx, rank in enumerate(rankings):
                            st.write(f"#{idx+1} **{rank['label']}** - {rank['match_score']:.1f}%")
                                
                    with res_col2:
                        st.subheader(f"🧠 Deep Analysis: {best_match.get('label')}")
                        st.markdown(f"**Why it's your best fit:** {best_match.get('why_best_fit')}")
                        st.markdown("**Core Strengths:**")
                        for s in best_match.get("key_strengths_for_this_role", []): st.markdown(f"- {s}")
                        st.markdown("**Watch Out For:**")
                        for g in best_match.get("watch_out_for", []): st.markdown(f"- ⚠️ {g}")

# ==========================================
# TAB 6: BATCH RANKING
# ==========================================
with tab6:
    st.header("📋 Batch Candidate Ranking")
    br_col1, br_col2 = st.columns(2)

    with br_col1:
        br_files = st.file_uploader("Upload resume PDFs (up to 10)", type=["pdf"], accept_multiple_files=True, key="batch_pdfs")
    with br_col2:
        br_jd = st.text_area("Target Job Description", height=200, key="batch_jd")

    rank_btn = st.button("🏆 Rank Candidates", type="primary", use_container_width=True)

    if rank_btn:
        if not br_files or not br_jd.strip():
            st.error("Please provide resumes and a job description.")
        else:
            with st.spinner(f"Scoring {len(br_files)} resumes..."):
                files_payload = [("files", (f.name, f.getvalue(), "application/pdf")) for f in br_files]
                payload, error = fetch_from_api("/api/batch-ranking", files=files_payload, data={"job_description": br_jd})

                if error:
                    st.error(error)
                else:
                    st.success(f"Ranked {len(payload.get('rankings', []))} candidate(s)!")
                    st.divider()

                    st.subheader("🏆 Leaderboard")
                    for i, r in enumerate(payload.get("rankings", [])):
                        st.write(f"#{i + 1} **{r['filename']}** — {r['match_score']}% ({r['strength']})")

                    if payload.get("top_candidates_analysis"):
                        st.divider()
                        st.subheader("🔍 Shortlist Analysis")
                        for analysis in payload.get("top_candidates_analysis", []):
                            with st.expander(f"📄 {analysis.get('display_id')}"):
                                for s in analysis.get("strengths", []): st.success(s)
                                for c in analysis.get("concerns", []): st.warning(c)
                                st.markdown(f"**🎯 Recommendation:** {analysis.get('recommendation')}")