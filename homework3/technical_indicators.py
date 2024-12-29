import os
import pandas as pd


# Function to calculate RSI
def calculate_rsi(data, period=14):
    delta = data['LastTradePrice'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


# Function to calculate Moving Averages (SMA and EMA)
def calculate_moving_averages(data, windows=[5, 10, 20]):
    ma_data = pd.DataFrame(index=data.index)
    for window in windows:
        ma_data[f'SMA_{window}'] = data['LastTradePrice'].rolling(window=window).mean()
        ma_data[f'EMA_{window}'] = data['LastTradePrice'].ewm(span=window, adjust=False).mean()
    return ma_data


# Function to calculate MACD and Signal Line
def calculate_macd(data, short_window=12, long_window=26, signal_window=9):
    short_ema = data['LastTradePrice'].ewm(span=short_window, adjust=False).mean()
    long_ema = data['LastTradePrice'].ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=signal_window, adjust=False).mean()
    return macd, signal_line


# Function to calculate all indicators for a company
def calculate_indicators(company_df):
    result = company_df.copy()

    # RSI
    result['RSI'] = calculate_rsi(company_df)

    # Moving Averages
    ma_data = calculate_moving_averages(company_df)
    for col in ma_data.columns:
        result[col] = ma_data[col]

    # MACD and Signal Line
    macd, signal_line = calculate_macd(company_df)
    result['MACD'] = macd
    result['Signal_Line'] = signal_line

    return result


# Main part of the program
if __name__ == '__main__':

    # Path to the input CSV file
    file_path = 'company_data.csv'

    # Load the data
    print(f"Loading data from {file_path}...")
    data = pd.read_csv(file_path)

    # Ensure the 'Date' column is properly parsed
    data['Date'] = pd.to_datetime(data['Date'], format='%d.%m.%Y')

    # Ensure 'LastTradePrice' is numeric
    data['LastTradePrice'] = pd.to_numeric(data['LastTradePrice'].str.replace(',', ''), errors='coerce')

    # Group the data by company
    grouped_data = data.groupby('CompanyCode')

    # Directory to save the results
    output_dir = "data"

    # Create the directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Calculate indicators and save results for each company
    for company_name, company_df in grouped_data:
        print(f"Processing company: {company_name}")

        # Calculate indicators for the company
        indicators_df = calculate_indicators(company_df)

        # Save the results to a CSV file in the 'data' directory
        output_file = os.path.join(output_dir, f"{company_name}_indicators.csv")
        indicators_df.to_csv(output_file, index=False)
        print(f"Indicators saved for {company_name} in {output_file}")