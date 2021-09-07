from typing import *
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Record


async def add_record(session: AsyncSession, data: Dict):
    new_record = Record(**data)
    session.add(new_record)
    await session.commit()
    # print("add_record done")
    # return new_record

async def _get_highest_price(session: AsyncSession) -> list:
    result = await session.execute(select(Record).order_by(Record.PRICE.desc()).limit(5))
    return result.scalars().all()
