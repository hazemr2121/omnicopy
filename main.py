from datetime import datetime, timezone
from typing import Annotated, Generic, Optional, TypeVar

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Field, Session, SQLModel, create_engine, select

T = TypeVar("T")
class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )


class CampaignCreate(SQLModel):
    name: str
    due_date: datetime | None = None


class CampaignUpdate(SQLModel):
    name: str | None = None
    due_date: datetime | None = None

class PaginatedResponse(BaseModel, Generic[T]):
    data: T
    count: int
    next: str | None = None
    prev: str | None = None

sqlite_file_name = "database.db"
sql_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sql_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(Campaign)).first():
            session.add_all(
                [
                    Campaign(name="Summer Launch", due_date=datetime.now(timezone.utc)),
                    Campaign(name="Black Friday", due_date=datetime.now(timezone.utc)),
                ]
            )
            session.commit()
    yield


app = FastAPI(root_path="/api/v1", lifespan=lifespan)




class Response(BaseModel, Generic[T]):
    data: T


@app.get("/")
async def root():
    return {"message": "hello world!"}


@app.get("/campaigns", response_model=Response[list[Campaign]])
async def read_campaigns(request: Request ,session: SessionDep, page: int = Query(1, ge=1), page_size = Query(20, ge=1)):
    limit = page_size
    offset = (page-1) * limit
    data = session.exec(select(Campaign).order_by(Campaign.campaign_id).offset(offset).limit(limit)).all()
    total = session.exec(select(func.count()).select_from(Campaign)).one()
    base_url = str(request.url).split('?')[0]
    if offset + limit < total:
        next_url = f"{base_url}?page={page+1}&page_size{limit}"
    else:
        next_url = None

    if page > 1:
        prev_url = f"{base_url}?page={page-1}&page_size{limit}"
    else:
        prev_url = None


    return {
        "count": total,
        "next": next_url,
        "prev": prev_url,
        "data": data,

        }


@app.get("/campaigns/{id}", response_model=Response[Campaign])
async def read_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"data": data}


@app.post("/campaigns", status_code=201, response_model=Response[Campaign])
async def create_campaign(campaign: CampaignCreate, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return {"data": db_campaign}


@app.put("/campaigns/{id}", response_model=Response[Campaign])
async def update_campaign(id: int, campaign: CampaignUpdate, session: SessionDep):
    db_campaign = session.get(Campaign, id)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db_campaign.sqlmodel_update(campaign.model_dump(exclude_unset=True))
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return {"data": db_campaign}


@app.delete("/campaigns/{id}", status_code=204)
async def delete_campaign(id: int, session: SessionDep):
    db_campaign = session.get(Campaign, id)
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    session.delete(db_campaign)
    session.commit()