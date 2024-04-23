from fastapi import APIRouter, Body, Request
from fastapi.encoders import jsonable_encoder
from models.source import Source
from models.post import Post
import os
import requests
from collections import Counter

recommender_router = APIRouter(prefix="/recommender")
POSTS_PULL_LIMIT = 10


@recommender_router.get("/get-recommendations")
async def get_recommendations(_: Request, user_id: str, limit: int):
    print(f"Received request for recommendations for user: {user_id}")

    list_posts = get_posts()

    if user := get_user_info(user_id) is None:
        return {
            "message": "Could not retrieve user data",
            "list_recommendations": [],
        }

    # user_prefs = Counter(user["preferences"])

    # post_matches = Counter()
    # for i in range(len(list_posts)):
    #     post, annotation = list_posts[i]
    #     annotation_counts = Counter(annotation)
    #     post_matches[post] = sum((user_prefs & annotation_counts).values())

    list_recommendations = [jsonable_encoder(post) for post in list_posts[:limit]]

    # FIXME: for now, put random title and summary and media
    for post in list_recommendations:
        post["title"] = "Random title"
        post["summary"] = "Random summary"
        post["media"] = (
            "https://t3.ftcdn.net/jpg/05/82/67/96/360_F_582679641_zCnWSvan9oScBHyWzfirpD4MKGp0kylJ.jpg"
        )

    return {
        "message": "Recommendation sent",
        "list_recommendations": list_recommendations,
    }


def get_user_info(user_id: str) -> dict | None:
    return get_db_data("user/get-user", {"user_id": user_id})


def get_posts() -> list[Post]:
    list_posts = list()

    if list_posts_json := get_db_data(
        "annotator/get-all-posts", {"limit": POSTS_PULL_LIMIT}
    ):
        for post_json in list_posts_json["list_posts"]:
            post = Post(**post_json)
            list_posts.append(post)

    return list_posts


def get_source(source_id: str) -> Source | None:
    source_json = get_db_data("aggregator/get-aggregation", {"source_id": source_id})
    return Source(**source_json) if source_json else None


def get_db_data(endpoint: str, params: dict):
    DB_HOST = os.getenv("DB_HOST", "localhost")
    db_url = f"http://{DB_HOST}:8000/{endpoint}"

    encountered_error = False

    try:
        response = requests.get(db_url, params=params, timeout=5)
    except requests.exceptions.RequestException:
        print(f"Could not get data from database service due to timeout")
        encountered_error = True
    else:
        if response.status_code != 200:
            print(f"Received status code {response.status_code} from database service")
            encountered_error = True

    return response.json() if not encountered_error else None
