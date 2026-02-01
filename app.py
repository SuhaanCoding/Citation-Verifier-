"""
Citation Verifier - Flask Web Frontend

Serves the web UI and acts as an A2A client to the Supervisor agent.
For Phase 1, this is a skeleton that will be connected to agents later.
"""
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config

app = Flask(__name__)


@app.route("/")
def index():
    """Render the main page with text input form."""
    return render_template("index.html")


@app.route("/verify", methods=["POST"])
def verify():
    """
    Submit text for citation verification.
    
    Phase 1: Returns a stub response.
    Later: Sends text to Supervisor Agent via A2A.
    """
    text = request.form.get("text", "")
    
    if not text.strip():
        return jsonify({"error": "No text provided"}), 400
    
    # TODO: Phase 3 - Send to Supervisor Agent via A2A
    # For now, return a stub response
    return jsonify({
        "status": "received",
        "message": "Citation verification coming soon!",
        "text_length": len(text)
    })


@app.route("/status/<task_id>")
def status(task_id: str):
    """
    Check verification task status.
    
    Phase 1: Returns stub.
    Later: Queries Supervisor Agent for task state.
    """
    return jsonify({
        "task_id": task_id,
        "status": "pending",
        "message": "Status checking coming in Phase 3"
    })


@app.route("/report/<task_id>")
def report(task_id: str):
    """
    Display verification report.
    
    Phase 1: Returns stub template.
    Later: Renders actual hallucination report.
    """
    # Stub data for template development
    stub_report = {
        "overall_score": 75.0,
        "total_citations": 3,
        "verified_count": 2,
        "flagged_count": 1,
        "analysis_mode": "tfidf",
        "citations": []
    }
    return render_template("report.html", report=stub_report)


@app.route("/health")
def health():
    """Health check endpoint for Docker."""
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = Config.FLASK_PORT
    debug = Config.DEBUG
    
    print(f"Starting Citation Verifier on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
