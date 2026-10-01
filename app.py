"""
HaqqNama - "Know Before You Sign"
Main Flask Web Application Controller.
Manages document uploads, OCR pipelining, plain-language analysis,
audio explanations, comprehension verifications, cryptographic hashing, and post-sign disputes.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
)
from werkzeug.utils import secure_filename

# Load environment configuration
load_dotenv()

# Internal modular services and database operations
from database.models import (
    init_db, save_document, get_document, save_verification,
    save_consent, get_consent, save_complaint, get_complaint, log_audit
)
from services.hashing import calculate_sha256, generate_document_id, generate_complaint_id
from services.ocr import extract_document_text
from services.legal_explanation import analyze_legal_document, get_demo_analysis
from services.translation import get_translations_for_lang, translate_explanation
from services.speech import generate_audio_explanation

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'haqqnama-hackathon-secure-session-key-2026')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg'}

# Ensure necessary storage directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'audio'), exist_ok=True)

# Initialize database tables on application boot
init_db()


def is_allowed_file(filename):
    """Check if uploaded file has a permissible extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.context_processor
def inject_localization():
    """Inject current language dictionary into all Jinja templates."""
    lang = session.get('lang', 'en')
    translations = get_translations_for_lang(lang)
    return {'t': translations, 'current_lang': lang}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Landing page introducing HaqqNama and core actions."""
    return render_template('index.html')


@app.route('/set-language/<lang_code>')
def set_language(lang_code):
    """Update user session language preference."""
    if lang_code in ['en', 'ur', 'sd']:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))


@app.route('/upload')
def upload():
    """Document upload interface with drag-and-drop and sample triggers."""
    return render_template('upload.html')


@app.route('/process-document', methods=['POST'])
def process_document():
    """
    Handle document upload, perform SHA-256 integrity hashing,
    extract text via OCR, and run legal explanation analysis.
    """
    if 'document' not in request.files:
        flash('Please select a legal document file to upload.', 'danger')
        return redirect(url_for('upload'))

    file = request.files['document']
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('upload'))

    if not is_allowed_file(file.filename):
        flash('Unsupported file type. Please upload a PDF, PNG, JPG, or JPEG file.', 'danger')
        return redirect(url_for('upload'))

    orig_filename = secure_filename(file.filename)
    doc_id = generate_document_id()
    saved_filename = f"{doc_id}_{orig_filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
    file.save(file_path)

    # 1. Calculate SHA-256 hash for tamper-evident tracking
    file_hash = calculate_sha256(file_path)

    # 2. Perform OCR text extraction
    extracted_text, ocr_success, msg = extract_document_text(file_path)

    # 3. Analyze document text
    if ocr_success and len(extracted_text.strip()) > 30:
        analysis = analyze_legal_document(extracted_text)
    else:
        # Graceful fallback to demo analysis if OCR produces unreadable text
        analysis = get_demo_analysis()
        flash('Document text had low clarity; sample analysis loaded for demonstration.', 'warning')

    # 4. Persist to Database & Audit Log
    summary = analysis.get('summary', '')
    structured_json = json.dumps(analysis)
    save_document(
        document_id=doc_id,
        filename=saved_filename,
        original_filename=orig_filename,
        file_hash=file_hash,
        extracted_text=extracted_text,
        structured_data=structured_json,
        summary=summary,
        language=session.get('lang', 'en')
    )
    log_audit(doc_id, "DOCUMENT_PROCESSED", f"Uploaded {orig_filename} with SHA-256: {file_hash[:16]}...")

    # Store active identifiers in session
    session['current_doc_id'] = doc_id
    session['current_file_hash'] = file_hash

    return redirect(url_for('explanation'))


@app.route('/demo')
def demo_flow():
    """Trigger pre-loaded sample workflow representing a rural Khairpur inheritance dispute."""
    doc_id = generate_document_id()
    demo_hash = calculate_sha256(b"DEMO_KHAIRPUR_INHERITANCE_RELINQUISHMENT_SAMPLE_2026")
    analysis = get_demo_analysis()

    save_document(
        document_id=doc_id,
        filename="demo_relinquishment_khairpur.pdf",
        original_filename="demo_relinquishment_khairpur.pdf",
        file_hash=demo_hash,
        extracted_text="Demo Deed of Relinquishment text...",
        structured_data=json.dumps(analysis),
        summary=analysis['summary'],
        language=session.get('lang', 'en')
    )
    log_audit(doc_id, "DEMO_INITIALIZED", "User loaded Khairpur inheritance sample deed.")

    session['current_doc_id'] = doc_id
    session['current_file_hash'] = demo_hash

    return redirect(url_for('explanation'))


@app.route('/explanation')
def explanation():
    """Display plain-language breakdown, clauses, consequences, and audio."""
    doc_id = session.get('current_doc_id')
    if not doc_id:
        return redirect(url_for('upload'))

    doc = get_document(doc_id)
    if not doc:
        return redirect(url_for('upload'))

    raw_data = json.loads(doc['structured_data'])
    target_lang = session.get('lang', 'en')
    localized_data = translate_explanation(raw_data, target_lang)

    # Generate or retrieve TTS narration audio
    audio_file, audio_ok, _ = generate_audio_explanation(localized_data.get('summary', ''), target_lang)

    return render_template(
        'explanation.html',
        doc_id=doc_id,
        data=localized_data,
        audio_file=audio_file,
        file_hash=doc['file_hash']
    )


@app.route('/verification')
def verification():
    """Display 3 comprehension questions to ensure signer understanding."""
    doc_id = session.get('current_doc_id')
    if not doc_id:
        return redirect(url_for('upload'))

    return render_template('verification.html', doc_id=doc_id)


@app.route('/submit-verification', methods=['POST'])
def submit_verification():
    """Score comprehension answers and verify signer readiness."""
    doc_id = session.get('current_doc_id')
    if not doc_id:
        return redirect(url_for('upload'))

    q1 = request.form.get('q1')
    q2 = request.form.get('q2')
    q3 = request.form.get('q3')

    # Correct answers: Q1 -> A (Permanently surrendered), Q2 -> B (Waives claims), Q3 -> A (Spoken words don't override paper)
    score = 0
    if q1 == 'A':
        score += 1
    if q2 == 'B':
        score += 1
    if q3 == 'A':
        score += 1

    passed = (score == 3)

    v_id = save_verification(
        document_id=doc_id,
        q1="Consequence on share", a1=q1,
        q2="Right to challenge in court", a2=q2,
        q3="Verbal promises vs paper", a3=q3,
        passed=passed, score=score, total=3
    )

    log_audit(doc_id, "VERIFICATION_ATTEMPT", f"Score: {score}/3, Passed: {passed}")

    if passed:
        session['verification_id'] = v_id
        session['verification_passed'] = True
        return redirect(url_for('consent'))
    else:
        flash("One or more answers were incorrect. Please review the explanation again to ensure you understand your rights.", "danger")
        return redirect(url_for('explanation'))


@app.route('/consent')
def consent():
    """Informed consent confirmation screen."""
    doc_id = session.get('current_doc_id')
    if not doc_id or not session.get('verification_passed'):
        flash("Please complete the comprehension verification first.", "warning")
        return redirect(url_for('verification'))

    doc = get_document(doc_id)
    return render_template(
        'consent.html',
        doc_id=doc_id,
        file_hash=doc['file_hash'],
        summary=doc['summary']
    )


@app.route('/confirm-consent', methods=['POST'])
def confirm_consent():
    """Record informed understanding milestone and generate digital receipt."""
    doc_id = session.get('current_doc_id')
    if not doc_id:
        return redirect(url_for('upload'))

    doc = get_document(doc_id)
    save_consent(
        document_id=doc_id,
        file_hash=doc['file_hash'],
        language_used=session.get('lang', 'en'),
        verification_id=session.get('verification_id')
    )
    log_audit(doc_id, "CONSENT_CONFIRMED", "User acknowledged informed understanding.")

    return redirect(url_for('receipt', document_id=doc_id))


@app.route('/receipt/<document_id>')
def receipt(document_id):
    """Digital document receipt with tamper-evident SHA-256 fingerprint."""
    doc = get_document(document_id)
    if not doc:
        flash("Document record not found.", "danger")
        return redirect(url_for('index'))

    consent_record = get_consent(document_id)
    return render_template(
        'consent.html',
        doc_id=doc['document_id'],
        file_hash=doc['file_hash'],
        summary=doc['summary'],
        consent_record=consent_record,
        is_receipt=True
    )


@app.route('/complaint')
def complaint():
    """Post-signing concern / dispute registration screen."""
    doc_id = request.args.get('doc_id', session.get('current_doc_id', ''))
    return render_template('complaint.html', preset_doc_id=doc_id)


@app.route('/submit-complaint', methods=['POST'])
def submit_complaint():
    """Store formal concern and return timestamped tracking ID."""
    doc_id = request.form.get('document_id', '').strip() or "HQN-MANUAL-ENTRY"
    concern_type = request.form.get('concern_type', 'General Dispute')
    description = request.form.get('description', '').strip()
    supporting_info = request.form.get('supporting_info', '').strip()

    if not description:
        flash("Please describe your concern so it can be recorded.", "danger")
        return redirect(url_for('complaint'))

    complaint_id = generate_complaint_id()
    save_complaint(complaint_id, doc_id, concern_type, description, supporting_info)
    log_audit(doc_id, "COMPLAINT_SUBMITTED", f"Complaint {complaint_id} recorded for {concern_type}")

    saved_complaint = get_complaint(complaint_id)
    return render_template('complaint.html', complaint=saved_complaint)


@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve cached TTS audio files."""
    audio_dir = os.path.join(app.root_path, 'static', 'audio')
    return send_from_directory(audio_dir, secure_filename(filename))


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(413)
def file_too_large(e):
    flash("The uploaded file exceeds the 16MB limit. Please upload a smaller file.", "danger")
    return redirect(url_for('upload')), 413


@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)