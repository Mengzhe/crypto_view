# https://stribny.name/blog/fastapi-asyncalchemy/

import asyncio
import random

import websockets
import json

from typing import *
# import yfinance
from fastapi import FastAPI, Request, Depends, BackgroundTasks, WebSocket
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.base import init_models, get_session, async_session
from db.models import Record
import db.service

import datetime

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://localhost",
    "http://localhost:8000"
    "http://localhost:8080",
    "http://localhost:63342"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

queue = asyncio.Queue(maxsize=10)
ws_buffer = asyncio.Queue(maxsize=10)

class PriceSchema(BaseModel):
    LASTUPDATE: int
    MARKET: str
    FROMSYMBOL: str
    TOSYMBOL: str
    PRICE: float
    MEDIAN: Optional[float] = None
    TIMESTAMP: datetime.datetime

class PriceChartSchema(BaseModel):
    value: float
    time: int


delta = datetime.timedelta(hours=4) ## timezone difference

## https://min-api.cryptocompare.com/documentation/websockets?key=Channels&cat=AggregateIndex
async def cryptocompare():
    # this is where you paste your api key
    api_key = "this is where you paste your api key"
    url = "wss://streamer.cryptocompare.com/v2?api_key=" + api_key
    async with websockets.connect(url) as websocket:
        await websocket.send(json.dumps({
            "action": "SubAdd",
            "subs": ["5~CCCAGG~BTC~USD"],
        }))
        while True:
            try:
                data = await websocket.recv()
            except websockets.ConnectionClosed:
                break

            data = json.loads(data)
            ## prcess data
            processed_data = {}
            processed_data['MARKET'] = data.get('MARKET', None)
            processed_data['FROMSYMBOL'] = data.get('FROMSYMBOL', None)
            processed_data['TOSYMBOL'] = data.get('TOSYMBOL', None)
            processed_data['PRICE'] = data.get('PRICE', None)
            processed_data['MEDIAN'] = data.get('MEDIAN', None)
            processed_data['LASTUPDATE'] = data.get('LASTUPDATE', None)
            processed_data['TIMESTAMP'] = datetime.datetime.now()

            # print(processed_data)
            if processed_data['PRICE'] is not None:
                await queue.put(processed_data)



async def consume_queue():
    while True:
        data: Dict = await queue.get()
        # await add_to_database(data)
        asyncio.create_task(add_to_database(data))
        if ws_buffer.full():
            ws_buffer.get_nowait()
        await ws_buffer.put(data)

async def add_to_database(data: Dict):
    async with async_session() as session:
        new_record = Record(**data)
        session.add(new_record)

        # simluate I/O latency
        await asyncio.sleep(random.randrange(4))

        await session.commit()
        print("ADD",
              new_record.MARKET,
              new_record.FROMSYMBOL,
              new_record.TOSYMBOL,
              new_record.PRICE,
              new_record.MEDIAN,
              new_record.LASTUPDATE,
              new_record.TIMESTAMP
              )


@app.on_event("startup")
async def startup_event():
    # initilization: database table
    await init_models()
    print("Database initilization is done. ")

    # initilization: download data
    task_crypto_download = asyncio.create_task(cryptocompare())
    # initilization: save data to database
    asyncio.create_task(consume_queue())


@app.get('/')
async def index(request: Request):
    # return {"hello": "world!"}
    return templates.TemplateResponse("streaming_chart.html",
                                      context={"request": request})

@app.post("/add_record_manually/")
async def add_record_manually(priceRecord: PriceSchema, session: AsyncSession = Depends(get_session)):
    await db.service.add_record(session, dict(priceRecord))

@app.get("/get_top_k_price_records/", response_model=List[PriceSchema])
async def get_top_k_price_records(k: int = 5, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Record).order_by(Record.PRICE.desc()).limit(k))
    result = result.scalars().all()

    # transform to PriceSchema
    results_price = []
    for record in result:
        price_record = PriceSchema(FROMSYMBOL=record.FROMSYMBOL,
                                   TOSYMBOL=record.TOSYMBOL,
                                   PRICE=record.PRICE,
                                   MEDIAN=record.MEDIAN,
                                   LASTUPDATE=record.LASTUPDATE,
                                   MARKET=record.MARKET,
                                   TIMESTAMP=record.TIMESTAMP)
        results_price.append(price_record)

    return results_price

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # print(ws_buffer)
            data: Dict = await ws_buffer.get()
            data['TIMESTAMP_UNIX'] = (data['TIMESTAMP']-delta).timestamp()
            data['TIMESTAMP'] = str(data['TIMESTAMP'])
            await websocket.send_json(data)
            await asyncio.sleep(0.5)
    except Exception:
        pass

    finally:
        await websocket.close()


@app.get("/history/", response_model=List[PriceChartSchema])
async def history(request: Request, session: AsyncSession = Depends(get_session)):
    # rename columns to satisfy the lightwight chart.js
    query_res = await session.execute(select(Record.TIMESTAMP.label("time"),
                                           Record.PRICE.label("value"))\
                                    .order_by(Record.TIMESTAMP))
    query_res = query_res.all()
    # print(query_res)
    res= []
    for dt, price in query_res:
        # res.append([str(dt), round(float(price), 2)])
        new_price = PriceChartSchema(value=round(float(price), 2),
                                     # time=dt.strftime("%Y-%m-%d %H:%M:%S")
                                     time=(dt-delta).timestamp()
                                     )
        # print(new_price)
        if len(res)>0 and new_price.time==res[-1].time:
            continue
        res.append(new_price)
    res.sort(key = lambda x: x.time)
    return res

@app.get("/get_history/")
async def get_history(request: Request):
    return templates.TemplateResponse("history.html",
                                      context={"request": request})