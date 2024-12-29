import pandas as pd
import plotly.graph_objs as go
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Path to the CSV file
DATA_PATH = os.path.join("data", "company_data.csv")

# Check if the file exists
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"File not found: {DATA_PATH}")

# Read CSV data
data = pd.read_csv(DATA_PATH, low_memory=False)

# Ensure the date is properly parsed
if 'Date' in data.columns:
    data['Date'] = pd.to_datetime(data['Date'], format='%d.%m.%Y')
else:
    raise ValueError("The 'Date' column is missing in the CSV file.")

# Ensure 'LastTradePrice' is numeric
if 'LastTradePrice' in data.columns:
    data['LastTradePrice'] = pd.to_numeric(data['LastTradePrice'].str.replace(',', ''), errors='coerce')
else:
    raise ValueError("The 'LastTradePrice' column is missing in the CSV file.")


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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_companies', methods=['GET'])
def get_companies():
    try:
        companies = data['CompanyCode'].drop_duplicates().tolist()
        return jsonify({"companies": companies})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        company = request.form.get('company')
        timeframe = request.form.get('timeframe', 'daily')

        # Get selected indicators from the form
        selected_indicators = request.form.getlist('indicators')

        # Filter data by the selected company
        company_data = data[data['CompanyCode'] == company]

        if company_data.empty:
            raise ValueError(f"No data available for the selected company: {company}")

        # Hardcoded current date for testing (today is fixed as 9th November 2024)
        hardcoded_date = datetime(2024, 11, 7)

        # Filter data based on timeframe
        if timeframe == 'weekly':
            last_week_start = hardcoded_date - timedelta(days=6)
            filtered_data = company_data[
                (company_data['Date'] >= last_week_start) & (company_data['Date'] <= hardcoded_date)]

        elif timeframe == 'monthly':
            last_month_start = hardcoded_date - timedelta(days=29)
            filtered_data = company_data[
                (company_data['Date'] >= last_month_start) & (company_data['Date'] <= hardcoded_date)]

        else:
            filtered_data = company_data

        if filtered_data.empty:
            raise ValueError(f"No data available for the selected timeframe: {timeframe}")

        # Calculate indicators for the filtered data
        indicators_df = calculate_indicators(filtered_data)

        # Count buy, sell, and hold signals
        signals_summary = calculate_signals(indicators_df, selected_indicators)

        # Generate Plotly graph using selected indicators
        fig = go.Figure()

        for indicator in selected_indicators:
            if indicator in indicators_df.columns:
                fig.add_trace(go.Scatter(
                    x=indicators_df['Date'],
                    y=indicators_df[indicator],
                    mode='lines',
                    name=indicator
                ))

        graph_json = fig.to_json()

        return jsonify({
            "graph": graph_json,
            "signals": signals_summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def calculate_signals(indicators_df, selected_indicators):
    """
    Calculate buy, sell, and hold signals based on indicators.
    """
    buy_signals = 0
    sell_signals = 0
    hold_signals = 0

    for _, row in indicators_df.iterrows():
        # RSI Logic
        if 'RSI' in selected_indicators and not pd.isna(row['RSI']):
            if row['RSI'] > 70:
                sell_signals += 1
            elif row['RSI'] < 30:
                buy_signals += 1
            else:
                hold_signals += 1

        # SMA and EMA Logic
        for ma_type in ['SMA', 'EMA']:
            if f'{ma_type}_5' in selected_indicators and f'{ma_type}_10' in selected_indicators:
                if row[f'{ma_type}_5'] > row[f'{ma_type}_10']:
                    buy_signals += 1
                elif row[f'{ma_type}_5'] < row[f'{ma_type}_10']:
                    sell_signals += 1
                else:
                    hold_signals += 1

            if f'{ma_type}_5' in selected_indicators and f'{ma_type}_20' in selected_indicators:
                if row[f'{ma_type}_5'] > row[f'{ma_type}_20']:
                    buy_signals += 1
                elif row[f'{ma_type}_5'] < row[f'{ma_type}_20']:
                    sell_signals += 1
                else:
                    hold_signals += 1

        # MACD and Signal Line Logic
        if 'MACD' in selected_indicators and 'Signal_Line' in selected_indicators:
            if row['MACD'] > row['Signal_Line']:
                buy_signals += 1
            elif row['MACD'] < row['Signal_Line']:
                sell_signals += 1
            else:
                hold_signals += 1

    return {"buy": buy_signals, "sell": sell_signals, "hold": hold_signals}



if __name__ == '__main__':
    app.run(debug=True)
