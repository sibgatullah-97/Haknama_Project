# HaqqNama
## Know Before You Sign

**HaqqNama** ("Document of Truth / Rights") is an independent digital transparency and informed-consent platform designed for vulnerable citizens—particularly rural women and inheritors in Khairpur, Sindh, Pakistan—navigating high-stakes legal documents such as land transfers, inheritance waivers, and relinquishment deeds (*Dastbardari*).

---

### 1. Project Overview

In rural communities, legal paperwork is predominantly drafted in complex legal Urdu or English. Signers frequently rely on verbal explanations provided by interested third parties (beneficiary relatives, agents, or aligned legal actors). 

HaqqNama interrupts this cycle of asymmetric information. It extracts document contents via OCR, analyzes high-impact clauses, translates them into accessible English, Urdu, and Sindhi, provides spoken voice explanations, tests the signer's comprehension, and issues a tamper-evident SHA-256 digital audit receipt.

---

### 2. Problem Statement

> **"The Signature That Signs Away Everything"**

1. **Misleading Verbal Summaries:** Signers are verbally told they are signing an authorization to "look after the family land," while the physical document constitutes a permanent, irrevocable surrender of their inheritance share.
2. **Patwari / Revenue Office Conflict of Interest:** When signers realize the disparity, local land registry officials (*Tapedars* / *Patwaris*) responsible for registering mutations (*Dakhil Kharij*) may have personal or financial connections to the beneficiary.
3. **Evidence Trap:** Once signed, the document becomes definitive evidence in revenue courts. Challenging family members is socially punitive, financially prohibitive, and takes years in court.

---

### 3. Our Solution & Core Principle

> *"We don't stop the signature. We make the signature informed."*

HaqqNama remains strictly **neutral**:
* It does **not** command the user: *"You should sign"* or *"You should not sign"*.
* It eliminates reliance on biased verbal summaries by presenting unvarnished, plain-language facts.
* It guarantees that signers verify their own comprehension prior to acknowledging consent.

---

### 4. Key Features

- **Document Ingestion:** Drag-and-drop support for PDF and image scans (PNG, JPG, JPEG) up to 16 MB.
- **OCR Engine:** Isolated optical character recognition powered by PyTesseract and Pillow with deterministic demo fallbacks.
- **Clause Extraction:** Automated detection of relinquishment deeds, zero-compensation (*PKR 0*) clauses, and court waiver bars.
- **Trilingual Localization:** Native interface and explanations in **English**, **اردو (Urdu)**, and **سنڌي (Sindhi)**.
- **Audio Narration (TTS):** Spoken explanations for users with limited digital or text literacy via Google Text-to-Speech (gTTS).
- **Conflict of Interest Detection:** Flags uncompensated transfers to relatives and directives targeting immediate Patwari mutations.
- **Comprehension Gate (Verification):** Multi-choice questions confirming signer understanding before consent can be registered.
- **Tamper-Evident SHA-256 Fingerprinting:** Generates verifiable mathematical digests of all ingested documents.
- **Post-Sign Dispute Logging:** Structured complaint desk issuing tracking IDs (`HQN-C-2026-XXXX`) to timestamp discrepancies.
- **Deterministic Hackathon Demo Mode:** Fully functional simulation of a rural Khairpur inheritance case that works offline without live external APIs.

---

### 5. Target Users

- **Primary:** Rural women dealing with inheritance, agricultural landholders, and individuals with limited English or legal Urdu literacy.
- **Secondary:** Legal-aid NGOs, public-interest lawyers, community paralegals, and dispute resolution committees.

---

### 6. Technology Stack

- **Backend:** Python, Flask
- **Frontend:** Semantic HTML5, CSS3 (Bilingual LTR/RTL support), Vanilla JavaScript
- **Database:** SQLite3
- **OCR & Imaging:** Tesseract OCR, PyTesseract, Pillow
- **Text-to-Speech:** gTTS (Google Text-to-Speech)
- **Security:** SHA-256 cryptographic hashing, Werkzeug file sanitization, secure session integrity

---

### 7. Project Architecture

```text
haqqnama/
│
├── README.md
├── app.py
├── requirements.txt
├── .env
├── haqqnama.db
│
├── templates/
│   ├── index.html
│   ├── upload.html
│   ├── explanation.html
│   ├── verification.html
│   ├── consent.html
│   └── complaint.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── main.js
│   └── audio/
│
├── uploads/
│
├── services/
│   ├── __init__.py
│   ├── ocr.py
│   ├── legal_explanation.py
│   ├── translation.py
│   ├── speech.py
│   └── hashing.py
│
└── database/
    ├── __init__.py
    └── models.py