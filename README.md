# Face Authentication System

> A biometric identity verification system using real-time facial recognition — built to explore the security properties, attack surface, and practical tradeoffs of face-based authentication.

---

## Overview

This project implements a face-based authentication pipeline using computer vision and deep learning. It covers the full lifecycle of a biometric auth system: **enrollment**, **verification**, and **access decision** — while analysing the security implications at each stage.

The system was built not just as a working prototype, but as a hands-on study of how biometric authentication works, where it can fail, and how its weaknesses map to real-world threat models.

---

## Features

- **Real-time face detection** via webcam using OpenCV
- **128-dimensional face encoding** using the `face_recognition` library (based on dlib's ResNet model)
- **CSV-based identity store** for enrollment records and face embeddings
- **Threshold-based access control** — configurable tolerance to tune the FAR/FRR tradeoff
- **Enrollment & verification workflow** — register new users, then authenticate against stored encodings

---

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  Webcam     │────▶│  Face Detection  │────▶│  Face Encoding    │
│  Input      │     │  (OpenCV + HOG)  │     │  (128-d vector)   │
└─────────────┘     └──────────────────┘     └────────┬──────────┘
                                                       │
                              ┌────────────────────────▼──────────┐
                              │    Compare against CSV database    │
                              │    using Euclidean distance        │
                              └────────────────────────┬──────────┘
                                                       │
                              ┌────────────────────────▼──────────┐
                              │  Distance < Threshold?            │
                              │  YES → ACCESS GRANTED             │
                              │  NO  → ACCESS DENIED              │
                              └───────────────────────────────────┘
```

---

## Project Structure

```
face-auth/
├── face-auth.ipynb       # Main notebook: enrollment, verification, analysis
├── requirements.txt      # All dependencies with pinned versions
├── SECURITY.md           # Threat model, known vulnerabilities, mitigations
├── README.md             # This file
└── LICENSE               # MIT License
```

---

## Setup & Installation

**Prerequisites:** Python 3.8+, a working webcam

```bash
# Clone the repository
git clone https://github.com/pharaoh77731/face-auth.git
cd face-auth

# Install dependencies
pip install -r requirements.txt

# Launch the notebook
jupyter notebook face-auth.ipynb
```

> **Note:** `face_recognition` requires `cmake` and `dlib` to build. On Ubuntu/Debian: `sudo apt install cmake`. On Windows, use a pre-built wheel or WSL.

---

## Usage

**Step 1 — Enroll a user**
Run the enrollment cell. The system captures your face via webcam, computes a 128-d encoding, and saves it to the CSV database with a username label.

**Step 2 — Authenticate**
Run the verification cell. The system captures a live frame, encodes it, and computes the Euclidean distance against all enrolled faces. If the closest match is within the configured tolerance threshold, access is granted.

**Step 3 — Adjust the threshold**
The default tolerance is `0.6`. Lower values (e.g. `0.45`) reduce false acceptances at the cost of more false rejections. See `SECURITY.md` for analysis.

---

## Tech Stack

| Library | Version | Purpose |
|---|---|---|
| `face_recognition` | 1.3.0 | Face encoding & comparison |
| `opencv-python` | 4.9.0.80 | Webcam capture, frame processing |
| `numpy` | 1.26.4 | Numerical operations on encodings |
| `pandas` | 2.2.1 | CSV database management |
| `matplotlib` | 3.8.3 | Visualisation of encodings & results |
| `jupyter` | 1.0.0 | Notebook runtime |

---

## Security Analysis

See [`SECURITY.md`](./SECURITY.md) for a detailed breakdown of:
- Threat model and attack surface
- Known vulnerabilities (photo spoofing, adversarial inputs, replay attacks)
- FAR / FRR tradeoff analysis
- Recommended mitigations

---

## Limitations

This is a **prototype for educational and research purposes**. It is not production-ready due to:
- No liveness detection (vulnerable to photo/video spoofing)
- Face encodings stored in plaintext CSV (no encryption at rest)
- No rate limiting on authentication attempts
- Single-factor — not suitable as a standalone auth mechanism for sensitive systems

---

## Author

**Bhupendra Singh**
[github.com/pharaoh77731](https://github.com/pharaoh77731)

---

## License

This project is licensed under the [MIT License](./LICENSE).
