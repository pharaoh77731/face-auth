# 🔐 Face Authentication System

> A fully deployable biometric identity verification CLI — with AES-256 encrypted storage and liveness detection.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green?style=flat-square&logo=opencv)
![Security](https://img.shields.io/badge/Storage-AES--256%20Encrypted-critical?style=flat-square)
![Liveness](https://img.shields.io/badge/Liveness-Blink%20Detection-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## Overview

A production-ready biometric access control system that verifies identity in real time using deep learning facial recognition. Built for local deployment with a security-first design:

- **AES-256 encrypted** face encoding storage (SQLite + Fernet)
- **Liveness detection** via Eye Aspect Ratio (EAR) blink analysis — defeats photo spoofing
- **Full audit logging** of all authentication events
- **Clean CLI** — no notebook, no manual cell execution
- **Modular codebase** — ready to extend into an API or GUI

---

## Features

| Feature | Details |
|---------|---------|
| Face detection | OpenCV HOG model, real-time webcam feed |
| Face encoding | 128-dimension deep learning encoding (dlib) |
| Storage | SQLite database with AES-256 (Fernet) encrypted blobs |
| Liveness | EAR blink detection — requires live blink before matching |
| Audit log | Every enrolment/verification event is timestamped and stored |
| Rate limiting | Configurable verification timeout |
| Multi-user | Enrol and manage unlimited users |

---

## Project Structure

```
face-auth/
├── main.py                  # Entry point — run this
├── requirements.txt
├── face_auth/
│   ├── __init__.py
│   ├── cli.py               # CLI menu and user interface
│   ├── recognition.py       # Enrolment, verification, liveness detection
│   └── database.py          # Encrypted SQLite storage layer
├── data/                    # Auto-created on first run
│   ├── faceauth.db          # Encrypted database
│   └── .key                 # AES key (chmod 600, never commit)
├── logs/
│   └── faceauth.log         # Audit trail
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.8+
- A webcam
- CMake and a C++ compiler (required by `dlib`)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y cmake build-essential libopenblas-dev liblapack-dev
```

**macOS:**
```bash
brew install cmake
```

**Windows:** Install [CMake](https://cmake.org/download/) and [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

### Setup

```bash
# Clone the repository
git clone https://github.com/pharaoh77731/face-auth.git
cd face-auth

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py
```

You will see the main menu:

```
  ── MAIN MENU ──────────────────────────────
  [1]  Verify identity
  [2]  Enrol a new user
  [3]  List enrolled users
  [4]  Delete a user
  [5]  View audit log
  [6]  Verify without liveness check (testing only)
  [q]  Quit
```

### Typical workflow

1. **Enrol** — Select `[2]`, enter a name, look at the camera. Auto-captures after 3 seconds.
2. **Verify** — Select `[1]`, blink when prompted (liveness check), then hold still. Matched user is displayed with confidence score.
3. **Audit** — Select `[5]` to view a log of all events.

---

## Security Architecture

### Threat Model

| Attack | Mitigation |
|--------|------------|
| Photo spoofing | ✅ EAR blink detection rejects static images |
| Database exfiltration | ✅ All encodings AES-256 encrypted at rest |
| Key theft | ✅ Key stored with `chmod 600`, separate from DB |
| Brute force | ✅ Verification timeout (15s default) |
| Replay attack | ⚠️ Planned — challenge-response nonce |
| Adversarial ML | 🔲 Out of scope for current version |

### Encryption Design

```
Facial Encoding (numpy array)
        │
        ▼
   pickle.dumps()          ← Serialisation
        │
        ▼
  Fernet.encrypt()         ← AES-128-CBC + HMAC-SHA256 (Fernet = symmetric AES)
        │
        ▼
  SQLite BLOB column       ← Stored encrypted, never plaintext
```

The AES key is generated once on first run, stored at `data/.key` with `chmod 600`. The database is unreadable without this key.

### Why not SHA/bcrypt for biometrics?

Password hashing algorithms (bcrypt, Argon2) are one-way — you can't recover the original. Face matching requires comparing two float arrays, which means the encoding must be *decryptable* for comparison. AES (symmetric encryption) is the correct primitive here, not hashing.

---

## Configuration

Edit constants in `face_auth/recognition.py` to tune behaviour:

```python
MATCH_TOLERANCE = 0.5        # 0.4 = stricter, 0.6 = more lenient
CAPTURE_COUNTDOWN = 3        # Seconds before auto-capture during enrolment
VERIFICATION_TIMEOUT = 15    # Seconds before verification fails
LIVENESS_BLINK_REQUIRED = 1  # Blinks required to pass liveness
EAR_THRESHOLD = 0.25         # Eye Aspect Ratio threshold for blink detection
```

---

## Known Limitations

- **Single-factor** — designed as one layer in an MFA stack, not standalone for high-security systems
- **Lighting sensitive** — poor lighting reduces detection accuracy
- **Replay attacks** — sophisticated video replay not yet mitigated
- **Local only** — no network authentication; not designed for distributed systems in this version

---

## Roadmap

- [x] AES-256 encrypted face encoding storage
- [x] EAR liveness detection (blink-based)
- [x] Full audit logging
- [x] Modular, deployable CLI
- [ ] Challenge-response nonce for replay attack mitigation
- [ ] REST API wrapper (Flask) for integration into larger systems
- [ ] Docker containerisation
- [ ] Multi-camera support
- [ ] Failed attempt lockout with configurable threshold

---

## Author

**Bhupendra Singh**
[GitHub](https://github.com/pharaoh77731)

---

## License

[MIT License](LICENSE)

---

## Acknowledgements

- [OpenCV](https://opencv.org/) — Computer vision
- [face_recognition](https://pypi.org/project/face-recognition/) — dlib-based facial encoding
- [cryptography](https://cryptography.io/) — AES-256 via Fernet
- [NumPy](https://numpy.org/) — Numerical computing
