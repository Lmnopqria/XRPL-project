import xrpl
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.asyncio.clients import AsyncJsonRpcClient
from sqlalchemy.orm import Session
from app.models.record import Record, TransactionType
from app.models.user import User as UserModel
from app.models.donation_summary import DonationSummary
from app.models.transaction_record import TransactionRecord, TransactionStatus

async def send_xrp_to_user(
    central_wallet: xrpl.wallet.Wallet,
    receiver_address: str,
    amount: str,
    user_id: str,
    client: AsyncJsonRpcClient,
    db: Session
):
    """
    Send XRP from central wallet to a user and record the transaction
    
    Args:
        central_wallet: Central wallet to send XRP from
        receiver_address: User's wallet address to receive XRP
        amount: Amount of XRP to send
        user_id: Receiver's user ID
        client: XRPL client instance
        db: Database session
    """
 
    # Submit transaction with retry logic

    try:
        # Send XRP with explicit sequence number
        payment_tx = xrpl.models.Payment(
            account=central_wallet.address,
            amount=amount,
            destination=receiver_address
        )
        result = await submit_and_wait(payment_tx, client, central_wallet)
        tx_hash = result.result.get("hash") if hasattr(result, "result") else None

        # Update user's balance
        user = db.query(UserModel).filter(UserModel.user_id == int(user_id)).first()
        if user:
            user.balance += int(amount)

        # Record the transaction
        record = Record(
            user_id=int(user_id),
            amount=int(amount),
            type=TransactionType.RECEIVED.value
        )
        db.add(record)

        # 트랜잭션 기록 추가
        tx_record = TransactionRecord(
            user_id=int(user_id),
            from_wallet_address=central_wallet.address,
            to_wallet_address=receiver_address,
            tx_hash=tx_hash or "",
            amount=int(amount),
            status=TransactionStatus.SUCCESS.value
        )
        db.add(tx_record)

        # Update the total pool
        summary = db.query(DonationSummary).filter(DonationSummary.id == 1).first()
        if not summary:
            raise Exception(status_code=500, detail="Donation summary record does not exist.")
        if summary.total - int(amount) < 0:
            raise Exception(status_code=500, detail="amount can't be negative")
        summary.total -= int(amount)

        db.commit()
        print(f"[Success] Successfully sent {amount} XRP to user {user_id}.")
        return True
    except Exception as e:
        # 실패 시에는 rollback 먼저!
        db.rollback()
        # 실패 기록 추가
        tx_record = TransactionRecord(
            user_id=int(user_id),
            from_wallet_address=central_wallet.address,
            to_wallet_address=receiver_address,
            tx_hash="",
            amount=int(amount),
            status=TransactionStatus.FAILED.value
        )
        db.add(tx_record)
        db.commit()
        print(f"[Failure] Failed to send XRP to user {user_id}: {str(e)}")
        return False 