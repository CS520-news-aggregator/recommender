from fastapi import APIRouter, Body, Request
from models.data import Post, Annotation
import os
import requests
from collections import Counter

recommender_router = APIRouter(prefix="/recommender")
POSTS_PULL_LIMIT = 10


@recommender_router.get("/get-recommendations")
async def get_recommendations(_: Request, user_id: str, limit: int):
    print(f"Received request for recommendations for user: {user_id}")

    list_annotations = get_annotations()
    list_posts = get_posts()

    if user := get_user_info(user_id) is None:
        return {
            "message": "Could not retrieve user data",
            "list_recommendations": [],
        }

    # user_prefs = Counter(user["preferences"])

    # post_matches = Counter()
    # for i in range(len(list_annotations)):
    #     post, annotation = list_annotations[i]
    #     annotation_counts = Counter(annotation)
    #     post_matches[post] = sum((user_prefs & annotation_counts).values())

    # list_recommendations = post_matches.most_common(limit)

    return {
        "message": "Recommendation sent",
        # "list_recommendations": list_annotations[:limit],
        "list_recommendations": list_posts[:limit],
    }


def get_user_info(user_id: str) -> dict | None:
    return get_db_data("user/get-user", {"user_id": user_id})


def get_annotations() -> list[Annotation]:
    list_annotations = list()

    if list_annotations_json := get_db_data(
        "annotator/get-all-annotations", {"limit": POSTS_PULL_LIMIT}
    ):
        for annotation_json in list_annotations_json["list_annotations"]:
            annotation = Annotation(**annotation_json)
            list_annotations.append(annotation)

    return list_annotations


def get_posts() -> list[Post]:
    list_posts = list()

    if list_posts_json := get_db_data(
        "aggregator/get-all-aggregations", {"limit": POSTS_PULL_LIMIT}
    ):
        for post_json in list_posts_json["list_posts"]:
            post = Post(**post_json)
            list_posts.append(post)

    return list_posts


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
