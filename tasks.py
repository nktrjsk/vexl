import asyncio

from lnbits.core.models import Payment
from lnbits.core.services import websocket_updater
from lnbits.tasks import register_invoice_listener

from .crud import get_vexl, update_vexl
from .models import CreatevexlData

#######################################
########## RUN YOUR TASKS HERE ########
#######################################

# The usual task is to listen to invoices related to this extension


async def wait_for_paid_invoices():
    invoice_queue = asyncio.Queue()
    register_invoice_listener(invoice_queue, "ext_vexl")
    while True:
        payment = await invoice_queue.get()
        await on_invoice_paid(payment)


# Do somethhing when an invoice related top this extension is paid


async def on_invoice_paid(payment: Payment) -> None:
    if payment.extra.get("tag") != "vexl":
        return

    vexl_id = payment.extra.get("vexlId")
    assert vexl_id, "vexlId not set in invoice"
    vexl = await get_vexl(vexl_id)
    assert vexl, "vexl does not exist"

    # update something in the db
    if payment.extra.get("lnurlwithdraw"):
        total = vexl.total - payment.amount
    else:
        total = vexl.total + payment.amount

    vexl.total = total
    await update_vexl(CreatevexlData(**vexl.dict()))

    # here we could send some data to a websocket on
    # wss://<your-lnbits>/api/v1/ws/<vexl_id> and then listen to it on

    some_payment_data = {
        "name": vexl.name,
        "amount": payment.amount,
        "fee": payment.fee,
        "checking_id": payment.checking_id,
    }

    await websocket_updater(vexl_id, str(some_payment_data))
