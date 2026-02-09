# Description: This file contains the CRUD operations for talking to the database.


from lnbits.db import Database
from lnbits.helpers import urlsafe_short_hash

from .models import CreatevexlData, vexl

db = Database("ext_vexl")


async def create_vexl(data: CreatevexlData) -> vexl:
    data.id = urlsafe_short_hash()
    await db.insert("vexl.maintable", data)
    return vexl(**data.dict())


async def get_vexl(vexl_id: str) -> vexl | None:
    return await db.fetchone(
        "SELECT * FROM vexl.maintable WHERE id = :id",
        {"id": vexl_id},
        vexl,
    )


async def get_vexls(wallet_ids: str | list[str]) -> list[vexl]:
    if isinstance(wallet_ids, str):
        wallet_ids = [wallet_ids]
    q = ",".join([f"'{w}'" for w in wallet_ids])
    return await db.fetchall(
        f"SELECT * FROM vexl.maintable WHERE wallet IN ({q}) ORDER BY id",
        model=vexl,
    )


async def update_vexl(data: CreatevexlData) -> vexl:
    await db.update("vexl.maintable", data)
    return vexl(**data.dict())


async def delete_vexl(vexl_id: str) -> None:
    await db.execute(
        "DELETE FROM vexl.maintable WHERE id = :id", {"id": vexl_id}
    )
