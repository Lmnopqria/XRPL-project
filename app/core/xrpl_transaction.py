import xrpl
from xrpl.asyncio.transaction import submit_and_wait
from xrpl.asyncio.clients import AsyncJsonRpcClient
from sqlalchemy.orm import Session
from app.models.record import Record, TransactionType
from app.models.user import User as UserModel


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
    try:
        # Send XRP
        payment_tx = xrpl.models.Payment(
            account=central_wallet.address,
            amount=amount,
            destination=receiver_address,
        )
        await submit_and_wait(payment_tx, client, central_wallet)
        
        # Update user's balance and record the transaction
        user = db.query(UserModel).filter(UserModel.user_id == int(user_id)).first()
        if user:
            user.balance += int(amount)
            db.commit()
        record = Record(
            user_id=int(user_id),
            amount=int(amount),
            type=TransactionType.RECEIVED.value
        )
        db.add(record)
        db.commit()
        print(f"[Success] Successfully sent {amount} XRP to user {user_id}.")
        return True
    except Exception as e:
        print(f"[Failure] Failed to send XRP to user {user_id}: {str(e)}")
        return False 