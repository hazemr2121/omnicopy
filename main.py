from random import randint

from fastapi import FastAPI, HTTPException, Request, Response
from datetime import datetime
from typing import Any
app = FastAPI(root_path="/api/v1")

@app.get("/")
async def root():
    return {"message":"hello world!"}

data : Any = [
    {
        "campaign_id": 1,
        "name": "Summer Lunch",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
    {
        "campaign_id": 2,
        "name": "Black Friday",
        "due_date": datetime.now(),
        "created_at": datetime.now()
    },
]

"""
Compaigns
- compaign_id
- name
- due_date
- created_at
"""

@app.get("/campaigns")
async def read_campaigns():
    return{"campaigns": data}

@app.get("/campaigns/{id}")
async def read_campaign(id: int):
    for camp in data:
        if camp.get("campaign_id") == id:
            return {"campaign": camp}
    raise HTTPException(status_code=404)


@app.post("/campaigns", status_code=201)
async def create_campaign(body: dict[str, Any]):

    new = {
        "campaign_id": randint(100,1000),
        "name": body.get("name"),
        "due_date": body.get("due_date"),
        "created_at": datetime.now()
    }

    data.append(new)

    return{"campaign": new}


@app.put("campaigns/{id}")
async def update_campaign(id: int,body: dict[str, Any]):
    for index, camp in enumerate(data):
        if camp.get("campaign_id") == id:

            updated = {
                "campaign_id": id,
                "name": body.get("name"),
                "due_date": body.get("due_date"),
                "created_at": camp.get("created_at")
            }
            data[index] = updated
            return {"campaign": updated}

    raise HTTPException(status_code=404)


@app.delete("campaigns/{id}")
async def update_campaign(id: int):
    for index, camp in enumerate(data):
        if camp.get("campaign_id") == id:

            data.pop(index)            
            return Response(status_code=204)
    raise HTTPException(status_code=404)