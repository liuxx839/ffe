import pandas as pd
import datetime
import io
import argparse
from ffe_groundrules_test import (
    evaluate_mr_city_coverage, check_personnel_deployment, evaluate_dm_deployment,
    evaluate_rm_deployment, calculate_pt_group_metrics, evaluate_mr_performance,
    evaluate_dm_city_coverage, evaluate_rm_coverage
)

def load_data(file_path):
    return pd.read_excel(file_path)

def main(input_file):
    df_orig = load_data(input_file)
    
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

    print('Running all modules... Please wait!')
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{input_file.split('.')[0]}_{current_time}_diagnosis.xlsx"

    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        for module_name, module_func in evaluation_modules:
            print(f"Running {module_name}...")
            if module_name == "MR Performance":
                pt_group_metrics = calculate_pt_group_metrics(df_orig)
                result = module_func(df_orig, pt_group_metrics)
            else:
                result = module_func(df_orig)
            result.to_excel(writer, sheet_name=module_name, index=False)

    print(f'All modules executed successfully! Results saved to {output_filename}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Medical Representatives Evaluation App')
    parser.add_argument('-f', '--file', required=True, help='Path to the input Excel file')
    args = parser.parse_args()

    main(args.file)
