# Description: This file contains the extensions API endpoints.

from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from lnbits.core.crud import get_user
from lnbits.core.models import WalletTypeInfo
from lnbits.core.services import create_invoice
from lnbits.decorators import require_admin_key, require_invoice_key
from starlette.exceptions import HTTPException

from .crud import (
    create_vexl,
    delete_vexl,
    get_vexl,
    get_vexls,
    update_vexl,
)
from .helpers import lnurler
from .models import CreatevexlData, CreatePayment, vexl

vexl_api_router = APIRouter()

# Note: we add the lnurl params to returns so the links
# are generated in the vexl model in models.py

## Get all the records belonging to the user


@vexl_api_router.get("/api/v1/myex")
async def api_vexls(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    wallet: WalletTypeInfo = Depends(require_invoice_key),
) -> list[vexl]:
    wallet_ids = [wallet.wallet.id]
    user = await get_user(wallet.wallet.user)
    wallet_ids = user.wallet_ids if user else []
    vexls = await get_vexls(wallet_ids)

    # Populate lnurlpay and lnurlwithdraw for each instance.
    # Without the lnurl stuff this wouldnt be needed.
    for myex in vexls:
        myex.lnurlpay = lnurler(myex.id, "vexl.api_lnurl_pay", req)
        myex.lnurlwithdraw = lnurler(myex.id, "vexl.api_lnurl_withdraw", req)

    return vexls


## Get a single record


@vexl_api_router.get(
    "/api/v1/myex/{vexl_id}",
    dependencies=[Depends(require_invoice_key)],
)
async def api_vexl(vexl_id: str, req: Request) -> vexl:
    myex = await get_vexl(vexl_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="vexl does not exist."
        )
    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "vexl.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "vexl.api_lnurl_withdraw", req)

    return myex


## Create a new record


@vexl_api_router.post("/api/v1/myex", status_code=HTTPStatus.CREATED)
async def api_vexl_create(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreatevexlData,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> vexl:
    myex = await create_vexl(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Withoutthe lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "vexl.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "vexl.api_lnurl_withdraw", req)

    return myex


## update a record


@vexl_api_router.put("/api/v1/myex/{vexl_id}")
async def api_vexl_update(
    req: Request,  # Withoutthe lnurl stuff this wouldnt be needed
    data: CreatevexlData,
    vexl_id: str,
    wallet: WalletTypeInfo = Depends(require_admin_key),
) -> vexl:
    myex = await get_vexl(vexl_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="vexl does not exist."
        )

    if wallet.wallet.id != myex.wallet:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your vexl."
        )

    for key, value in data.dict().items():
        setattr(myex, key, value)

    myex = await update_vexl(data)

    # Populate lnurlpay and lnurlwithdraw.
    # Without the lnurl stuff this wouldnt be needed.
    myex.lnurlpay = lnurler(myex.id, "vexl.api_lnurl_pay", req)
    myex.lnurlwithdraw = lnurler(myex.id, "vexl.api_lnurl_withdraw", req)

    return myex


## Delete a record


@vexl_api_router.delete("/api/v1/myex/{vexl_id}")
async def api_vexl_delete(
    vexl_id: str, wallet: WalletTypeInfo = Depends(require_admin_key)
):
    myex = await get_vexl(vexl_id)

    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="vexl does not exist."
        )

    if myex.wallet != wallet.wallet.id:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Not your vexl."
        )

    await delete_vexl(vexl_id)
    return


# ANY OTHER ENDPOINTS YOU NEED

## This endpoint creates a payment


@vexl_api_router.post("/api/v1/myex/payment", status_code=HTTPStatus.CREATED)
async def api_vexl_create_invoice(data: CreatePayment) -> dict:
    vexl = await get_vexl(data.vexl_id)

    if not vexl:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="vexl does not exist."
        )

    # we create a payment and add some tags,
    # so tasks.py can grab the payment once its paid

    payment = await create_invoice(
        wallet_id=vexl.wallet,
        amount=data.amount,
        memo=(
            f"{data.memo} to {vexl.name}" if data.memo else f"{vexl.name}"
        ),
        extra={
            "tag": "vexl",
            "amount": data.amount,
        },
    )

    return {"payment_hash": payment.payment_hash, "payment_request": payment.bolt11}
