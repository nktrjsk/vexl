# Description: Extensions that use LNURL usually have a few endpoints in views_lnurl.py.

from http import HTTPStatus

import shortuuid
from fastapi import APIRouter, Query, Request
from lnbits.core.services import create_invoice, pay_invoice
from loguru import logger

from .crud import get_vexl

#################################################
########### A very simple LNURLpay ##############
# https://github.com/lnurl/luds/blob/luds/06.md #
#################################################
#################################################

vexl_lnurl_router = APIRouter()


@vexl_lnurl_router.get(
    "/api/v1/lnurl/pay/{vexl_id}",
    status_code=HTTPStatus.OK,
    name="vexl.api_lnurl_pay",
)
async def api_lnurl_pay(
    request: Request,
    vexl_id: str,
):
    vexl = await get_vexl(vexl_id)
    if not vexl:
        return {"status": "ERROR", "reason": "No vexl found"}
    return {
        "callback": str(
            request.url_for(
                "vexl.api_lnurl_pay_callback", vexl_id=vexl_id
            )
        ),
        "maxSendable": vexl.lnurlpayamount * 1000,
        "minSendable": vexl.lnurlpayamount * 1000,
        "metadata": '[["text/plain", "' + vexl.name + '"]]',
        "tag": "payRequest",
    }


@vexl_lnurl_router.get(
    "/api/v1/lnurl/paycb/{vexl_id}",
    status_code=HTTPStatus.OK,
    name="vexl.api_lnurl_pay_callback",
)
async def api_lnurl_pay_cb(
    request: Request,
    vexl_id: str,
    amount: int = Query(...),
):
    vexl = await get_vexl(vexl_id)
    logger.debug(vexl)
    if not vexl:
        return {"status": "ERROR", "reason": "No vexl found"}

    payment = await create_invoice(
        wallet_id=vexl.wallet,
        amount=int(amount / 1000),
        memo=vexl.name,
        unhashed_description=f'[["text/plain", "{vexl.name}"]]'.encode(),
        extra={
            "tag": "vexl",
            "vexlId": vexl_id,
            "extra": request.query_params.get("amount"),
        },
    )
    return {
        "pr": payment.bolt11,
        "routes": [],
        "successAction": {"tag": "message", "message": f"Paid {vexl.name}"},
    }


#################################################
######## A very simple LNURLwithdraw ############
# https://github.com/lnurl/luds/blob/luds/03.md #
#################################################
## withdraw is unlimited, look at withdraw ext ##
## for more advanced withdraw options          ##
#################################################


@vexl_lnurl_router.get(
    "/api/v1/lnurl/withdraw/{vexl_id}",
    status_code=HTTPStatus.OK,
    name="vexl.api_lnurl_withdraw",
)
async def api_lnurl_withdraw(
    request: Request,
    vexl_id: str,
):
    vexl = await get_vexl(vexl_id)
    if not vexl:
        return {"status": "ERROR", "reason": "No vexl found"}
    k1 = shortuuid.uuid(name=vexl.id)
    return {
        "tag": "withdrawRequest",
        "callback": str(
            request.url_for(
                "vexl.api_lnurl_withdraw_callback", vexl_id=vexl_id
            )
        ),
        "k1": k1,
        "defaultDescription": vexl.name,
        "maxWithdrawable": vexl.lnurlwithdrawamount * 1000,
        "minWithdrawable": vexl.lnurlwithdrawamount * 1000,
    }


@vexl_lnurl_router.get(
    "/api/v1/lnurl/withdrawcb/{vexl_id}",
    status_code=HTTPStatus.OK,
    name="vexl.api_lnurl_withdraw_callback",
)
async def api_lnurl_withdraw_cb(
    vexl_id: str,
    pr: str | None = None,
    k1: str | None = None,
):
    assert k1, "k1 is required"
    assert pr, "pr is required"
    vexl = await get_vexl(vexl_id)
    if not vexl:
        return {"status": "ERROR", "reason": "No vexl found"}

    k1_check = shortuuid.uuid(name=vexl.id)
    if k1_check != k1:
        return {"status": "ERROR", "reason": "Wrong k1 check provided"}

    await pay_invoice(
        wallet_id=vexl.wallet,
        payment_request=pr,
        max_sat=int(vexl.lnurlwithdrawamount * 1000),
        extra={
            "tag": "vexl",
            "vexlId": vexl_id,
            "lnurlwithdraw": True,
        },
    )
    return {"status": "OK"}
