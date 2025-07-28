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
- `amount` (int): Amount in XRP to escrow  
- `cancel_after` (int): UNIX timestamp after which the escrow can be cancelled  

**Returns:**
- `tx_sequence` (int): Sequence number of the `EscrowCreate` transaction

**Note:**  
The `to_address` (receiver wallet) is fixed and defined inside the function.


---

## 🔹 Function 2: `release_escrow(escrow_id, tx_sequence, from_address, secret_key)`
**Description:**  
Releases an existing escrow using the original preimage (`secret_key`).

**Parameters:**
- `escrow_id` (int): Identifier of the escrow to release
- `tx_sequence` (int): Sequence number of the original escrow transaction  
- `from_address` (str): Escrow creator's wallet address  
- `secret_key` (str): Preimage to fulfill the escrow condition  

**Returns:**
- Tuple (escrow_id, success: bool)

---

## 🔁 Process Flow (Pseudo Code)

```python
@post("/donate"):
    secret_key = generate_random_preimage()
    tx_sequence = make_escrow(from_address, secret_key, amount, cancel_after)
    save_in_db(secret_key, tx_sequence, amount, from_address)

@post("/distribute"):
    central_wallet = get_central_wallet()
    affected_users = get_affected_users()
    background_tasks.add_task(process_distribution, ...)
    return {"message": "Background distribution started"}
 
async def process_distribution(central_wallet, affected_users, client, db):
    # 1. Retrieve related Escrow records
    escrows = get_escrows_for_users()

    # 2. Process Escrow releases in parallel
    escrow_tasks = []
    for escrow in escrows:
        task = release_escrow(escrow.tx_sequence, escrow.from_address, escrow.secret_key)
        escrow_tasks.append(task)
    escrow_results = await asyncio.gather(*escrow_tasks, return_exceptions=True)

    # 3. Check balance and calculate per-user payout
    total_balance = get_balance(central_wallet)
    per_user_amount = calculate_share(total_balance, len(affected_users))

    # 4. Send payments to beneficiaries in parallel
    send_tasks = []
    for user in affected_users:
        task = send_xrp_to_user(user, per_user_amount)
        send_tasks.append(task)
    send_results = await asyncio.gather(*send_tasks, return_exceptions=True)