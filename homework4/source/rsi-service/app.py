from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

@app.route('/calculate_rsi', methods=['POST'])
def calculate_rsi():
     try:
         data = request.json['data']
         period = request.json.get('period', 14)
         df = pd.DataFrame(data)
         delta = df['LastTradePrice'].diff()
         gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
         loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
         rs = gain / loss
         rsi = 100 - (100 / (1 + rs))

         # Replace NaN and inf values
         rsi = rsi.replace([float('inf'), float('-inf')], None).fillna(0)

         return jsonify(rsi.tolist())
     except Exception as e:
         return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

