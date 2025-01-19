from flask import Flask, request, jsonify, render_template
import pandas as pd
import requests
import os

app = Flask(__name__)

# Base URLs for microservices
RSI_SERVICE_URL = "http://rsi-service:5001/calculate_rsi"
MOVING_AVERAGE_SERVICE_URL = "http://moving-average-service:5002/calculate_moving_averages"
MACD_SERVICE_URL = "http://macd-service:5003/calculate_macd"

# Path to the CSV file
DATA_PATH = os.path.join("data", "company_data.csv")

# Check if the file exists
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"File not found: {DATA_PATH}")

# Read the CSV file into a DataFrame
data = pd.read_csv(DATA_PATH, low_memory=False)

# Ensure the 'Date' column is properly parsed
if 'Date' in data.columns:
    data['Date'] = pd.to_datetime(data['Date'], format='%d.%m.%Y')
else:
    raise ValueError("The 'Date' column is missing in the CSV file.")

# Ensure 'LastTradePrice' is numeric
if 'LastTradePrice' in data.columns:
    data['LastTradePrice'] = pd.to_numeric(data['LastTradePrice'].str.replace(',', ''), errors='coerce')
else:
    raise ValueError("The 'LastTradePrice' column is missing in the CSV file.")

print(data.head())  # Печати ги првите неколку редови од CSV фајлот
print(data.columns)  # Печати ги колоните за да осигурате дека се правилни


@app.route('/')
def index():
    # Get unique company codes for dropdown selection
    companies = data['CompanyCode'].drop_duplicates().tolist()
    print(companies)  # Печати ја листата на компании
    return render_template('index.html', companies=companies)


print(data['CompanyCode'].head())  # Печати ги првите неколку вредности од колоната

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Parse user input from form submission
        company_code = request.form.get('company')
        indicators = request.form.getlist('indicators')
        timeframe = request.form.get('timeframe', 'daily')

        # Filter data for the selected company
        company_data = data[data['CompanyCode'] == company_code]

        if company_data.empty:
            raise ValueError(f"No data available for the selected company: {company_code}")

        # Filter data based on timeframe
        if timeframe == 'weekly':
            filtered_data = company_data.tail(7)
        elif timeframe == 'monthly':
            filtered_data = company_data.tail(30)
        else:
            filtered_data = company_data

        if filtered_data.empty:
            raise ValueError(f"No data available for the selected timeframe: {timeframe}")

        # Replace problematic values
        filtered_data = filtered_data.replace([float('inf'), float('-inf')], None)
        filtered_data = filtered_data.fillna(0)

        # Convert to dictionary for JSON serialization
        filtered_data_dict = filtered_data.to_dict(orient='records')

        # Prepare results dictionary (example)
        results = {
            "signals": {"buy": 5, "sell": 3, "hold": 2},  # Example signals
            "graph": {
                "data": [{"x": [1, 2, 3], "y": [4, 5, 6], "type": "scatter"}],
                "layout": {"title": "Example Graph"}
            }
        }

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_companies', methods=['GET'])
def get_companies():
    # Извлекување на уникатни компании од CSV фајлот
    companies = data['CompanyCode'].drop_duplicates().tolist()
    return jsonify({'companies': companies})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
