import pandas as pd

def evaluate_mr_city_coverage(df):
    """
    Evaluate the city coverage and base city alignment for each Medical Representative (MR) based on the following criteria:
    - Calculate the sum of tyq2_target and hospital potential for each MR in different cities
    - Count the number of cities covered by each MR and check if it's greater than 3
    - Find the city with the highest tyq2_target and the city with the highest hospital potential for each MR
    - Check if the mr_base_city_name matches the city with the highest tyq2_target or the city with the highest hospital potential

    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.

    Returns:
        pandas.DataFrame: A DataFrame containing the MR information, city, city coverage, top cities, and base city alignment evaluation.
    """

    # Extract the required columns for each MR
    mr_data = df[['mr_pos', 'mr_name', 'mr_base_city_name', 'hco_province_name', 'hco_city_name', 'r6m_actual_sales', 'hco_potential_value']].copy()

    # Calculate the sum of tyq2_target and hospital potential for each MR in different cities
    mr_city_summary = mr_data.groupby(['mr_pos', 'mr_name', 'hco_province_name', 'hco_city_name', 'mr_base_city_name'])[['r6m_actual_sales', 'hco_potential_value']].sum().reset_index()

    # Count the number of cities covered by each MR
    mr_city_count = mr_city_summary.groupby('mr_pos')['hco_city_name'].nunique().reset_index()
    mr_city_count.columns = ['mr_pos', 'num_cities_covered']
    mr_city_count['multi_city_coverage'] = mr_city_count['num_cities_covered'].apply(lambda x: 'Yes' if x > 3 else 'No')

    # Find the city with the highest tyq2_target and the city with the highest hospital potential for each MR
    mr_top_sales_city = mr_city_summary.loc[mr_city_summary.groupby('mr_pos')['r6m_actual_sales'].idxmax()][['mr_pos', 'hco_city_name']]
    mr_top_sales_city.columns = ['mr_pos', 'top_sales_city']

    mr_top_potential_city = mr_city_summary.loc[mr_city_summary.groupby('mr_pos')['hco_potential_value'].idxmax()][['mr_pos', 'hco_city_name']]
    mr_top_potential_city.columns = ['mr_pos', 'top_potential_city']

    # Merge the city coverage, top cities, and base city information
    mr_evaluation = mr_city_summary.merge(mr_city_count, on='mr_pos', how='left')
    mr_evaluation = mr_evaluation.merge(mr_top_sales_city, on='mr_pos', how='left')
    mr_evaluation = mr_evaluation.merge(mr_top_potential_city, on='mr_pos', how='left')

    # Evaluate the base city alignment
    mr_evaluation['base_city_aligned'] = 'No'
    mr_evaluation.loc[mr_evaluation['mr_base_city_name'] == mr_evaluation['top_sales_city'], 'base_city_aligned'] = 'Yes'
    mr_evaluation.loc[mr_evaluation['mr_base_city_name'] == mr_evaluation['top_potential_city'], 'base_city_aligned'] = 'Yes'

    return mr_evaluation[['mr_pos', 'mr_name', 'mr_base_city_name','hco_province_name', 'hco_city_name', 'r6m_actual_sales', 'hco_potential_value', 'num_cities_covered', 'multi_city_coverage', 'top_sales_city', 'top_potential_city', 'base_city_aligned']]

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
    province_stats = df.groupby('hco_province_name')[['lyq2_actual_sales', 'tyq2_target', 'mr_pos']].agg({'lyq2_actual_sales': 'sum', 'tyq2_target': 'sum', 'mr_pos': 'nunique'}).reset_index()
    province_stats['productivity'] = (province_stats['tyq2_target'] / province_stats['mr_pos']) * 4
    province_stats['growth_rate'] = (province_stats['tyq2_target'] / province_stats['lyq2_actual_sales']) - 1
    
    # Calculate the overall average productivity and growth rate using total 'tyq2_target' divided by total mr_pos
    total_24Q2_Final_Target = province_stats['tyq2_target'].sum()
    total_mr_pos = province_stats['mr_pos'].sum()
    
    overall_avg_productivity = (total_24Q2_Final_Target / total_mr_pos) * 4
    overall_avg_growth_rate = (total_24Q2_Final_Target / df['lyq2_actual_sales'].sum()) - 1
    
    
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
    dm_span = df.groupby(['dm_pos', 'dm_name'])['mr_pos'].nunique().reset_index()
    dm_span.columns = ['dm_pos', 'dm_name', 'span_of_control']
    
    # Check if the span of control is within the range of 6-10
    dm_span['span_range_check'] = dm_span['span_of_control'].apply(lambda x: 'Yes' if 6 <= x <= 10 else 'No')
    
    # Calculate the overall productivity for all DMs
    overall_dm_productivity = (df['tyq2_target'].sum() / df['dm_pos'].nunique())
    
    # Calculate the actual productivity for each DM
    dm_productivity = df.groupby('dm_pos')['tyq2_target'].sum().reset_index()
    dm_productivity['productivity'] = dm_productivity['tyq2_target']
    
    # Merge the span of control and productivity
    dm_eval = dm_span.merge(dm_productivity, on='dm_pos', how='left')
    
    # Evaluate the standard
    dm_eval['violation'] = 'No'
    low_span_mask = (dm_eval['span_of_control'] < 7) & (dm_eval['productivity'] < 0.7 * overall_dm_productivity)
    dm_eval.loc[low_span_mask, 'violation'] = 'Yes'
    
    return dm_eval[['dm_pos', 'dm_name', 'span_of_control', 'span_range_check', 'productivity', 'violation']]

def evaluate_rm_deployment(df):
    """
    Evaluate the deployment of regional Managers (RM) based on the following rules:
    1. RM's span of control (number of DMs under their management) should be between 6 and 10.
    2. If the span of control is less than 7, the sum of productivity of all DMs under the RM should not be lower than 70% of the average productivity of all DMs under all RMs.
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        
    Returns:
        pandas.DataFrame: A DataFrame containing the RM names, their span of control, span of control range check, overall DM productivity average, actual productivity sum, and whether they meet the standard or not.
    """
    
    # Calculate the span of control for each RM
    rm_span = df.groupby(['rm_position_cd', 'rm_name'])['dm_pos'].nunique().reset_index()
    rm_span.columns = ['rm_position_cd', 'rm_name', 'span_of_control']
    
    # Check if the span of control is within the range of 6-10
    rm_span['span_range_check'] = rm_span['span_of_control'].apply(lambda x: 'Yes' if 6 <= x <= 8 else 'No')
    
    # Calculate the overall productivity for all DMs under all RMs
    overall_dm_productivity = (df['tyq2_target'].sum() / df['rm_position_cd'].nunique()) 
    
    # Calculate the actual productivity sum for each RM
    rm_productivity = df.groupby('rm_position_cd')['tyq2_target'].sum().reset_index()
    rm_productivity['productivity'] = rm_productivity['tyq2_target']
    
    # Merge the span of control and productivity
    rm_eval = rm_span.merge(rm_productivity, on='rm_position_cd', how='left')
    
    # Evaluate the standard
    rm_eval['violation'] = 'No'
    low_span_mask = (rm_eval['span_of_control'] < 6) & (rm_eval['productivity'] < 0.7 * overall_dm_productivity)
    rm_eval.loc[low_span_mask, 'violation'] = 'Yes'
    
    return rm_eval[['rm_position_cd', 'rm_name', 'span_of_control', 'span_range_check', 'productivity', 'violation']]

def calculate_pt_group_metrics(df):
    """
    Calculate various metrics for each PT group, including:
    - Number of people in each PT group
    - Total sales for 2023Q1, 2023Q2, 2024Q1, and tyq2_target
    - Average productivity for 24Q2 and 24Q1
    - Growth rate for 24Q2 and 24Q1
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        
    Returns:
        pandas.DataFrame: A DataFrame containing the PT group, number of people, total sales, average productivity, and growth rate for different quarters.
    """
    
    # Calculate the number of people in each PT group
    pt_group_count = df.groupby('pt_group')['mr_pos'].nunique().reset_index()
    pt_group_count.columns = ['pt_group', 'num_people']
    
    # Calculate the total sales for different quarters
    pt_group_sales = df.groupby('pt_group')[['lyq1_actual_sales', 'lyq2_actual_sales', 'tyq1_actual_sales', 'tyq2_target']].sum().reset_index()
    
    # Merge the number of people with the sales data
    pt_group_metrics = pt_group_sales.merge(pt_group_count, on='pt_group', how='left')
    
    # Calculate the average productivity for 24Q2 and 24Q1
    pt_group_metrics['24Q2_avg_productivity'] = pt_group_metrics['tyq2_target'] / pt_group_metrics['num_people']
    pt_group_metrics['24Q1_avg_productivity'] = pt_group_metrics['tyq1_actual_sales'] / pt_group_metrics['num_people']
    
    # Calculate the growth rate for 24Q2 and 24Q1
    pt_group_metrics['24Q2_growth_rate'] = (pt_group_metrics['tyq2_target'] / pt_group_metrics['lyq2_actual_sales']) - 1
    pt_group_metrics['24Q1_growth_rate'] = (pt_group_metrics['tyq1_actual_sales'] / pt_group_metrics['lyq1_actual_sales']) - 1
    
    return pt_group_metrics

def evaluate_mr_performance(df, pt_group_metrics):
    """
    Evaluate the performance of each Medical Representative (MR) based on the following criteria:
    - Sum up the lyq1_actual_sales, lyq2_actual_sales, tyq1_actual_sales, and tyq2_target for each mr_pos
    - Calculate the Q2 Productivity Index and Q2 Growth for each mr_pos
    - Check if Q2 Productivity Index is lower than 0.5
    - Check if Q2 Growth is lower than the corresponding PT group's 24Q2_growth_rate and if Q2 Productivity Index is between 0.5 and 0.7
    - Calculate similar metrics for Q1

    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
        pt_group_metrics (pandas.DataFrame): The DataFrame containing the metrics for each PT group, calculated by the `calculate_pt_group_metrics` function.

    Returns:
        pandas.DataFrame: A DataFrame containing the MR name, MR position, PT group, summed actual sales, productivity index, growth, and evaluation results for Q2 and Q1.
    """

    # Sum up the actual sales for each mr_pos
    mr_data = df.groupby(['mr_pos', 'mr_name'])[['lyq1_actual_sales', 'lyq2_actual_sales', 'tyq1_actual_sales', 'tyq2_target']].sum().reset_index()

    # Merge the pt_group column
    mr_data = mr_data.merge(df[['mr_pos', 'pt_group']].drop_duplicates(), on='mr_pos', how='left')

    # Calculate Q2 Productivity Index and Q2 Growth for each mr_pos
    mr_data = mr_data.merge(pt_group_metrics[['pt_group', '24Q2_avg_productivity', '24Q2_growth_rate']], on='pt_group', how='left')
    mr_data['Q2_Productivity_Index'] = mr_data['tyq2_target'] / mr_data['24Q2_avg_productivity']
    mr_data['Q2_Growth'] = (mr_data['tyq2_target'] / mr_data['lyq2_actual_sales']) - 1

    # Evaluate Q2 performance
    mr_data['Q2_Productivity_Index_Low'] = (mr_data['Q2_Productivity_Index'] < 0.5).apply(lambda x: 'Yes' if x else 'No')
    mr_data['Q2_Growth_Low_and_Productivity_Index_Medium'] = ((mr_data['Q2_Growth'] < mr_data['24Q2_growth_rate']) & (mr_data['Q2_Productivity_Index'].between(0.5, 0.7))).apply(lambda x: 'Yes' if x else 'No')

    # Calculate Q1 Productivity Index and Q1 Growth for each mr_pos
    mr_data = mr_data.merge(pt_group_metrics[['pt_group', '24Q1_avg_productivity', '24Q1_growth_rate']], on='pt_group', how='left')
    mr_data['Q1_Productivity_Index'] = mr_data['tyq1_actual_sales'] / mr_data['24Q1_avg_productivity']
    mr_data['Q1_Growth'] = (mr_data['tyq1_actual_sales'] / mr_data['lyq1_actual_sales']) - 1

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
    dm_data = df[['dm_pos', 'dm_name', 'dm_base_city_name', 'dm_base_province_name', 'hco_province_name', 'hco_city_name', 'r6m_actual_sales', 'hco_potential_value', 'hco_cd']].copy()
    
    # Calculate the sum of r6m_actual_sales for each DM in different cities (without deduplication)
    sales_summary = dm_data.groupby(['dm_pos', 'dm_name', 'dm_base_province_name', 'hco_province_name', 'hco_city_name', 'dm_base_city_name'])['r6m_actual_sales'].sum().reset_index()
    
    # Calculate the sum of unique hospital potential for each DM in different cities
    potential_summary = dm_data.drop_duplicates(subset=['dm_pos', 'hco_city_name', 'hco_cd']).groupby(['dm_pos', 'dm_name', 'dm_base_province_name', 'hco_province_name', 'hco_city_name', 'dm_base_city_name'])['hco_potential_value'].sum().reset_index()
    
    # Merge sales and potential summaries
    dm_city_summary = sales_summary.merge(potential_summary, on=['dm_pos', 'dm_name', 'dm_base_province_name', 'hco_province_name', 'hco_city_name', 'dm_base_city_name'], how='outer')
    
    # Count the number of cities covered by each DM
    dm_city_count = dm_city_summary.groupby('dm_pos')['hco_city_name'].nunique().reset_index()
    dm_city_count.columns = ['dm_pos', 'num_cities_covered']
    
    # Find the city with the highest r6m_actual_sales and the city with the highest hospital potential for each DM
    dm_top_sales_city = dm_city_summary.loc[dm_city_summary.groupby('dm_pos')['r6m_actual_sales'].idxmax()][['dm_pos', 'hco_city_name']]
    dm_top_sales_city.columns = ['dm_pos', 'top_sales_city']
    
    dm_top_potential_city = dm_city_summary.loc[dm_city_summary.groupby('dm_pos')['hco_potential_value'].idxmax()][['dm_pos', 'hco_city_name']]
    dm_top_potential_city.columns = ['dm_pos', 'top_potential_city']
    
    # Merge the city coverage, top cities, and base city information
    dm_evaluation = dm_city_summary.merge(dm_city_count, on='dm_pos', how='left')
    dm_evaluation = dm_evaluation.merge(dm_top_sales_city, on='dm_pos', how='left')
    dm_evaluation = dm_evaluation.merge(dm_top_potential_city, on='dm_pos', how='left')
    
    # Evaluate the base city alignment
    dm_evaluation['base_city_aligned'] = 'No'
    dm_evaluation.loc[dm_evaluation['dm_base_city_name'] == dm_evaluation['top_sales_city'], 'base_city_aligned'] = 'Yes'
    dm_evaluation.loc[dm_evaluation['dm_base_city_name'] == dm_evaluation['top_potential_city'], 'base_city_aligned'] = 'Yes'
    
    # Check if the DM covers cities outside their base province
    dm_evaluation['cross_province'] = dm_evaluation.apply(lambda row: 'Yes' if row['dm_base_province_name'] != row['hco_province_name'] else 'No', axis=1)
    
    # Calculate cross_province_all
    cross_province_all = dm_evaluation.groupby('dm_pos')['cross_province'].apply(lambda x: 'Yes' if 'Yes' in x.values else 'No').reset_index()
    cross_province_all.columns = ['dm_pos', 'cross_province_all']
    
    # Merge cross_province_all into dm_evaluation
    dm_evaluation = dm_evaluation.merge(cross_province_all, on='dm_pos', how='left')
    
    return dm_evaluation[['dm_pos', 'dm_name', 'dm_base_city_name', 'dm_base_province_name', 'hco_province_name', 'hco_city_name', 'r6m_actual_sales', 'hco_potential_value', 
                          'num_cities_covered', 'top_sales_city', 'top_potential_city', 'base_city_aligned', 'cross_province', 'cross_province_all']]



def evaluate_rm_coverage(df):
    """
    Evaluate the coverage and alignment for each regional Manager (RM) at the province level.
    
    Args:
        df (pandas.DataFrame): The input DataFrame containing the required columns.
    
    Returns:
        pandas.DataFrame: A DataFrame containing the RM information, coverage, top provinces, 
        base province and city alignment evaluation, and province sharing.
    """
    # Extract the required columns for each RM
    rm_data = df[['rm_position_cd', 'rm_name', 'rm_base_city_name', 'rm_base_province_name', 'hco_province_name', 'r6m_actual_sales', 'hco_potential_value', 'hco_cd']].copy()
    
    # Calculate the sum of r6m_actual_sales for each RM in different provinces (without deduplication)
    sales_summary = rm_data.groupby(['rm_position_cd', 'rm_name', 'rm_base_city_name', 'rm_base_province_name', 'hco_province_name'])['r6m_actual_sales'].sum().reset_index()
    
    # Calculate the sum of unique hospital potential for each RM in different provinces
    potential_summary = rm_data.drop_duplicates(subset=['rm_position_cd', 'hco_province_name', 'hco_cd']).groupby(['rm_position_cd', 'rm_name', 'rm_base_city_name', 'rm_base_province_name', 'hco_province_name'])['hco_potential_value'].sum().reset_index()
    
    # Merge sales and potential summaries
    rm_province_summary = sales_summary.merge(potential_summary, on=['rm_position_cd', 'rm_name', 'rm_base_city_name', 'rm_base_province_name', 'hco_province_name'], how='outer')
    
    # Count the number of provinces covered by each RM
    rm_province_count = rm_province_summary.groupby('rm_position_cd')['hco_province_name'].nunique().reset_index()
    rm_province_count.columns = ['rm_position_cd', 'num_provinces_covered']
    
    # Find the province with the highest r6m_actual_sales and the province with the highest hospital potential for each RM
    rm_top_sales_province = rm_province_summary.loc[rm_province_summary.groupby('rm_position_cd')['r6m_actual_sales'].idxmax()][['rm_position_cd', 'hco_province_name']]
    rm_top_sales_province.columns = ['rm_position_cd', 'top_sales_province']
    
    rm_top_potential_province = rm_province_summary.loc[rm_province_summary.groupby('rm_position_cd')['hco_potential_value'].idxmax()][['rm_position_cd', 'hco_province_name']]
    rm_top_potential_province.columns = ['rm_position_cd', 'top_potential_province']
    
    # Merge the province coverage, top provinces, and base province information
    rm_evaluation = rm_province_summary.merge(rm_province_count, on='rm_position_cd', how='left')
    rm_evaluation = rm_evaluation.merge(rm_top_sales_province, on='rm_position_cd', how='left')
    rm_evaluation = rm_evaluation.merge(rm_top_potential_province, on='rm_position_cd', how='left')
    
    # Evaluate the base province alignment
    rm_evaluation['base_province_aligned'] = 'No'
    rm_evaluation.loc[rm_evaluation['rm_base_province_name'] == rm_evaluation['top_sales_province'], 'base_province_aligned'] = 'Yes'
    rm_evaluation.loc[rm_evaluation['rm_base_province_name'] == rm_evaluation['top_potential_province'], 'base_province_aligned'] = 'Yes'
    
    # Check if the RM covers provinces outside their base province
    rm_evaluation['cross_province'] = rm_evaluation.apply(lambda row: 'Yes' if row['rm_base_province_name'] != row['hco_province_name'] else 'No', axis=1)
    
    # Calculate cross_province_all
    cross_province_all = rm_evaluation.groupby('rm_position_cd')['cross_province'].apply(lambda x: 'Yes' if 'Yes' in x.values else 'No').reset_index()
    cross_province_all.columns = ['rm_position_cd', 'cross_province_all']
    
    # Merge cross_province_all into rm_evaluation
    rm_evaluation = rm_evaluation.merge(cross_province_all, on='rm_position_cd', how='left')
    
    # Check if a province has more than 2 different rm_position_cd
    province_rm_count = rm_evaluation.groupby('hco_province_name')['rm_position_cd'].nunique().reset_index()
    province_rm_count['multiple_rms'] = province_rm_count['rm_position_cd'].apply(lambda x: 'Yes' if x >= 2 else 'No')
    
    # Merge the multiple_rms information into rm_evaluation
    rm_evaluation = rm_evaluation.merge(province_rm_count[['hco_province_name', 'multiple_rms']], on='hco_province_name', how='left')
    
    return rm_evaluation[['rm_position_cd', 'rm_name', 'rm_base_city_name', 'rm_base_province_name', 'hco_province_name', 'r6m_actual_sales', 'hco_potential_value', 
                          'num_provinces_covered', 'top_sales_province', 'top_potential_province', 'base_province_aligned', 'cross_province', 'cross_province_all', 'multiple_rms']]