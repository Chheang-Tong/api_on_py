from flask import Flask, jsonify, request

app = Flask(__name__)

# Example route
@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello, World!"})

# Example POST route
@app.route('/echo', methods=['POST'])
def echo():
    data = request.json
    return jsonify({"you_sent": data})

if __name__ == '__main__':
    app.run(debug=True)
