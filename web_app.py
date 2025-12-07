import json

from flask import Flask, request, render_template_string

from process_case_from_url import process_uscis_case

app = Flask(__name__)

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Imli – USCIS Case Analyzer</title>
    <style>
        body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; max-width: 900px; }
        h1 { margin-bottom: 0.5rem; }
        form { margin-bottom: 1.5rem; }
        input[type="text"] { width: 100%; padding: 0.5rem; font-size: 1rem; }
        button { padding: 0.5rem 1rem; font-size: 1rem; cursor: pointer; }
        .error { color: #b00020; margin-bottom: 1rem; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-top: 1rem; }
        .field-label { font-weight: 600; }
        pre { background: #f6f6f6; padding: 1rem; border-radius: 6px; overflow-x: auto; }
        ul { padding-left: 1.2rem; }
    </style>
</head>
<body>
    <h1>Imli – USCIS/AAO Case Analyzer</h1>
    <p>Paste a direct USCIS/AAO PDF URL below. Imli will fetch the decision, extract the text, and return a structured analysis.</p>

    <form method="POST">
        <label for="url"><strong>USCIS/AAO PDF URL</strong></label><br>
        <input type="text" id="url" name="url" value="{{ url|default('') }}" placeholder="https://www.uscis.gov/sites/default/files/err/.../DECISION.pdf">
        <br><br>
        <button type="submit">Analyze</button>
    </form>

    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}

    {% if result %}
        <div class="card">
            <h2>Case Overview</h2>
            <p><span class="field-label">Visa Type:</span> {{ result.visa_type or 'unknown' }}</p>
            <p><span class="field-label">Case Type:</span> {{ result.case_type or 'unknown' }}</p>
            <p><span class="field-label">Decision Outcome:</span> {{ result.decision_outcome or 'unknown' }}</p>
            <p><span class="field-label">Decision Date:</span> {{ result.decision_date or 'unknown' }}</p>
            <p><span class="field-label">Service Center:</span> {{ result.service_center or 'unknown' }}</p>
            <p><span class="field-label">Beneficiary Role:</span> {{ result.beneficiary_role or 'unknown' }}</p>

            {% if result.issues %}
                <h3>Key Issues</h3>
                <ul>
                {% for issue in result.issues %}
                    <li>{{ issue }}</li>
                {% endfor %}
                </ul>
            {% endif %}

            {% if result.criteria_not_met %}
                <h3>Criteria Not Met</h3>
                <ul>
                {% for c in result.criteria_not_met %}
                    <li>{{ c }}</li>
                {% endfor %}
                </ul>
            {% endif %}

            {% if result.notes %}
                <h3>Notes</h3>
                <p>{{ result.notes }}</p>
            {% endif %}
        </div>

        <div class="card">
            <h2>Full JSON</h2>
            <pre>{{ json_text }}</pre>
        </div>
    {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    url = ""
    result = None
    error = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            error = "Please enter a URL."
        else:
            try:
                data = process_uscis_case(url)
                # Flask/Jinja likes attribute-style access; wrap in SimpleNamespace-like object
                class Obj(dict):
                    __getattr__ = dict.get
                result = Obj(data)
            except Exception as e:
                error = f"Error processing URL: {e}"

    json_text = json.dumps(result, indent=2) if result else ""

    return render_template_string(
        PAGE_TEMPLATE,
        url=url,
        result=result,
        json_text=json_text,
        error=error,
    )


if __name__ == "__main__":
    # Run the app locally
    app.run(host="127.0.0.1", port=5000, debug=True)
