from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    return """
    <h2>Network Diagnostic Tool</h2>
    <form action="/ping" method="get">
        <label>Host to ping:</label><br>
        <input type="text" name="host" placeholder="e.g. 8.8.8.8" size="40">
        <input type="submit" value="Ping">
    </form>
    """

@app.route("/ping")
def ping():
    host = request.args.get("host", "")
    result = subprocess.check_output(f"ping -c 2 {host}", shell=True, stderr=subprocess.STDOUT)
    return f"<pre>{result.decode()}</pre><br><a href='/'>Back</a>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)