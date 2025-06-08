#  Xsolace – Transparent Disater Relief via XRP Token on XRP Ledger

> A transparent earthquake donation platform using RLUSD stablecoin on the XRP Ledger to deliver instant, auditable aid.


##  Problem

Earthquake victims often suffer from delayed and opaque relief distribution. Traditional donation systems include intermediaries, high fees, and lack public accountability.


##  Solution

**Xsolace** leverages the XRP Ledger and XRP Token to:
- Enable instant, low-cost donations to verified recipients and NGOs.
- Ensure transparency by recording all transactions on-chain.
- Tag donations with clear metadata (memo fields) for traceability.

---

##  How It Works

1. **Connect Wallet** (XRP-compatible wallet via XUMM or client wallet)
2. **Trust XRP Issuer** (trustline established)
3. **Donate XRP** – choose amount, add optional memo
4. **View Public Ledger** – every donation is verifiable via transaction hash


## 🔧 Tech Stack

| Layer        | Stack                          |
|--------------|--------------------------------|
| Frontend     | Android Development         |
| Backend/API  | Python,FastApi,Flask            |
| Blockchain   | XRP Ledger,XRP Token  |
| SDK          | `xrpl.py`                      |
| Design       | Canva (presentation)           |


##  XRPL Features Used

-  **Issued Currencies**: XRP Token
-  **Trustlines**: Donors trust XRP Token issuer
-  **Memo Fields**: Tag donations with purpose & metadata
-  **Low Fees**: Enables even micro-donations


##  How We Use the XRP Ledger

- Wallets interact with the **XRPL Testnet**
- Donations sent via **XRP (Issued Token)**
- **Transaction memo** includes:
  ```json
  {
    "donor": "0xabc...123",
    "region": "Turkey",
    "purpose": "Emergency Shelter"
  }

# XRPL API Server

This is a FastAPI-based server for the XRPL Project.

