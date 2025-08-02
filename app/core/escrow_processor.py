from sqlalchemy.orm import Session
from app.models.escrow_record import EscrowRecord, EscrowStatus


def process_escrow_results(db: Session, results):
    """
    Process escrow results and update their statuses in the database
    
    Args:
        db (Session): Database session
        results: List of (escrow_id, success) tuples from escrow operations
        
    Returns:
        tuple: (successful_count, total_escrows, released_sum)
    """
    successful_escrow_ids = []
    failed_escrow_ids = []
    released_sum = 0

    for result in results:
        escrow_id, success = result
        if success:
            successful_escrow_ids.append(escrow_id)
        else:
            failed_escrow_ids.append(escrow_id)

    # Batch update successful escrows
    if successful_escrow_ids:
        successful_escrows = db.query(EscrowRecord).filter(
            EscrowRecord.escrow_id.in_(successful_escrow_ids)
        ).all()
        released_sum = sum(escrow.amount for escrow in successful_escrows)

        db.query(EscrowRecord).filter(
            EscrowRecord.escrow_id.in_(successful_escrow_ids)
        ).update({"status": EscrowStatus.COMPLETED}, synchronize_session=False)

    # Batch update failed escrows
    if failed_escrow_ids:
        db.query(EscrowRecord).filter(
            EscrowRecord.escrow_id.in_(failed_escrow_ids)
        ).update({"status": EscrowStatus.FAILED}, synchronize_session=False)

    # Update remaining PROCESSING escrows to FAILED (timeout handling)
    db.query(EscrowRecord).filter(
        EscrowRecord.status == EscrowStatus.PROCESSING
    ).update({"status": EscrowStatus.FAILED}, synchronize_session=False)

    db.commit()

    successful_count = len(successful_escrow_ids)
    total_escrows = len(successful_escrow_ids) + len(failed_escrow_ids)
    return successful_count, total_escrows, released_sum 