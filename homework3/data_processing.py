import pandas as pd

def load_data(file_path):
    """
    Читање на CSV фајлот и враќање на DataFrame.
    """
    try:
        print(f"Loading data from {file_path}...")
        data = pd.read_csv(file_path)
        print(f"Data loaded successfully with {len(data)} rows and {len(data.columns)} columns.")
        print("Columns:", data.columns.tolist())
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def preprocess_data(data):
    """
    Претворање на колоната 'LastTradePrice' во нумерички тип и проверка за празни вредности.
    """
    if 'LastTradePrice' in data.columns:
        print("Processing 'LastTradePrice' column...")
        # Претвори ја колоната во нумерички формат
        data['LastTradePrice'] = pd.to_numeric(data['LastTradePrice'].str.replace(',', ''), errors='coerce')
        # Провери за празни вредности
        invalid_values = data['LastTradePrice'].isna().sum()
        print(f"Number of invalid values in 'LastTradePrice': {invalid_values}")
    else:
        print("'LastTradePrice' column not found in the dataset.")
    return data

def group_by_company(data):
    """
    Групирање на податоците по компанија.
    """
    if 'CompanyCode' in data.columns:
        print("Grouping data by company...")
        grouped_data = data.groupby('CompanyCode')
        print(f"Data grouped into {len(grouped_data)} groups.")
        return grouped_data
    else:
        print("'CompanyCode' column not found in the dataset.")
        return None
