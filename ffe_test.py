import streamlit as st
import pandas as pd
from ffe_groundrules_test import evaluate_mr_city_coverage, check_personnel_deployment, evaluate_dm_deployment, evaluate_rm_deployment, calculate_pt_group_metrics, evaluate_mr_performance, evaluate_dm_city_coverage, evaluate_rm_coverage
import datetime
import io

st.set_page_config(layout="wide")

# Load and preprocess data
def load_data(file):
    df = pd.read_excel(file)
    df_orig = df.copy()
    return df_orig

# Main Streamlit app
def main():
    st.title('Medical Representatives Evaluation App')

    required_fields = ["'MR_Pos'", "'MR_Name'", "'MR_Base City'", "'省份'", "'城市'", "' 24Q2 Final Target'", "'R6M Sales Actual'", "'医院潜力'", "'医院编码'", "'2023Q2 Actual'", "'DM_POS'", "'DM_Name'", "'RM_POS'", "'RM_Name'", "'RM_Base City'", "'RM_Base Province'", "'PT_Group'", "'2023Q1 Actual'", "'2024Q1 Actual'"]
    field_names = ", ".join(required_fields)
    st.sidebar.markdown(f"您的数据需包含 {field_names} 这些字段，字段名严格遵循上述名称。")

    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])

    if uploaded_file is not None:
        df_orig = load_data(uploaded_file)
        
        evaluation_module = st.sidebar.selectbox("Select evaluation module", ["MR City Coverage", "Personnel Deployment", "DM Deployment", "RM Deployment", "PT Group Metrics", "MR Performance", "DM City Coverage", "RM Coverage"])
        
        result_df = None
        
        if st.sidebar.button("Run Selected Module"):
            if evaluation_module == "MR City Coverage":
                result_df = evaluate_mr_city_coverage(df_orig)
            elif evaluation_module == "Personnel Deployment":
                result_df = check_personnel_deployment(df_orig)
            elif evaluation_module == "DM Deployment":
                result_df = evaluate_dm_deployment(df_orig)
            elif evaluation_module == "RM Deployment":
                result_df = evaluate_rm_deployment(df_orig)
            elif evaluation_module == "PT Group Metrics":
                result_df = calculate_pt_group_metrics(df_orig)
            elif evaluation_module == "MR Performance":
                pt_group_metrics = calculate_pt_group_metrics(df_orig)
                result_df = evaluate_mr_performance(df_orig, pt_group_metrics)
            elif evaluation_module == "DM City Coverage":
                result_df = evaluate_dm_city_coverage(df_orig)
            elif evaluation_module == "RM Coverage":
                result_df = evaluate_rm_coverage(df_orig)

            if result_df is not None:
                st.write(result_df)
                download_filename = f"{evaluation_module.replace(' ', '_')}_result.xlsx"
                result_df.to_excel(download_filename, index=False)
                st.download_button(label=f"Download {evaluation_module} Result", data=open(download_filename, 'rb'), file_name=download_filename)

        if st.sidebar.button("Show me the power!"):
            evaluation_modules = [
                ("MR City Coverage", evaluate_mr_city_coverage),
                ("Personnel Deployment", check_personnel_deployment),
                ("DM Deployment", evaluate_dm_deployment),
                ("RM Deployment", evaluate_rm_deployment),
                ("PT Group Metrics", calculate_pt_group_metrics),
                ("MR Performance", evaluate_mr_performance),
                ("DM City Coverage", evaluate_dm_city_coverage),
                ("RM Coverage", evaluate_rm_coverage)
            ]

            with st.spinner('Running all modules... Please wait!'):
                current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{uploaded_file.name.split('.')[0]}_{current_time}_diagnosis.xlsx"

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    for module_name, module_func in evaluation_modules:
                        if module_name == "MR Performance":
                            pt_group_metrics = calculate_pt_group_metrics(df_orig)
                            result = module_func(df_orig, pt_group_metrics)
                        else:
                            result = module_func(df_orig)
                        result.to_excel(writer, sheet_name=module_name, index=False)

                output.seek(0)
                st.success('All modules executed successfully!')
                st.download_button(
                    label="Download Complete Diagnosis",
                    data=output,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == '__main__':
    main()
