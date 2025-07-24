# TASK SPECIFICATION

## Task Overview
Create two XRP escrow-related functions as part of a fund distribution system.

---

## 🔹 Function 1: `make_escrow(from_address, secret_key, amount, cancel_after)`
**Description:**  
Creates a new conditional escrow using a preimage-based hash condition and `cancel_after` time.

**Parameters:**
- `from_address` (str): Sender’s XRP wallet address  
- `secret_key` (str): Preimage used to generate the hash condition  
- `amount` (float): Amount in XRP to escrow  
- `cancel_after` (int): UNIX timestamp after which the escrow can be cancelled  

**Returns:**
- `tx_sequence` (int): Sequence number of the `EscrowCreate` transaction

**Note:**  
The `to_address` (receiver wallet) is fixed and defined inside the function.


---

## 🔹 Function 2: `release_escrow(tx_sequence, from_address, secret_key)`
**Description:**  
Releases an existing escrow using the original preimage (`secret_key`).

**Parameters:**
- `tx_sequence` (int): Sequence number of the original escrow transaction  
- `from_address` (str): Escrow creator's wallet address  
- `secret_key` (str): Preimage to fulfill the escrow condition  

**Returns:**
- Result indicating whether the release succeeded or not

---

## 🔁 Process Flow (Pseudo Code)

```python
@post("/donate"):
    secret_key = generate_random_preimage()
    tx_sequence = make_escrow(from_address, secret_key, amount, cancel_after)
    save_in_db(secret_key, tx_sequence, amount, from_address)

@post("/distribute"):
    escrow_list = get_escrows_from_db()
    for escrow in escrow_list:
        release_escrow(escrow.tx_sequence, escrow.from_address, escrow.secret_key)
    distribute_fund_from_central_wallet()