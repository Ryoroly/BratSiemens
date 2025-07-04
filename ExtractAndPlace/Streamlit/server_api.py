# server_api.py
from flask import Flask, request, jsonify

app = Flask(__name__)

latest_data = {"image": None, "detections": []}

@app.route("/post", methods=["POST"])
def post_data():
    global latest_data
    data = request.get_json()
    latest_data["image"] = data.get("image")
    latest_data["detections"] = data.get("detections", [])
    print("✅ Received POST:", latest_data.keys())
    return jsonify({"status": "ok"})

@app.route("/get", methods=["GET"])
def get_data():
    return jsonify(latest_data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010)
