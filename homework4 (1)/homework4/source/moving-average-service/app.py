from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)


@app.route('/calculate_moving_averages', methods=['POST'])
def calculate_moving_averages():
    try:
        data = request.json['data']
        windows = request.json.get('windows', [5, 10, 20])
        df = pd.DataFrame(data)
        ma_data = {}
        for window in windows:
            sma = df['LastTradePrice'].rolling(window=window).mean()
            ema = df['LastTradePrice'].ewm(span=window, adjust=False).mean()

            # Replace NaN and inf values
            sma = sma.replace([float('inf'), float('-inf')], None).fillna(0)
            ema = ema.replace([float('inf'), float('-inf')], None).fillna(0)

            ma_data[f'SMA_{window}'] = sma.tolist()
            ma_data[f'EMA_{window}'] = ema.tolist()

        return jsonify(ma_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5002 , debug=True)
