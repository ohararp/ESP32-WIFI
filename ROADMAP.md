# ESP32 Health Monitor - Development Roadmap

## Project Overview

Medical device for periodic health sensor data collection with cloud upload.
Target: FDA approval pathway.

---

## Hardware Platform

- **Prototype:** YD-ESP32-S3 N16R8
- **Production:** TBD (ESP32-S3 based, with secure element consideration)
- **Sensors:** 16 channels, 32-bit values
- **Storage:** SPI Flash/EEPROM for local buffering
- **Sampling:** 60 Hz bursts, configurable intervals

---

## Data Specifications

| Parameter | Value |
|-----------|-------|
| Sensors | 16 × 32-bit |
| Sample rate | 60 Hz during burst |
| Burst duration | ~1 second (60 samples) |
| Burst frequency | Every 1-60 minutes (configurable) |
| Data per burst | ~3.75 KB |
| Upload frequency | 1-2× daily |
| Daily data (per device) | ~5.4 MB |

### Scale Projections

| Phase | Devices | Daily Data | Monthly Data |
|-------|---------|------------|--------------|
| Pilot | 10 | 54 MB | 1.6 GB |
| Trial | 25 | 135 MB | 4 GB |
| Scale | 100 | 540 MB | 16 GB |
| Production | 1000+ | 5.4 GB | 162 GB |

---

## Development Phases

### Phase 1: CircuitPython Prototype ✓ IN PROGRESS
**Goal:** Prove concept, validate sensors, iterate quickly

- [x] WiFi connectivity with robust reconnection
- [x] LED status feedback
- [x] Settings via settings.toml
- [ ] SPI sensor interface
- [ ] Local data buffering (SPI Flash)
- [ ] HTTPS upload to test endpoint
- [ ] Basic encryption (AES)

**Deliverable:** Working prototype for stakeholder demos

---

### Phase 2: Cloud Infrastructure
**Goal:** Production-ready backend for data collection

#### Database Architecture
- **Engine:** PostgreSQL + TimescaleDB
- **Hosting:** AWS RDS or Azure (HIPAA-eligible, BAA required)

#### Schema
```sql
-- Device registry
CREATE TABLE devices (
    device_id       UUID PRIMARY KEY,
    device_name     TEXT,
    user_id         UUID,
    location        TEXT,
    firmware_ver    TEXT,
    provisioned_at  TIMESTAMPTZ,
    last_seen       TIMESTAMPTZ
);

-- Sensor readings (TimescaleDB hypertable)
CREATE TABLE readings (
    time            TIMESTAMPTZ NOT NULL,
    device_id       UUID NOT NULL,
    batch_id        UUID NOT NULL,
    sample_index    INT,
    s01 INT, s02 INT, s03 INT, s04 INT,
    s05 INT, s06 INT, s07 INT, s08 INT,
    s09 INT, s10 INT, s11 INT, s12 INT,
    s13 INT, s14 INT, s15 INT, s16 INT,
    signature       TEXT  -- HMAC for integrity
);
SELECT create_hypertable('readings', 'time');

-- Audit log (FDA 21 CFR Part 11)
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ DEFAULT NOW(),
    actor           TEXT NOT NULL,  -- device_id, user_id, or system
    action          TEXT NOT NULL,
    resource        TEXT,
    details         JSONB,
    ip_address      INET
);
```

#### API Endpoints
```
POST /api/v1/upload          - Device data upload (mutual TLS)
GET  /api/v1/devices         - List devices (admin)
GET  /api/v1/readings        - Query readings (analyst)
GET  /api/v1/audit           - Audit log (compliance)
```

**Deliverable:** Secure API + database accepting device uploads

---

### Phase 3: ESP-IDF Production Firmware
**Goal:** FDA-ready firmware with security features

#### Why ESP-IDF (not CircuitPython) for Production

| Requirement | CircuitPython | ESP-IDF |
|-------------|---------------|---------|
| Secure boot | No | Yes |
| Flash encryption | No | AES-256-XTS |
| Hardware crypto | Limited | Full |
| Signed OTA | No | Yes |
| Deterministic timing | GC pauses | FreeRTOS |
| FDA audit trail | Harder | Easier |

#### Security Features to Implement
- [ ] Secure boot (verify firmware signature)
- [ ] Flash encryption (protect firmware/data)
- [ ] Per-device certificates (provisioned at manufacturing)
- [ ] Mutual TLS (device ↔ server authentication)
- [ ] AES-256 payload encryption
- [ ] HMAC-SHA256 data signing
- [ ] Signed OTA updates
- [ ] Tamper detection

#### Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    ESP-IDF Firmware                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Sensor  │  │ Storage │  │ Crypto  │  │  Cloud  │   │
│  │  Task   │  │  Task   │  │  Task   │  │  Task   │   │
│  │ (60Hz)  │  │ (Flash) │  │ (AES)   │  │ (HTTPS) │   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│       │            │            │            │         │
│       └────────────┴────────────┴────────────┘         │
│                         │                               │
│              ┌──────────┴──────────┐                   │
│              │    FreeRTOS Core    │                   │
│              └─────────────────────┘                   │
├─────────────────────────────────────────────────────────┤
│  Secure Boot │ Flash Encryption │ Hardware Crypto      │
└─────────────────────────────────────────────────────────┘
```

**Deliverable:** Production firmware with security features

---

### Phase 4: FDA Submission Preparation
**Goal:** Documentation and testing for regulatory submission

#### Required Documentation
- [ ] Software Requirements Specification (SRS)
- [ ] Software Design Specification (SDS)
- [ ] Cybersecurity Risk Assessment
- [ ] Threat Model (STRIDE)
- [ ] Security Architecture Document
- [ ] Software Bill of Materials (SBOM)
- [ ] Traceability Matrix
- [ ] Unit Test Reports
- [ ] Integration Test Reports
- [ ] Penetration Test Results

#### Compliance Requirements
- [ ] FDA 21 CFR Part 11 (electronic records)
- [ ] HIPAA (PHI protection)
- [ ] IEC 62304 (medical device software)
- [ ] FDA Cybersecurity Guidance (pre/post-market)

#### Testing
- [ ] Functional testing
- [ ] Security penetration testing
- [ ] Stress/load testing
- [ ] Failure mode testing
- [ ] Update/recovery testing

**Deliverable:** Complete Design History File (DHF)

---

### Phase 5: Manufacturing & Deployment
**Goal:** Scalable device provisioning and deployment

#### Device Provisioning Flow
```
1. Generate unique device_id (UUID)
2. Generate device certificate (signed by CA)
3. Generate encryption keys
4. Flash firmware with secure boot enabled
5. Write credentials to secure NVM
6. Register device in cloud database
7. Verify device can connect and upload
8. Package and ship
```

#### Infrastructure
- [ ] Certificate Authority (CA) setup
- [ ] Provisioning station software
- [ ] Device registration API
- [ ] Monitoring and alerting
- [ ] OTA update server

**Deliverable:** Manufacturing-ready provisioning process

---

## Security Architecture

### Encryption Layers

```
┌─────────────┐
│   ESP32     │
│             │
│  Sensor     │
│  Data       │
│     │       │
│     ▼       │
│  AES-256    │  ← Payload encryption (E2E)
│  Encrypt    │
│     │       │
│     ▼       │
│  HMAC-SHA   │  ← Integrity signature
│  Sign       │
│     │       │
└─────┼───────┘
      │
      │ TLS 1.3 (mutual auth)  ← Transport encryption
      │
      ▼
┌─────────────┐
│   Server    │
│             │
│  Verify     │  ← Check signature
│  signature  │
│     │       │
│     ▼       │
│  Store      │  ← Encrypted at rest
│  (encrypted)│
│             │
└─────────────┘
```

### Key Management

| Key Type | Storage | Provisioned |
|----------|---------|-------------|
| Device certificate | Secure NVM | Manufacturing |
| Device private key | Secure NVM | Manufacturing |
| AES encryption key | Secure NVM | Manufacturing |
| HMAC signing key | Secure NVM | Manufacturing |
| Server CA cert | Firmware | Build time |

---

## Technology Stack

### Device (Prototype)
- CircuitPython 10.x
- adafruit_requests
- aesio (encryption)

### Device (Production)
- ESP-IDF 5.x
- FreeRTOS
- mbedTLS (crypto)
- esp_http_client

### Backend
- PostgreSQL + TimescaleDB
- Python/FastAPI (API server)
- AWS/Azure (HIPAA-compliant hosting)

### Analytics
- Direct SQL access for data analysts
- Compatible with: Tableau, PowerBI, Metabase, Grafana

---

## Timeline (Estimated)

| Phase | Duration | Milestone |
|-------|----------|-----------|
| Phase 1: CircuitPython Prototype | 1-2 months | Working demo |
| Phase 2: Cloud Infrastructure | 1-2 months | API accepting uploads |
| Phase 3: ESP-IDF Firmware | 2-3 months | Secure production firmware |
| Phase 4: FDA Preparation | 3-6 months | Submission-ready documentation |
| Phase 5: Manufacturing | 1-2 months | Provisioning process |

*Note: Timeline estimates only - actual schedule depends on resources and regulatory feedback.*

---

## Open Questions

1. **Device classification** - Class I, II, or III? (affects regulatory pathway)
2. **Secure element** - Add hardware security module (ATECC608)?
3. **OTA strategy** - Required update frequency?
4. **Data retention** - How long to keep raw sensor data?
5. **Multi-region** - Single region or global deployment?

---

## References

- [FDA Cybersecurity Guidance](https://www.fda.gov/medical-devices/digital-health-center-excellence/cybersecurity)
- [ESP-IDF Security Guide](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/security/index.html)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [HIPAA Compliance](https://www.hhs.gov/hipaa/index.html)
- [21 CFR Part 11](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11)

---

## Repository

- **Code:** https://github.com/ohararp/ESP32-WIFI
- **Current Phase:** 1 (CircuitPython Prototype)
