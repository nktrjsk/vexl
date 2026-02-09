# Description: Add your page endpoints here.

from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from lnbits.core.models import User
from lnbits.decorators import check_user_exists
from lnbits.helpers import template_renderer
from lnbits.settings import settings

from .crud import get_vexl
from .helpers import lnurler

vexl_generic_router = APIRouter()


def vexl_renderer():
    return template_renderer(["vexl/templates"])


#######################################
##### ADD YOUR PAGE ENDPOINTS HERE ####
#######################################


# Backend admin page


@vexl_generic_router.get("/", response_class=HTMLResponse)
async def index(req: Request, user: User = Depends(check_user_exists)):
    return vexl_renderer().TemplateResponse(
        "vexl/index.html", {"request": req, "user": user.json()}
    )


# Frontend shareable page


@vexl_generic_router.get("/{vexl_id}")
async def vexl(req: Request, vexl_id):
    myex = await get_vexl(vexl_id)
    if not myex:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="vexl does not exist."
        )
    return vexl_renderer().TemplateResponse(
        "vexl/vexl.html",
        {
            "request": req,
            "vexl_id": vexl_id,
            "lnurlpay": lnurler(myex.id, "vexl.api_lnurl_pay", req),
            "web_manifest": f"/vexl/manifest/{vexl_id}.webmanifest",
        },
    )


# Manifest for public page, customise or remove manifest completely


@vexl_generic_router.get("/manifest/{vexl_id}.webmanifest")
async def manifest(vexl_id: str):
    vexl = await get_vexl(vexl_id)
    if not vexl:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="vexl does not exist."
        )

    return {
        "short_name": settings.lnbits_site_title,
        "name": vexl.name + " - " + settings.lnbits_site_title,
        "icons": [
            {
                "src": (
                    settings.lnbits_custom_logo
                    if settings.lnbits_custom_logo
                    else "https://cdn.jsdelivr.net/gh/lnbits/lnbits@0.3.0/docs/logos/lnbits.png"
                ),
                "type": "image/png",
                "sizes": "900x900",
            }
        ],
        "start_url": "/vexl/" + vexl_id,
        "background_color": "#1F2234",
        "description": "Minimal extension to build on",
        "display": "standalone",
        "scope": "/vexl/" + vexl_id,
        "theme_color": "#1F2234",
        "shortcuts": [
            {
                "name": vexl.name + " - " + settings.lnbits_site_title,
                "short_name": vexl.name,
                "description": vexl.name + " - " + settings.lnbits_site_title,
                "url": "/vexl/" + vexl_id,
            }
        ],
    }
