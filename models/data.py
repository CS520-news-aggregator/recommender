from typing import List
from pydantic import BaseModel


class Post(BaseModel):
    _id: str
    title: str
    link: str
    media: str
    author: str
    date: str


class Annotation(BaseModel):
    post_ids: List[str]
    topics: List[str]
