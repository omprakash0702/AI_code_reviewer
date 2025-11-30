from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_URL = "http://127.0.0.1:8000/review"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/review", methods=["POST"])
def review():
    filename = request.form.get("filename")
    code = request.form.get("code")

    payload = {
        "filename": filename,
        "code": code,
        "analysis": {"lint_issues": []}
    }

    try:
        res = requests.post(API_URL, json=payload)
        return jsonify(res.json())
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
