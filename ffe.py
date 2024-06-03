import streamlit as st
import pandas as pd
from ffe_groundrules import evaluate_mr_city_coverage, check_personnel_deployment, evaluate_dm_deployment, evaluate_rm_deployment, calculate_pt_group_metrics, evaluate_mr_performance

# Load and preprocess data
def load_data(file):
    df = pd.read_excel(file)
    df_orig = df.copy()  # Create a copy of the original dataframe
    df_orig.rename(columns={' 24Q2 Final Target': '24Q2 Final Target'}, inplace=True)  # Rename the column
    return df_orig

# Main Streamlit app
def main():
    # Set page title
    st.title('Medical Representatives Evaluation App')

    # Display field names requirement in the top left corner
    required_fields = ["'MR_Pos'", "'MR_Name'", "'MR_Base City'", "'省份'", "'城市'", "' 24Q2 Final Target'", "'医院潜力'", "'2023Q2 Actual'", "'DM_POS'", "'DM_Name'", "'RM_POS'", "'RM_Name'", "'PT_Group'", "'2023Q1 Actual'", "'2024Q1 Actual'"]
    field_names = ", ".join(required_fields)
    st.sidebar.markdown(f"您的数据需包含 {field_names} 这些字段，字段名严格遵循上述名称。")

    # Create sidebar for user inputs
    uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])

    # Check if file is uploaded
    if uploaded_file is not None:
        # Load and preprocess the data
        df_orig = load_data(uploaded_file)

        # Initialize result_df
        result_df = None

        # Create a selection box for the user to choose the evaluation module
        evaluation_module = st.sidebar.selectbox("Select evaluation module", ["MR City Coverage", "Personnel Deployment", "DM Deployment", "RM Deployment", "PT Group Metrics", "MR Performance"])

        # Perform evaluation based on the selected module
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

        # Display the result DataFrame if result_df is not None
        if result_df is not None:
            st.write(result_df)

            # Allow user to download the result DataFrame as XLSX with the evaluation module name
            download_filename = f"{evaluation_module.replace(' ', '_')}_result.xlsx"
            result_df.to_excel(download_filename, index=False)
            st.download_button(label=f"Download {evaluation_module} Result", data=open(download_filename, 'rb'), file_name=download_filename)

if __name__ == '__main__':
    main()
