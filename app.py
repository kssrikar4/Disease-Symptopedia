import streamlit as st
from pathlib import Path
from utils import init_streamlit_app

st.set_page_config(
    page_title="Disease-Symptopedia",
    layout="wide"
)

st.title("Disease-Symptopedia")
st.markdown("An interactive disease-symptom knowledge explorer with Columbia University's Disease-Symptom Knowledge Database.")

data_dir = Path("disease_symptom_data")
if not data_dir.exists():
    st.error("❌ No data found! Please run `python pipeline.py` first to generate CSV files.")
    st.stop()

csv_files = sorted(data_dir.glob("disease_symptom_mappings_*.csv"))
if not csv_files:
    st.error("❌ No mappings file found! Please run the pipeline first.")
    st.stop()

latest_file = csv_files[-1]

mappings_file = latest_file
diseases_file = data_dir / latest_file.name.replace("disease_symptom_mappings_", "diseases_")
symptoms_file = data_dir / latest_file.name.replace("disease_symptom_mappings_", "symptoms_")

if not diseases_file.exists() or not symptoms_file.exists():
    st.error(f"❌ Missing required files. Expected:\n- {diseases_file}\n- {symptoms_file}")
    st.stop()


@st.cache_resource
def load_data():
    return init_streamlit_app(
        str(mappings_file),
        str(diseases_file),
        str(symptoms_file)
    )


data = load_data()

timestamp = latest_file.stem.split("_", 3)[-1]
st.info(f"📊 Data loaded from: {timestamp.replace('_', ' ')}")

tab1, tab2, tab3 = st.tabs(["🔍 Symptom → Diseases", "🔍 Disease → Symptoms", "📊 Statistics"])

with tab1:
    st.subheader("Find Diseases Associated with a Symptom")
    symptom_options = sorted(data['symptoms'])
    selected_symptom = st.selectbox("Select a symptom:", symptom_options, key='symptom_selector')

    if selected_symptom:
        if selected_symptom in data['s2d']:
            diseases = data['s2d'][selected_symptom]
            col1, col2 = st.columns([2, 1])

            with col1:
                st.success(f"✓ Found **{len(diseases)}** diseases associated with **{selected_symptom}**")

            display_diseases = []
            for idx, disease in enumerate(diseases, 1):
                display_diseases.append({
                    'Rank': idx,
                    'Disease': disease,
                    'Symptom Count': len(data['d2s'].get(disease, []))
                })
            st.dataframe(display_diseases, use_container_width=True)

            if st.checkbox("Show symptom details", key='symptom_details'):
                st.write(f"**Symptom:** {selected_symptom}")
                st.write(f"**Associated diseases:** {', '.join(diseases[:10])}{'...' if len(diseases) > 10 else ''}")
        else:
            st.warning(f"⚠️ No diseases found for symptom: {selected_symptom}")

with tab2:
    st.subheader("Find Symptoms Associated with a Disease")
    disease_options = sorted(data['d2s'].keys())
    selected_disease = st.selectbox("Select a disease:", disease_options, key='disease_selector')

    if selected_disease:
        if selected_disease in data['d2s']:
            symptoms = data['d2s'][selected_disease]
            col1, col2 = st.columns([2, 1])

            with col1:
                st.success(f"✓ Found **{len(symptoms)}** symptoms for **{selected_disease}**")

            display_symptoms = []
            for idx, symptom in enumerate(symptoms, 1):
                display_symptoms.append({
                    'Rank': idx,
                    'Symptom': symptom,
                    'Associated Diseases': len(data['s2d'].get(symptom, []))
                })
            st.dataframe(display_symptoms, use_container_width=True)

            st.markdown("**Top 5 Most Associated Symptoms:**")
            for i, symptom in enumerate(symptoms[:5], 1):
                st.write(f"{i}. {symptom}")
        else:
            st.warning(f"⚠️ No symptoms found for disease: {selected_disease}")

with tab3:
    st.subheader("Database Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Diseases", len(data['d2s']))

    with col2:
        st.metric("Total Symptoms", len(data['symptoms']))

    with col3:
        total_mappings = sum(len(symptoms) for symptoms in data['d2s'].values())
        st.metric("Total Associations", total_mappings)

    st.markdown("### Symptom Distribution")

    symptom_counts = {}
    for symptom in data['symptoms']:
        count = len(data['s2d'].get(symptom, []))
        symptom_counts[symptom] = count

    top_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    st.write("**Top 10 Most Common Symptoms** (by disease count):")
    for symptom, count in top_symptoms:
        st.write(f"- **{symptom}**: {count} diseases")

    st.markdown("### Disease Distribution")

    disease_counts = {}
    for disease in data['d2s']:
        count = len(data['d2s'][disease])
        disease_counts[disease] = count

    top_diseases = sorted(disease_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    st.write("**Top 10 Diseases with Most Symptoms:**")
    for disease, count in top_diseases:
        st.write(f"- **{disease}**: {count} symptoms")

st.sidebar.title("About")
st.sidebar.info("""
**Disease-Symptom Knowledge Database**

- **Source**: Columbia University DBMI
- **Data**: New York Presbyterian Hospital (2004)
- **Method**: MedLEE NLP + Statistical Analysis
- **Reference**: Wang X, et al. "Automated Knowledge Acquisition from Clinical Narrative Reports." AMIA Annu Symp Proc. 2008:783-787.
""")

st.sidebar.markdown("---")
st.sidebar.title("How to Use")
st.sidebar.markdown("""
1. **Symptom → Diseases**: Enter a symptom to find associated diseases
2. **Disease → Symptoms**: Enter a disease to find associated symptoms
3. **Statistics**: View database overview and distribution
""")

st.sidebar.markdown("---")

st.markdown("---")
st.caption("⚠️ Medical knowledge database. Use for informational purposes only. Consult medical professionals for diagnosis and treatment.")