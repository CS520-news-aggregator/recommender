from typing import List
from pydantic import BaseModel


class Source(BaseModel):
    _id: str
    title: str
    link: str
    media: str
    author: str
    date: str


class Post(BaseModel):
    id: str
    source_ids: List[str]
    topics: List[str]

    upvotes: int
    downvotes: int