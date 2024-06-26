import pandas as pd

def evaluate_mr_city_coverage(df):
    """
    Evaluate the city coverage and base city alignment for each Medical Representative (MR) based on the following criteria:
    - Calculate the sum of 24Q2 Final Target and hospital potential for each MR in different cities
    - Count the number of cities covered by each MR and check if it's greater than 3
    - Find the city with the highest 24Q2 Final Target and the city with the highest hospital potential for each MR
    - Check if the MR_Base City matches the city with the highest 24Q2 Final Target or the city with the highest hospital potential

    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.

    Returns:
        pandas.DataFrame: A DataFrame containing the MR information, city, city coverage, top cities, and base city alignment evaluation.
    """

    # Extract the required columns for each MR
    mr_data = df[['MR_Pos', 'MR_Name', 'MR_Base City', '省份', '城市', 'R6M Sales Actual', '医院潜力']].copy()

    # Calculate the sum of 24Q2 Final Target and hospital potential for each MR in different cities
    mr_city_summary = mr_data.groupby(['MR_Pos', 'MR_Name', '省份', '城市', 'MR_Base City'])[['R6M Sales Actual', '医院潜力']].sum().reset_index()

    # Count the number of cities covered by each MR
    mr_city_count = mr_city_summary.groupby('MR_Pos')['城市'].nunique().reset_index()
    mr_city_count.columns = ['MR_Pos', 'num_cities_covered']
    mr_city_count['multi_city_coverage'] = mr_city_count['num_cities_covered'].apply(lambda x: 'Yes' if x > 3 else 'No')

    # Find the city with the highest 24Q2 Final Target and the city with the highest hospital potential for each MR
    mr_top_sales_city = mr_city_summary.loc[mr_city_summary.groupby('MR_Pos')['R6M Sales Actual'].idxmax()][['MR_Pos', '城市']]
    mr_top_sales_city.columns = ['MR_Pos', 'top_sales_city']

    mr_top_potential_city = mr_city_summary.loc[mr_city_summary.groupby('MR_Pos')['医院潜力'].idxmax()][['MR_Pos', '城市']]
    mr_top_potential_city.columns = ['MR_Pos', 'top_potential_city']

    # Merge the city coverage, top cities, and base city information
    mr_evaluation = mr_city_summary.merge(mr_city_count, on='MR_Pos', how='left')
    mr_evaluation = mr_evaluation.merge(mr_top_sales_city, on='MR_Pos', how='left')
    mr_evaluation = mr_evaluation.merge(mr_top_potential_city, on='MR_Pos', how='left')

    # Evaluate the base city alignment
    mr_evaluation['base_city_aligned'] = 'No'
    mr_evaluation.loc[mr_evaluation['MR_Base City'] == mr_evaluation['top_sales_city'], 'base_city_aligned'] = 'Yes'
    mr_evaluation.loc[mr_evaluation['MR_Base City'] == mr_evaluation['top_potential_city'], 'base_city_aligned'] = 'Yes'

    return mr_evaluation[['MR_Pos', 'MR_Name', 'MR_Base City','省份', '城市', 'R6M Sales Actual', '医院潜力', 'num_cities_covered', 'multi_city_coverage', 'top_sales_city', 'top_potential_city', 'base_city_aligned']]

def check_personnel_deployment(df):
    """
    Check if the personnel deployment adheres to the following principle:
    At the level of provinces/hospital groups/chain groups/other strategic segments defined by the BU, personnel allocation should match the business growth rate. Allocation of personnel with both productivity and growth rates below average should be avoided.
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        
    Returns:
        pandas.DataFrame: A DataFrame containing the provinces, their total productivity, growth rate, MR count, and a flag indicating violations.
    """
    
    # Calculate total productivity, growth rate, and MR count for each province
    province_stats = df.groupby('省份')[['2023Q2 Actual', '24Q2 Final Target', 'MR_Pos']].agg({'2023Q2 Actual': 'sum', '24Q2 Final Target': 'sum', 'MR_Pos': 'nunique'}).reset_index()
    province_stats['productivity'] = (province_stats['24Q2 Final Target'] / province_stats['MR_Pos']) * 4
    province_stats['growth_rate'] = (province_stats['24Q2 Final Target'] / province_stats['2023Q2 Actual']) - 1
    
    # Calculate the overall average productivity and growth rate using total '24Q2 Final Target' divided by total MR_Pos
    total_24Q2_Final_Target = province_stats['24Q2 Final Target'].sum()
    total_MR_Pos = province_stats['MR_Pos'].sum()
    
    overall_avg_productivity = (total_24Q2_Final_Target / total_MR_Pos) * 4
    overall_avg_growth_rate = (total_24Q2_Final_Target / df['2023Q2 Actual'].sum()) - 1
    
    
    # Check for violations and add a flag column
    province_stats['violation'] = 'N'
    low_productivity_mask = (province_stats['productivity'] < overall_avg_productivity) & (province_stats['growth_rate'] < overall_avg_growth_rate)
    province_stats.loc[low_productivity_mask, 'violation'] = 'Y'
    
    return province_stats

def evaluate_dm_deployment(df):
    """
    Evaluate the deployment of District Managers (DM) based on the following rules:
    1. DM's span of control (number of MRs under their management) should be between 6 and 10.
    2. If the span of control is less than 7, the productivity of the MRs under the DM should not be lower than 70% of the average productivity of all DMs.
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        
    Returns:
        pandas.DataFrame: A DataFrame containing the DM names, their span of control, span of control range check, overall DM productivity average, actual productivity, and whether they meet the standard or not.
    """
    
    # Calculate the span of control for each DM
    dm_span = df.groupby(['DM_POS', 'DM_Name'])['MR_Pos'].nunique().reset_index()
    dm_span.columns = ['DM_POS', 'DM_Name', 'span_of_control']
    
    # Check if the span of control is within the range of 6-10
    dm_span['span_range_check'] = dm_span['span_of_control'].apply(lambda x: 'Yes' if 6 <= x <= 10 else 'No')
    
    # Calculate the overall productivity for all DMs
    overall_dm_productivity = (df['24Q2 Final Target'].sum() / df['DM_POS'].nunique())
    
    # Calculate the actual productivity for each DM
    dm_productivity = df.groupby('DM_POS')['24Q2 Final Target'].sum().reset_index()
    dm_productivity['productivity'] = dm_productivity['24Q2 Final Target']
    
    # Merge the span of control and productivity
    dm_eval = dm_span.merge(dm_productivity, on='DM_POS', how='left')
    
    # Evaluate the standard
    dm_eval['violation'] = 'No'
    low_span_mask = (dm_eval['span_of_control'] < 7) & (dm_eval['productivity'] < 0.7 * overall_dm_productivity)
    dm_eval.loc[low_span_mask, 'violation'] = 'Yes'
    
    return dm_eval[['DM_POS', 'DM_Name', 'span_of_control', 'span_range_check', 'productivity', 'violation']]

def evaluate_rm_deployment(df):
    """
    Evaluate the deployment of Regional Managers (RM) based on the following rules:
    1. RM's span of control (number of DMs under their management) should be between 6 and 10.
    2. If the span of control is less than 7, the sum of productivity of all DMs under the RM should not be lower than 70% of the average productivity of all DMs under all RMs.
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        
    Returns:
        pandas.DataFrame: A DataFrame containing the RM names, their span of control, span of control range check, overall DM productivity average, actual productivity sum, and whether they meet the standard or not.
    """
    
    # Calculate the span of control for each RM
    rm_span = df.groupby(['RM_POS', 'RM_Name'])['DM_POS'].nunique().reset_index()
    rm_span.columns = ['RM_POS', 'RM_Name', 'span_of_control']
    
    # Check if the span of control is within the range of 6-10
    rm_span['span_range_check'] = rm_span['span_of_control'].apply(lambda x: 'Yes' if 6 <= x <= 8 else 'No')
    
    # Calculate the overall productivity for all DMs under all RMs
    overall_dm_productivity = (df['24Q2 Final Target'].sum() / df['RM_POS'].nunique()) 
    
    # Calculate the actual productivity sum for each RM
    rm_productivity = df.groupby('RM_POS')['24Q2 Final Target'].sum().reset_index()
    rm_productivity['productivity'] = rm_productivity['24Q2 Final Target']
    
    # Merge the span of control and productivity
    rm_eval = rm_span.merge(rm_productivity, on='RM_POS', how='left')
    
    # Evaluate the standard
    rm_eval['violation'] = 'No'
    low_span_mask = (rm_eval['span_of_control'] < 6) & (rm_eval['productivity'] < 0.7 * overall_dm_productivity)
    rm_eval.loc[low_span_mask, 'violation'] = 'Yes'
    
    return rm_eval[['RM_POS', 'RM_Name', 'span_of_control', 'span_range_check', 'productivity', 'violation']]

def calculate_pt_group_metrics(df):
    """
    Calculate various metrics for each PT group, including:
    - Number of people in each PT group
    - Total sales for 2023Q1, 2023Q2, 2024Q1, and 24Q2 Final Target
    - Average productivity for 24Q2 and 24Q1
    - Growth rate for 24Q2 and 24Q1
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        
    Returns:
        pandas.DataFrame: A DataFrame containing the PT group, number of people, total sales, average productivity, and growth rate for different quarters.
    """
    
    # Calculate the number of people in each PT group
    pt_group_count = df.groupby('PT_Group')['MR_Pos'].nunique().reset_index()
    pt_group_count.columns = ['PT_Group', 'num_people']
    
    # Calculate the total sales for different quarters
    pt_group_sales = df.groupby('PT_Group')[['2023Q1 Actual', '2023Q2 Actual', '2024Q1 Actual', '24Q2 Final Target']].sum().reset_index()
    
    # Merge the number of people with the sales data
    pt_group_metrics = pt_group_sales.merge(pt_group_count, on='PT_Group', how='left')
    
    # Calculate the average productivity for 24Q2 and 24Q1
    pt_group_metrics['24Q2_avg_productivity'] = pt_group_metrics['24Q2 Final Target'] / pt_group_metrics['num_people']
    pt_group_metrics['24Q1_avg_productivity'] = pt_group_metrics['2024Q1 Actual'] / pt_group_metrics['num_people']
    
    # Calculate the growth rate for 24Q2 and 24Q1
    pt_group_metrics['24Q2_growth_rate'] = (pt_group_metrics['24Q2 Final Target'] / pt_group_metrics['2023Q2 Actual']) - 1
    pt_group_metrics['24Q1_growth_rate'] = (pt_group_metrics['2024Q1 Actual'] / pt_group_metrics['2023Q1 Actual']) - 1
    
    return pt_group_metrics

def evaluate_mr_performance(df, pt_group_metrics):
    """
    Evaluate the performance of each Medical Representative (MR) based on the following criteria:
    - Sum up the 2023Q1 Actual, 2023Q2 Actual, 2024Q1 Actual, and 24Q2 Final Target for each MR_Pos
    - Calculate the Q2 Productivity Index and Q2 Growth for each MR_Pos
    - Check if Q2 Productivity Index is lower than 0.5
    - Check if Q2 Growth is lower than the corresponding PT group's 24Q2_growth_rate and if Q2 Productivity Index is between 0.5 and 0.7
    - Calculate similar metrics for Q1

    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        pt_group_metrics (pandas.DataFrame): The DataFrame containing the metrics for each PT group, calculated by the `calculate_pt_group_metrics` function.

    Returns:
        pandas.DataFrame: A DataFrame containing the MR name, MR position, PT group, summed actual sales, productivity index, growth, and evaluation results for Q2 and Q1.
    """

    # Sum up the actual sales for each MR_Pos
    mr_data = df.groupby(['MR_Pos', 'MR_Name'])[['2023Q1 Actual', '2023Q2 Actual', '2024Q1 Actual', '24Q2 Final Target']].sum().reset_index()

    # Merge the PT_Group column
    mr_data = mr_data.merge(df[['MR_Pos', 'PT_Group']].drop_duplicates(), on='MR_Pos', how='left')

    # Calculate Q2 Productivity Index and Q2 Growth for each MR_Pos
    mr_data = mr_data.merge(pt_group_metrics[['PT_Group', '24Q2_avg_productivity', '24Q2_growth_rate']], on='PT_Group', how='left')
    mr_data['Q2_Productivity_Index'] = mr_data['24Q2 Final Target'] / mr_data['24Q2_avg_productivity']
    mr_data['Q2_Growth'] = (mr_data['24Q2 Final Target'] / mr_data['2023Q2 Actual']) - 1

    # Evaluate Q2 performance
    mr_data['Q2_Productivity_Index_Low'] = (mr_data['Q2_Productivity_Index'] < 0.5).apply(lambda x: 'Yes' if x else 'No')
    mr_data['Q2_Growth_Low_and_Productivity_Index_Medium'] = ((mr_data['Q2_Growth'] < mr_data['24Q2_growth_rate']) & (mr_data['Q2_Productivity_Index'].between(0.5, 0.7))).apply(lambda x: 'Yes' if x else 'No')

    # Calculate Q1 Productivity Index and Q1 Growth for each MR_Pos
    mr_data = mr_data.merge(pt_group_metrics[['PT_Group', '24Q1_avg_productivity', '24Q1_growth_rate']], on='PT_Group', how='left')
    mr_data['Q1_Productivity_Index'] = mr_data['2024Q1 Actual'] / mr_data['24Q1_avg_productivity']
    mr_data['Q1_Growth'] = (mr_data['2024Q1 Actual'] / mr_data['2023Q1 Actual']) - 1

    # Evaluate Q1 performance
    mr_data['Q1_Productivity_Index_Low'] = (mr_data['Q1_Productivity_Index'] < 0.5).apply(lambda x: 'Yes' if x else 'No')
    mr_data['Q1_Growth_Low_and_Productivity_Index_Medium'] = ((mr_data['Q1_Growth'] < mr_data['24Q1_growth_rate']) & (mr_data['Q1_Productivity_Index'].between(0.5, 0.7))).apply(lambda x: 'Yes' if x else 'No')

    return mr_data

def evaluate_dm_city_coverage(df):
    """
    Evaluate the city coverage and base city alignment for each District Manager (DM).
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
    
    Returns:
        pandas.DataFrame: A DataFrame containing the DM information, city coverage, top cities, 
        base city alignment evaluation, and cross-province coverage.
    """
    # Extract the required columns for each DM
    dm_data = df[['DM_POS', 'DM_Name', 'DM_Base City', 'DM_Base Province', '省份', '城市', 'R6M Sales Actual', '医院潜力', '医院编码']].copy()
    
    # Calculate the sum of R6M Sales Actual for each DM in different cities (without deduplication)
    sales_summary = dm_data.groupby(['DM_POS', 'DM_Name', 'DM_Base Province', '省份', '城市', 'DM_Base City'])['R6M Sales Actual'].sum().reset_index()
    
    # Calculate the sum of unique hospital potential for each DM in different cities
    potential_summary = dm_data.drop_duplicates(subset=['DM_POS', '城市', '医院编码']).groupby(['DM_POS', 'DM_Name', 'DM_Base Province', '省份', '城市', 'DM_Base City'])['医院潜力'].sum().reset_index()
    
    # Merge sales and potential summaries
    dm_city_summary = sales_summary.merge(potential_summary, on=['DM_POS', 'DM_Name', 'DM_Base Province', '省份', '城市', 'DM_Base City'], how='outer')
    
    # Count the number of cities covered by each DM
    dm_city_count = dm_city_summary.groupby('DM_POS')['城市'].nunique().reset_index()
    dm_city_count.columns = ['DM_POS', 'num_cities_covered']
    
    # Find the city with the highest R6M Sales Actual and the city with the highest hospital potential for each DM
    dm_top_sales_city = dm_city_summary.loc[dm_city_summary.groupby('DM_POS')['R6M Sales Actual'].idxmax()][['DM_POS', '城市']]
    dm_top_sales_city.columns = ['DM_POS', 'top_sales_city']
    
    dm_top_potential_city = dm_city_summary.loc[dm_city_summary.groupby('DM_POS')['医院潜力'].idxmax()][['DM_POS', '城市']]
    dm_top_potential_city.columns = ['DM_POS', 'top_potential_city']
    
    # Merge the city coverage, top cities, and base city information
    dm_evaluation = dm_city_summary.merge(dm_city_count, on='DM_POS', how='left')
    dm_evaluation = dm_evaluation.merge(dm_top_sales_city, on='DM_POS', how='left')
    dm_evaluation = dm_evaluation.merge(dm_top_potential_city, on='DM_POS', how='left')
    
    # Evaluate the base city alignment
    dm_evaluation['base_city_aligned'] = 'No'
    dm_evaluation.loc[dm_evaluation['DM_Base City'] == dm_evaluation['top_sales_city'], 'base_city_aligned'] = 'Yes'
    dm_evaluation.loc[dm_evaluation['DM_Base City'] == dm_evaluation['top_potential_city'], 'base_city_aligned'] = 'Yes'
    
    # Check if the DM covers cities outside their base province
    dm_evaluation['cross_province'] = dm_evaluation.apply(lambda row: 'Yes' if row['DM_Base Province'] != row['省份'] else 'No', axis=1)
    
    # Calculate cross_province_all
    cross_province_all = dm_evaluation.groupby('DM_POS')['cross_province'].apply(lambda x: 'Yes' if 'Yes' in x.values else 'No').reset_index()
    cross_province_all.columns = ['DM_POS', 'cross_province_all']
    
    # Merge cross_province_all into dm_evaluation
    dm_evaluation = dm_evaluation.merge(cross_province_all, on='DM_POS', how='left')
    
    return dm_evaluation[['DM_POS', 'DM_Name', 'DM_Base City', 'DM_Base Province', '省份', '城市', 'R6M Sales Actual', '医院潜力', 
                          'num_cities_covered', 'top_sales_city', 'top_potential_city', 'base_city_aligned', 'cross_province', 'cross_province_all']]



def evaluate_rm_coverage(df):
    """
    Evaluate the coverage and alignment for each Regional Manager (RM) at the province level.
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
    
    Returns:
        pandas.DataFrame: A DataFrame containing the RM information, coverage, top provinces, 
        base province and city alignment evaluation, and province sharing.
    """
    # Extract the required columns for each RM
    rm_data = df[['RM_POS', 'RM_Name', 'RM_Base City', 'RM_Base Province', '省份', 'R6M Sales Actual', '医院潜力', '医院编码']].copy()
    
    # Calculate the sum of R6M Sales Actual for each RM in different provinces (without deduplication)
    sales_summary = rm_data.groupby(['RM_POS', 'RM_Name', 'RM_Base City', 'RM_Base Province', '省份'])['R6M Sales Actual'].sum().reset_index()
    
    # Calculate the sum of unique hospital potential for each RM in different provinces
    potential_summary = rm_data.drop_duplicates(subset=['RM_POS', '省份', '医院编码']).groupby(['RM_POS', 'RM_Name', 'RM_Base City', 'RM_Base Province', '省份'])['医院潜力'].sum().reset_index()
    
    # Merge sales and potential summaries
    rm_province_summary = sales_summary.merge(potential_summary, on=['RM_POS', 'RM_Name', 'RM_Base City', 'RM_Base Province', '省份'], how='outer')
    
    # Count the number of provinces covered by each RM
    rm_province_count = rm_province_summary.groupby('RM_POS')['省份'].nunique().reset_index()
    rm_province_count.columns = ['RM_POS', 'num_provinces_covered']
    
    # Find the province with the highest R6M Sales Actual and the province with the highest hospital potential for each RM
    rm_top_sales_province = rm_province_summary.loc[rm_province_summary.groupby('RM_POS')['R6M Sales Actual'].idxmax()][['RM_POS', '省份']]
    rm_top_sales_province.columns = ['RM_POS', 'top_sales_province']
    
    rm_top_potential_province = rm_province_summary.loc[rm_province_summary.groupby('RM_POS')['医院潜力'].idxmax()][['RM_POS', '省份']]
    rm_top_potential_province.columns = ['RM_POS', 'top_potential_province']
    
    # Merge the province coverage, top provinces, and base province information
    rm_evaluation = rm_province_summary.merge(rm_province_count, on='RM_POS', how='left')
    rm_evaluation = rm_evaluation.merge(rm_top_sales_province, on='RM_POS', how='left')
    rm_evaluation = rm_evaluation.merge(rm_top_potential_province, on='RM_POS', how='left')
    
    # Evaluate the base province alignment
    rm_evaluation['base_province_aligned'] = 'No'
    rm_evaluation.loc[rm_evaluation['RM_Base Province'] == rm_evaluation['top_sales_province'], 'base_province_aligned'] = 'Yes'
    rm_evaluation.loc[rm_evaluation['RM_Base Province'] == rm_evaluation['top_potential_province'], 'base_province_aligned'] = 'Yes'
    
    # Check if the RM covers provinces outside their base province
    rm_evaluation['cross_province'] = rm_evaluation.apply(lambda row: 'Yes' if row['RM_Base Province'] != row['省份'] else 'No', axis=1)
    
    # Calculate cross_province_all
    cross_province_all = rm_evaluation.groupby('RM_POS')['cross_province'].apply(lambda x: 'Yes' if 'Yes' in x.values else 'No').reset_index()
    cross_province_all.columns = ['RM_POS', 'cross_province_all']
    
    # Merge cross_province_all into rm_evaluation
    rm_evaluation = rm_evaluation.merge(cross_province_all, on='RM_POS', how='left')
    
    # Check if a province has more than 2 different RM_POS
    province_rm_count = rm_evaluation.groupby('省份')['RM_POS'].nunique().reset_index()
    province_rm_count['multiple_rms'] = province_rm_count['RM_POS'].apply(lambda x: 'Yes' if x >= 2 else 'No')
    
    # Merge the multiple_rms information into rm_evaluation
    rm_evaluation = rm_evaluation.merge(province_rm_count[['省份', 'multiple_rms']], on='省份', how='left')
    
    return rm_evaluation[['RM_POS', 'RM_Name', 'RM_Base City', 'RM_Base Province', '省份', 'R6M Sales Actual', '医院潜力', 
                          'num_provinces_covered', 'top_sales_province', 'top_potential_province', 'base_province_aligned', 'cross_province', 'cross_province_all', 'multiple_rms']]
