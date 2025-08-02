from datetime import datetime

def make_escrow(from_address, secret_key, amount, cancel_after):
    return "sample_tx_sequence" + str(datetime.now())

async def release_escrow(escrow_id, tx_sequence, from_address, secret_key):
    return (escrow_id, True)