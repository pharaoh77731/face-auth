# 🔐 Face Authentication System

> A biometric identity verification system using deep learning — built with a security-first mindset.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-green?style=flat-square&logo=opencv)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

---

## Overview

The Face Authentication System is a biometric access control tool that verifies individual identity by analysing facial features in real time. It demonstrates the practical application of computer vision and machine learning in cybersecurity contexts such as physical access control, attendance verification, and multi-factor authentication (MFA) pipelines.

This project was built with an awareness of the security trade-offs inherent in biometric systems — including spoofing risks and data-at-rest vulnerabilities — making it a practical study in both implementation and threat modelling.

---

## Features

- **Real-time face detection** using OpenCV's camera feed
- **Deep learning–based facial encoding** via the `face_recognition` library (dlib backend)
- **Enrolment workflow** — register new individuals with their facial embeddings
- **Verification workflow** — compare live face data against stored encodings
- **Structured data storage** — facial encodings stored with associated metadata

---

## Security Design Considerations

> This section documents the threat model and known limitations — critical for any security-aware deployment.

### Known Attack Vectors

| Attack | Description | Mitigation Status |
|--------|-------------|-------------------|
| **Photo Spoofing** | Static image used to fool the camera | ⚠️ Partially mitigated — liveness detection planned |
| **Replay Attack** | Recorded video replayed at camera | ⚠️ Not yet mitigated |
| **Database Exfiltration** | Facial encodings stolen from storage | 🔲 Encryption of stored encodings planned |
| **Adversarial Input** | Crafted images designed to fool the model | 🔲 Out of scope for current version |

### Current Limitations

- Facial encodings are stored in plaintext — **not suitable for production** without encryption at rest
- No liveness detection — the system can potentially be fooled by a high-quality photograph
- Single-factor — intended as one layer in a broader MFA architecture, not standalone authentication

### Planned Hardening

- [ ] AES-256 encryption of stored facial embeddings
- [ ] Eye Aspect Ratio (EAR) based blink detection for liveness
- [ ] Rate limiting on failed authentication attempts
- [ ] Audit logging of all authentication events

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| Computer Vision | OpenCV |
| Face Analysis | face_recognition (dlib) |
| Numerical Computing | NumPy |
| Data Handling | Pandas |
| Visualisation | Matplotlib |

---

## Getting Started

### Prerequisites

```bash
pip install opencv-python face_recognition numpy pandas matplotlib
```

> **Note:** `face_recognition` requires `dlib`, which may need CMake and a C++ compiler. See [dlib installation guide](http://dlib.net/compile.html).

### Installation

```bash
git clone https://github.com/pharaoh77731/face-auth.git
cd face-auth
pip install -r requirements.txt
```

### Usage

Open `face-auth.ipynb` in Jupyter Notebook or VS Code:

```bash
jupyter notebook face-auth.ipynb
```

**Step 1 — Enrolment:** Run the enrolment cells to capture and store a user's facial encoding.

**Step 2 — Authentication:** Run the verification cells to compare a live face against the database.

---

## Project Structure

```
face-auth/
├── face-auth.ipynb      # Main notebook: enrolment & authentication pipeline
├── README.md            # Project documentation
└── LICENSE              # MIT License
```

---

## Cybersecurity Context

Biometric authentication is increasingly used across sectors — from border control to mobile banking. However, biometric systems introduce unique risks compared to password-based auth:

- **Biometrics are not revocable** — if a face encoding is leaked, you cannot change your face
- **False Acceptance Rate (FAR) vs False Rejection Rate (FRR)** — tuning the matching threshold is a core security trade-off
- **Privacy regulations** — biometric data is classified as sensitive personal data under GDPR and India's DPDP Act

This project explores these trade-offs in a controlled, educational environment.

---

## Roadmap

- [x] Core enrolment and verification pipeline
- [x] Real-time camera integration
- [ ] Encrypted storage backend (SQLite + AES)
- [ ] Liveness detection (blink-based EAR)
- [ ] CLI interface for non-notebook usage
- [ ] Docker containerisation
- [ ] REST API wrapper for integration into larger auth systems

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you'd like to change.

---

## Author

**Bhupendra Singh**
[GitHub](https://github.com/pharaoh77731)

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements

- [OpenCV](https://opencv.org/) — Computer vision library
- [face_recognition](https://pypi.org/project/face-recognition/) — Facial analysis built on dlib
- [NumPy](https://numpy.org/) — Numerical computing
- [Pandas](https://pandas.pydata.org/) — Data analysis
- [Matplotlib](https://matplotlib.org/) — Data visualisation
