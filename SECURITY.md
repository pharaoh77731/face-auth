# Security Analysis — Face Authentication System

This document analyses the security properties of the face authentication system from a threat modelling perspective. It identifies the attack surface, known vulnerabilities, and practical mitigations — framing the project as a study in biometric security rather than a production deployment.

---

## Threat Model

### Assets
- **Enrolled face encodings** (stored in CSV database)
- **Access control decision** (grant / deny)
- **Webcam input stream** (the trust boundary for identity claims)

### Threat Actors
| Actor | Capability | Goal |
|---|---|---|
| Unenrolled attacker | Physical access to device | Bypass authentication |
| Insider threat | Access to CSV database | Extract or manipulate encodings |
| Remote attacker | Network access (if deployed as service) | Intercept or replay session |

### Trust Boundaries
```
[Physical World] ──webcam──▶ [Application] ──read/write──▶ [CSV Store]
                              (trust boundary)               (trust boundary)
```

---

## Known Vulnerabilities

### 1. Photo / Video Spoofing (Presentation Attack)
**Severity: High**

The system has no liveness detection. An attacker with a photograph of an enrolled user can present it to the webcam and potentially obtain a match within the tolerance threshold.

**Why it works:** The face encoding pipeline processes static pixel data. It cannot distinguish between a live face and a printed or displayed image of that face.

**Mitigation:**
- Add liveness detection using blink detection (facial landmark tracking via dlib), or
- Require depth data (IR camera / 3D sensor, as used in Apple Face ID)
- Challenge-response: prompt the user to perform a random action (turn head, smile)

---

### 2. Threshold Tuning — FAR vs. FRR Tradeoff
**Severity: Medium (design consideration)**

The tolerance threshold (`default: 0.6`) directly controls the security-usability balance:

| Threshold | False Acceptance Rate (FAR) | False Rejection Rate (FRR) | Security Level |
|---|---|---|---|
| 0.4 | Very Low | High | Strict |
| 0.5 | Low | Medium | Balanced-Secure |
| **0.6** | **Medium** | **Low** | **Default** |
| 0.7 | High | Very Low | Permissive |

A threshold of `0.6` is suitable for convenience applications (attendance). For access control to sensitive systems, `0.45–0.5` is recommended.

**Key insight:** FAR is a security metric (how often an impostor gets through). FRR is a usability metric (how often a legitimate user is locked out). These cannot both be minimised simultaneously — this is the core design tradeoff in any authentication system.

---

### 3. Plaintext Encoding Storage
**Severity: Medium**

Face encodings are stored in a CSV file without encryption. While encodings are not directly reversible to the original face image, they are sensitive biometric data.

**Risk:** An attacker with file system access can:
- Exfiltrate all enrolled face encodings
- Substitute encodings (enrol themselves as another user)
- Perform offline brute-force with synthetic encodings

**Mitigation:**
- Encrypt the CSV at rest using AES-256 (e.g. via `cryptography` library)
- Store only a salted hash of encodings, not raw vectors
- Use file system permissions to restrict read access

---

### 4. No Rate Limiting / Brute Force Protection
**Severity: Low–Medium**

There is no lockout mechanism after repeated failed authentication attempts. In an API-deployed version, this would allow an attacker to attempt authentication continuously with different face images.

**Mitigation:**
- Implement exponential backoff after N failed attempts
- Log all authentication events (success + failure) with timestamps
- Alert on anomalous patterns (e.g. >10 failures in 60 seconds)

---

### 5. Single-Factor Authentication
**Severity: Design Limitation**

Face recognition alone is a single factor (something you are). It provides no protection if the biometric is compromised, and biometrics — unlike passwords — cannot be changed.

**Mitigation:**
- Use as one factor in a Multi-Factor Authentication (MFA) setup
- Pair with a PIN, hardware token, or knowledge factor for sensitive applications

---

## Security Controls in Place

| Control | Status | Notes |
|---|---|---|
| Input validation (face detection before encoding) | ✅ Implemented | Rejects frames with no detectable face |
| Configurable tolerance threshold | ✅ Implemented | Allows security tuning |
| MIT License (clear usage terms) | ✅ Present | |
| Liveness detection | ❌ Not implemented | Primary gap |
| Encoding encryption at rest | ❌ Not implemented | Recommended for any real deployment |
| Audit logging | ❌ Not implemented | Recommended |
| Rate limiting | ❌ Not implemented | Recommended for API deployment |

---

## Recommendations for Production Hardening

1. Integrate a liveness detection module (dlib facial landmarks or a dedicated anti-spoofing model)
2. Encrypt the face encoding database using AES-256-GCM
3. Log all auth events to a tamper-evident audit log
4. Enforce a strict threshold (`≤ 0.5`) for any security-critical use case
5. Deploy as one factor within an MFA framework, not standalone
6. Apply GDPR / biometric data handling compliance if used in any real system (consent, retention limits, right to erasure)

---

## References

- NIST SP 800-76-2 — Biometric Specifications for Personal Identity Verification
- ISO/IEC 30107-3 — Presentation Attack Detection
- OWASP Authentication Cheat Sheet — https://cheatsheats.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
- dlib face recognition model — http://dlib.net/face_recognition.py.html

---

*This analysis was conducted as part of a security-focused study of biometric authentication systems.*
