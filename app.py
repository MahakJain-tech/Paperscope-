import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ── Page config ──────────────────────────────────────────────────────
st.set_page_config(page_title="PaperScope", page_icon="📘", layout="wide")

# Small CSS for the blue-border KPI cards on the Home page
st.markdown("""<style>
.card{background:#f0f4ff;border-left:6px solid #2563eb;border-radius:8px;padding:14px 18px;margin-bottom:8px}
.clabel{font-size:13px;color:#475569}.cval{font-size:30px;font-weight:bold;color:#1e3a8a}
</style>""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────
q  = pd.read_csv("questions.csv")        # all exam questions
p  = pd.read_csv("question_papers.csv")  # paper metadata
sy = pd.read_csv("syllabus.csv")         # syllabus topics

# ── Sidebar navigation & filters ─────────────────────────────────────
st.sidebar.title("📘 PaperScope")
page = st.sidebar.radio("Go to", [" Home", " Questions", " Topic Analysis",
                                   " Unit Analysis", " Charts", " Upload New"])
st.sidebar.subheader("Filters")
sub  = st.sidebar.selectbox("Subject",       ["All"] + sorted(q["subject"].unique().tolist()))
sem  = st.sidebar.selectbox("Semester",      ["All"] + sorted(q["semester"].unique().tolist()))
yr   = st.sidebar.selectbox("Academic Year", ["All"] + sorted(q["academic_year"].unique().tolist()))
unit = st.sidebar.selectbox("Unit",          ["All"] + sorted(q["unit"].unique().tolist()))

# ── Apply filters ─────────────────────────────────────────────────────
fq = q.copy()                               # fq = filtered questions
if sub  != "All": fq = fq[fq["subject"]       == sub]
if sem  != "All": fq = fq[fq["semester"]       == sem]
if yr   != "All": fq = fq[fq["academic_year"]  == yr]
if unit != "All": fq = fq[fq["unit"]           == unit]

fp = p.copy()                               # fp = filtered papers
if sub != "All": fp = fp[fp["subject"]       == sub]
if sem != "All": fp = fp[fp["semester"]      == sem]
if yr  != "All": fp = fp[fp["academic_year"] == yr]

# helper: one KPI card
def card(label, value):
    st.markdown(f'<div class="card"><div class="clabel">{label}</div><div class="cval">{value}</div></div>',
                unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 🏠 HOME
# ═══════════════════════════════════════════════════════════
if page == " Home":
    st.title(" PaperScope – Previous Question Paper Analysis")
    st.write("Explore previous exam questions, repeated topics and unit-wise marks. Use the sidebar filters to narrow results.")
    st.divider()

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1: card(" Question Papers", len(fp))
    with c2: card(" Total Questions",  len(fq))
    with c3: card(" Subjects",         fq["subject"].nunique() if len(fq) else 0)
    with c4: card(" Syllabus Units",   sy["unit"].nunique())

    if len(fq) > 0:
        st.divider()
        st.subheader("Quick Insights")
        col1, col2, col3 = st.columns(3)
        col1.info(f" Most Repeated Topic: **{fq['topic'].value_counts().idxmax()}** ({fq['topic'].value_counts().max()} times)")
        col2.info(f" Top Unit by Marks: **{fq.groupby('unit')['marks'].sum().idxmax()}**")
        col3.info(f" Total Marks Analysed: **{int(fq['marks'].sum())}**")

    st.subheader("Question Papers")
    st.dataframe(fp, width="stretch", hide_index=True)

# ═══════════════════════════════════════════════════════════
# 📄 QUESTIONS
# ═══════════════════════════════════════════════════════════
elif page == " Questions":
    st.title(" Question Paper Analysis")
    topics     = ["All"] + sorted(fq["topic"].unique().tolist()) if len(fq) else ["All"]
    sel_topic  = st.selectbox("Filter by Topic", topics)
    keyword    = st.text_input(" Search by keyword", placeholder="e.g. stack, SQL, deadlock")

    result = fq.copy()
    if sel_topic != "All":
        result = result[result["topic"] == sel_topic]
    if keyword.strip():
        kw = keyword.strip().lower()
        result = result[result["question_text"].str.lower().str.contains(kw) |
                        result["topic"].str.lower().str.contains(kw)]

    st.caption(f"Showing {len(result)} question(s)")
    st.dataframe(result[["question_id","paper_id","subject","academic_year","unit","topic","question_type","marks","question_text"]],
                 width="stretch", hide_index=True)

# ═══════════════════════════════════════════════════════════
#  TOPIC ANALYSIS
# ═══════════════════════════════════════════════════════════
elif page == " Topic Analysis":
    st.title(" Topic Analysis")
    if len(fq) == 0:
        st.info("No data for selected filters.")
    else:
        summary = fq.groupby("topic").agg(Subject=("subject","first"), Unit=("unit","first"),
                              Times_Asked=("topic","count"), Total_Marks=("marks","sum")
                              ).reset_index().sort_values("Times_Asked", ascending=False)

        tab1, tab2 = st.tabs([" All Topics", " Topic History"])

        with tab1:
            st.write("Topics sorted by how often they appeared in exams.")
            st.dataframe(summary, width="stretch", hide_index=True)

        with tab2:
            chosen  = st.selectbox("Select a topic", summary["topic"].tolist())
            syl_row = sy[sy["topic"] == chosen]
            if len(syl_row):
                st.info(f" **{syl_row.iloc[0]['subtopic']}** — {syl_row.iloc[0]['description']}")
            history = fq[fq["topic"] == chosen].sort_values("academic_year")
            st.metric("Total Appearances", len(history))
            st.dataframe(history[["academic_year","paper_id","question_type","marks","question_text"]],
                         width="stretch", hide_index=True)

# ═══════════════════════════════════════════════════════════
#  UNIT ANALYSIS
# ═══════════════════════════════════════════════════════════
elif page == " Unit Analysis":
    st.title(" Unit-wise Analysis")
    if len(fq) == 0:
        st.info("No data for selected filters.")
    else:
        unit_df = fq.groupby("unit").agg(Questions=("question_id","count"),
                              Total_Marks=("marks","sum"), Avg_Marks=("marks","mean")
                              ).reset_index()
        col1, col2 = st.columns([1.2, 1])
        with col1:
            st.subheader("Unit Summary")
            st.dataframe(unit_df, width="stretch", hide_index=True)
        with col2:
            st.subheader("Questions per Unit")
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.bar(unit_df["unit"], unit_df["Questions"], color="#2563eb")
            ax.set_xlabel("Unit"); ax.set_ylabel("Questions"); plt.xticks(rotation=15, fontsize=7); plt.tight_layout()
            st.pyplot(fig); plt.close(fig)

        st.divider()
        st.subheader("Year-wise Breakdown")
        st.dataframe(pd.crosstab(fq["unit"], fq["academic_year"], margins=True, margins_name="Total"), width="stretch")

# ═══════════════════════════════════════════════════════════
#  CHARTS
# ═══════════════════════════════════════════════════════════
elif page == " Charts":
    st.title(" Visualisations")
    if len(fq) == 0:
        st.info("No data to plot. Change sidebar filters.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Unit-wise Questions")
            uc = fq["unit"].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(5,4)); ax.bar(uc.index, uc.values, color="#2563eb")
            ax.set_xlabel("Unit"); ax.set_ylabel("Questions"); plt.xticks(rotation=12,fontsize=7); plt.tight_layout()
            st.pyplot(fig); plt.close(fig)

        with col2:
            st.subheader("2. Question Type Distribution")
            tc = fq["question_type"].value_counts()
            fig, ax = plt.subplots(figsize=(5,4))
            ax.pie(tc.values, labels=tc.index, autopct="%1.1f%%", startangle=140,
                   colors=["#2563eb","#0ea5e9","#10b981","#f59e0b"])
            plt.tight_layout(); st.pyplot(fig); plt.close(fig)

        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            st.subheader("3. Year-wise Frequency")
            yc = fq["academic_year"].value_counts().sort_index()
            fig, ax = plt.subplots(figsize=(5,4)); ax.plot(yc.index, yc.values, marker="o", color="#0284c7", linewidth=2)
            ax.set_xlabel("Year"); ax.set_ylabel("Questions"); plt.xticks(rotation=15,fontsize=7); plt.tight_layout()
            st.pyplot(fig); plt.close(fig)

        with col4:
            st.subheader("4. Top Repeated Topics")
            tt = fq["topic"].value_counts().head(8).sort_values()
            fig, ax = plt.subplots(figsize=(5,4)); ax.barh(tt.index, tt.values, color="#0d9488")
            ax.set_xlabel("Times Asked"); plt.tight_layout(); st.pyplot(fig); plt.close(fig)

        st.divider()
        st.subheader("5. Marks Distribution")
        fig, ax = plt.subplots(figsize=(7,4)); ax.hist(fq["marks"], bins=6, color="#4f46e5", edgecolor="white")
        ax.set_xlabel("Marks"); ax.set_ylabel("Questions"); plt.tight_layout()
        st.pyplot(fig); plt.close(fig)

# ═══════════════════════════════════════════════════════════
# Upload New
# ═══════════════════════════════════════════════════════════
elif page == " Upload New":
    st.title(" File Upload & Data Management")
    st.write("Upload CSV/PDF files, add new records manually, or edit and delete existing data.")

    tab1, tab2, tab3 = st.tabs(["📂 Upload Files", "➕ Add Records", "✏️ Edit / Delete"])

    # ── TAB 1: UPLOAD ────────────────────────────────────────
    with tab1:
        st.subheader("Upload a CSV or PDF File")
        file_for = st.radio("This file contains:", ["Questions","Question Papers","Syllabus"], horizontal=True)
        uploaded = st.file_uploader("Choose CSV or PDF", type=["csv","pdf"])

        if uploaded:
            if uploaded.name.endswith(".pdf"):
                try:
                    import pymupdf
                    doc  = pymupdf.open(stream=uploaded.read(), filetype="pdf")
                    text = "".join(pg.get_text() for pg in doc)   # join text from all pages
                    st.text_area(" Extracted Text", text, height=300)
                    st.info("Copy the questions above, paste into a CSV, then re-upload as CSV.")
                except ImportError:
                    st.error("Run: pip install pymupdf")
            else:
                new_df = pd.read_csv(uploaded)
                st.write(f" {len(new_df)} rows loaded"); st.dataframe(new_df, width="stretch", hide_index=True)
                # required columns for each file type
                cols = {"Questions":["question_id","paper_id","subject","semester","academic_year",
                                     "question_text","unit","topic","question_type","marks"],
                        "Question Papers":["paper_id","subject","semester","academic_year","exam_type","total_marks"],
                        "Syllabus":["subject","unit","topic","subtopic","description"]}
                paths = {"Questions":"questions.csv","Question Papers":"question_papers.csv","Syllabus":"syllabus.csv"}
                missing = [c for c in cols[file_for] if c not in new_df.columns]
                if missing: st.error(f" Missing: {', '.join(missing)}")
                else:
                    st.success(" All columns found!")
                    if st.button(" Append to existing data"):
                        combined = pd.concat([pd.read_csv(paths[file_for]), new_df], ignore_index=True)
                        combined.to_csv(paths[file_for], index=False)
                        st.success(f"Saved! {paths[file_for]} now has {len(combined)} rows."); st.balloons()

    # ── TAB 2: ADD RECORDS ───────────────────────────────────
    with tab2:
        rtype = st.selectbox("What do you want to add?", ["New Question Paper","New Question","New Syllabus Entry"])

        if rtype == "New Question Paper":
            with st.form("f_paper"):
                c1,c2 = st.columns(2)
                pid=c1.text_input("Paper ID"); sub2=c2.text_input("Subject")
                sem2=c1.selectbox("Semester",["Semester 1","Semester 2","Semester 3","Semester 4"])
                yr2=c2.text_input("Academic Year"); etype=c1.selectbox("Exam Type",["End Semester","Supplementary","Mid Semester"])
                tm=c2.number_input("Total Marks",value=50,step=10)
                if st.form_submit_button(" Add Paper"):
                    if pid and sub2:
                        df=pd.read_csv("question_papers.csv")
                        pd.concat([df,pd.DataFrame([{"paper_id":pid,"subject":sub2,"semester":sem2,"academic_year":yr2,"exam_type":etype,"total_marks":tm}])],ignore_index=True).to_csv("question_papers.csv",index=False)
                        st.success(f"Paper {pid} added!")
                    else: st.error("Paper ID and Subject are required.")

        elif rtype == "New Question":
            with st.form("f_q"):
                c1,c2 = st.columns(2)
                qid=c1.text_input("Question ID"); pid2=c2.text_input("Paper ID")
                sub3=c1.text_input("Subject"); sem3=c2.selectbox("Semester",["Semester 1","Semester 2","Semester 3","Semester 4"])
                yr3=c1.text_input("Academic Year"); unit2=c2.text_input("Unit")
                topic2=c1.text_input("Topic"); qtype=c2.selectbox("Type",["Short Answer","Long Answer","Numerical / Problem","Conceptual"])
                marks2=c1.number_input("Marks",value=5,step=1); qtext=st.text_area("Question Text")
                if st.form_submit_button(" Add Question"):
                    if qid and qtext:
                        df=pd.read_csv("questions.csv")
                        pd.concat([df,pd.DataFrame([{"question_id":qid,"paper_id":pid2,"subject":sub3,"semester":sem3,"academic_year":yr3,"question_text":qtext,"unit":unit2,"topic":topic2,"question_type":qtype,"marks":marks2}])],ignore_index=True).to_csv("questions.csv",index=False)
                        st.success(f"Question {qid} added!")
                    else: st.error("Question ID and Question Text are required.")

        else:
            with st.form("f_syl"):
                c1,c2 = st.columns(2)
                sub4=c1.text_input("Subject"); unit3=c2.text_input("Unit")
                topic3=c1.text_input("Topic"); subt=c2.text_input("Subtopic")
                desc=st.text_area("Description")
                if st.form_submit_button(" Add Syllabus Entry"):
                    if sub4 and topic3:
                        df=pd.read_csv("syllabus.csv")
                        pd.concat([df,pd.DataFrame([{"subject":sub4,"unit":unit3,"topic":topic3,"subtopic":subt,"description":desc}])],ignore_index=True).to_csv("syllabus.csv",index=False)
                        st.success("Syllabus entry added!")
                    else: st.error("Subject and Topic are required.")

    # ── TAB 3: EDIT / DELETE ─────────────────────────────────
    with tab3:
        st.subheader("Edit or Delete Records")
        st.write("Click a cell to edit it. Select a row + press Delete to remove it. Click Save when done.")
        which = st.selectbox("Choose table", ["Questions","Question Papers","Syllabus"])
        fmap  = {"Questions":"questions.csv","Question Papers":"question_papers.csv","Syllabus":"syllabus.csv"}
        tfile = fmap[which]
        edited = st.data_editor(pd.read_csv(tfile), num_rows="dynamic", width="stretch", hide_index=True)
        if st.button(" Save Changes"):
            edited.to_csv(tfile, index=False)
            st.success(f" {which} saved — {len(edited)} rows. Reload the app to see changes.")
