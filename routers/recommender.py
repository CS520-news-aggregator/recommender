from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from models.recommendation import Recommendation
import os
import requests

recommender_router = APIRouter(prefix="/recommender")


@recommender_router.get("/get-recommendations")
async def get_recommendations(_: Request, user_id: str, limit: int):
    print(f"Received request for recommendations for user: {user_id}")
    if (
        user_recommendations := get_db_data(
            "recommendation/get-recommendations", {"user_id": user_id}
        )
    ) is None:
        raise HTTPException(status_code=404, detail="Recommendations not found")

    recommendations = [
        Recommendation(**rec) for rec in user_recommendations["recommendations"]
    ]

    user_posts = []

    for rec in recommendations:
        for post in rec.post_recommendations:
            post_id = post.post_id
            if post_json := get_db_data("annotator/get-post", {"post_id": post_id}):
                user_posts.append(post_json["post"])

        if len(user_posts) >= limit:
            break

    # FIXME: for now, put random media and date
    for post in user_posts:
        post["media"] = (
            "https://t3.ftcdn.net/jpg/05/82/67/96/360_F_582679641_zCnWSvan9oScBHyWzfirpD4MKGp0kylJ.jpg"
        )
        post["date"] = get_cur_date()

    return {
        "message": "Recommendation sent",
        "list_recommendations": list(map(change_db_id_to_str, user_posts)),
    }


def get_user_info(user_id: str) -> dict | None:
    return get_db_data("user/get-user", {"user_id": user_id})


def get_db_data(endpoint: str, params: dict):
    DB_HOST = os.getenv("DB_HOST", "localhost")
    db_url = f"http://{DB_HOST}:8000/{endpoint}"

    encountered_error = False

    try:
        response = requests.get(db_url, params=params, timeout=30)
    except requests.exceptions.RequestException:
        print(f"Could not get data from database service due to timeout")
        encountered_error = True
    else:
        if response.status_code != 200:
            print(f"Received status code {response.status_code} from database service")
            encountered_error = True

    return response.json() if not encountered_error else None


def change_db_id_to_str(data):
    if data:
        data["id"] = str(data["_id"])
    return data


def get_cur_date():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
