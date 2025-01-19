from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

@app.route('/calculate_macd', methods=['POST'])
def calculate_macd():
    try:
        data = request.json['data']
        short_window = request.json.get('short_window', 12)
        long_window = request.json.get('long_window', 26)
        signal_window = request.json.get('signal_window', 9)

        df = pd.DataFrame(data)
        short_ema = df['LastTradePrice'].ewm(span=short_window, adjust=False).mean()
        long_ema = df['LastTradePrice'].ewm(span=long_window, adjust=False).mean()
        macd = short_ema - long_ema
        signal_line = macd.ewm(span=signal_window, adjust=False).mean()

        # Replace NaN and inf values
        macd = macd.replace([float('inf'), float('-inf')], None).fillna(0)
        signal_line = signal_line.replace([float('inf'), float('-inf')], None).fillna(0)

        return jsonify({
            "MACD": macd.tolist(),
            "Signal_Line": signal_line.tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5003)