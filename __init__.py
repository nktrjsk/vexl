import asyncio

from fastapi import APIRouter
from lnbits.tasks import create_permanent_unique_task
from loguru import logger

from .crud import db
from .tasks import wait_for_paid_invoices
from .views import vexl_generic_router
from .views_api import vexl_api_router
from .views_lnurl import vexl_lnurl_router

logger.debug(
    "This logged message is from vexl/__init__.py, you can debug in your "
    "extension using 'import logger from loguru' and 'logger.debug(<thing-to-log>)'."
)


vexl_ext: APIRouter = APIRouter(prefix="/vexl", tags=["vexl"])
vexl_ext.include_router(vexl_generic_router)
vexl_ext.include_router(vexl_api_router)
vexl_ext.include_router(vexl_lnurl_router)

vexl_static_files = [
    {
        "path": "/vexl/static",
        "name": "vexl_static",
    }
]

scheduled_tasks: list[asyncio.Task] = []


def vexl_stop():
    for task in scheduled_tasks:
        try:
            task.cancel()
        except Exception as ex:
            logger.warning(ex)


def vexl_start():
    task = create_permanent_unique_task("ext_vexl", wait_for_paid_invoices)
    scheduled_tasks.append(task)


__all__ = [
    "db",
    "vexl_ext",
    "vexl_start",
    "vexl_static_files",
    "vexl_stop",
]
