from flask import Flask, request, jsonify
import math
import random
import json

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    results = perform_analysis(data)
    return jsonify(results),200

def perform_analysis(data):
    input_data = data['data']
    minhistory = int(data['minhistory'])
    shots = int(data['shots'])
    days = int(data['days'])

    results = []

    # Analysis for Buy Signals
    for i in range(len(input_data)):
        body = 0.01

        # Three Soldiers
        if (
            input_data[i]['Close'] - input_data[i]['Open'] >= body
            and input_data[i]['Close'] > input_data[i - 1]['Close']
            and input_data[i - 1]['Close'] - input_data[i - 1]['Open'] >= body
            and input_data[i - 1]['Close'] > input_data[i - 2]['Close']
            and input_data[i - 2]['Close'] - input_data[i - 2]['Open'] >= body
        ):
            input_data[i]['Buy'] = 1

    for i in range(minhistory, len(input_data) - days):
        if input_data[i]['Buy'] == 1:
            Buy_Date = input_data[i]['Date']
            Sell_Date = input_data[i + days]['Date']
            Buy_Price = input_data[i]['Close']
            Sell_Price = input_data[i + days]['Close']
            Difference_of_Price = Sell_Price - Buy_Price
            if Difference_of_Price > 0:
                Profit_or_Loss = "Profit"
            elif Difference_of_Price < 0:
                Profit_or_Loss = "Loss"
            else:
                Profit_or_Loss = "Same Price"
            Percentage_of_Profit_or_Loss = Difference_of_Price / Buy_Price

            history = [input_data[j]['Close'] for j in range(i - minhistory, i)]
            pct_change = [((b - a) / a) for a, b in zip(history[:-1], history[1:])]
            mean = sum(pct_change) / len(pct_change)
            std = math.sqrt(sum((x - mean) ** 2 for x in pct_change) / len(pct_change))
            simulated = sorted([random.gauss(mean, std) for _ in range(shots)], reverse=True)
            var95 = simulated[int(len(simulated) * 0.95)]
            var99 = simulated[int(len(simulated) * 0.99)]

            results.append(
                {
                    "Buy_Date": Buy_Date,
                    "Sell_Date": Sell_Date,
                    "Buy_Price": Buy_Price,
                    "Sell_Price": Sell_Price,
                    "Difference_of_Price": Difference_of_Price,
                    "Profit_or_Loss": Profit_or_Loss,
                    "Percentage_of_Profit_or_Loss": Percentage_of_Profit_or_Loss,
                    "var95": var95,
                    "var99": var99,
                }
            )

    # Analysis for Sell Signals
    for i in range(len(input_data)):
        body = 0.01

        # Three Crows
        if (
            input_data[i]['Open'] - input_data[i]['Close'] >= body
            and input_data[i]['Close'] < input_data[i - 1]['Close']
            and input_data[i - 1]['Open'] - input_data[i - 1]['Close'] >= body
            and input_data[i - 1]['Close'] < input_data[i - 2]['Close']
            and input_data[i - 2]['Open'] - input_data[i - 2]['Close'] >= body
            ):
            input_data[i]['Sell'] = 1

    for i in range(minhistory, len(input_data) - days):
        if input_data[i]['Sell'] == 1:
            Buy_Date = input_data[i - days]['Date']
            Sell_Date = input_data[i]['Date']
            Buy_Price = input_data[i - days]['Close']
            Sell_Price = input_data[i]['Close']
            Difference_of_Price = Sell_Price - Buy_Price
            if Difference_of_Price > 0:
                Profit_or_Loss = "Profit"
            elif Difference_of_Price < 0:
                Profit_or_Loss = "Loss"
            else:
                Profit_or_Loss = "Same Price"
            Percentage_of_Profit_or_Loss = Difference_of_Price / Buy_Price

            history = [input_data[j]['Close'] for j in range(i - minhistory, i)]
            pct_change = [((b - a) / a) for a, b in zip(history[:-1], history[1:])]
            mean = sum(pct_change) / len(pct_change)
            std = math.sqrt(sum((x - mean) ** 2 for x in pct_change) / len(pct_change))
            simulated = sorted([random.gauss(mean, std) for _ in range(shots)], reverse=True)
            var95 = simulated[int(len(simulated) * 0.95)]
            var99 = simulated[int(len(simulated) * 0.99)]
            
             results.append(
                {
                    "Buy_Date": Buy_Date,
                    "Sell_Date": Sell_Date,
                    "Buy_Price": Buy_Price,
                    "Sell_Price": Sell_Price,
                    "Difference_of_Price": Difference_of_Price,
                    "Profit_or_Loss": Profit_or_Loss,
                    "Percentage_of_Profit_or_Loss": Percentage_of_Profit_or_Loss,
                    "var95": var95,
                    "var99": var99,
                }
            )

    return results

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
