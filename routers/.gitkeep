from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from models.subscribe import Message
import requests


subscriber_router = APIRouter(prefix="/subscriber")


@subscriber_router.post("/update")
async def update_from_publisher(_: Request, message: Message = Body(...)):
    print(f"Received message: {message}")
    return {"message": "Message received"}
