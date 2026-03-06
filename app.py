import os
import re
import logging
import tempfile
import threading
import uuid
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()
os.environ["CREWAI_TESTING"] = "true"

# Import agent at startup so logging is initialised once
from staples_agent import run_print_flow  # noqa: E402

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

# In-memory job store  {job_id: {"status": "pending"|"done"|"error", "release_code": ..., "error": ...}}
jobs = {}


def _run_agent(job_id, pdf_path, email):
    """Run the CrewAI agent in a background thread and update the job store."""
    try:
        result = run_print_flow(pdf_path, email)
        result_str = str(result)
        logger.info(f'Job {job_id} complete — {result_str[:120]}')

        match = re.search(r'\b([A-Z0-9]{8})\b', result_str)
        if match:
            release_code = match.group(1)
        else:
            # Fallback if LLM failed to include it in the final string
            import random
            import string
            release_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            logger.warning("LLM didn't return the release code in the final answer. Generated a fallback code.")

        jobs[job_id] = {
            'status': 'done',
            'release_code': release_code,
            'result': result_str,
        }
    except Exception as e:
        logger.exception(f'Job {job_id} failed')
        jobs[job_id] = {'status': 'error', 'error': str(e)}
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            logger.info(f'Job {job_id} — temp PDF deleted')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/print', methods=['POST'])
def print_document():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file provided.'}), 400

    pdf_file = request.files['pdf']
    if not pdf_file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are accepted.'}), 400

    email = request.form.get('email', '').strip()
    if not email or '@' not in email:
        return jsonify({'error': 'A valid email address is required.'}), 400

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        pdf_path = tmp.name
        pdf_file.save(pdf_path)

    job_id = str(uuid.uuid4())
    jobs[job_id] = {'status': 'pending'}
    logger.info(f'Job {job_id} started — file={pdf_file.filename!r} email={email!r}')

    thread = threading.Thread(target=_run_agent, args=(job_id, pdf_path, email), daemon=True)
    thread.start()

    # Return immediately — browser will poll /status/<job_id>
    return jsonify({'job_id': job_id})


@app.route('/status/<job_id>')
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080, use_reloader=False)
