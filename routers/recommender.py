from fastapi import APIRouter, Body, Request
from models.data import Post, Annotation
import os
import requests

recommender_router = APIRouter(prefix="/recommender")
POSTS_PULL_LIMIT = 10


@recommender_router.get("/get-recommendations")
async def get_recommendations(_: Request, user_id: str, limit: int):
    print(f"Received request for recommendations for user: {user_id}")

    posts_to_annotation = get_posts_info()
    list_recommendations: list[Post] = list()

    # Dummy recommendation logic
    for i in range(min(limit, len(posts_to_annotation))):
        post, annotation = posts_to_annotation[i]
        list_recommendations.append(post)

    return {
        "message": "Recommendation sent",
        "list_recommendations": [post._id for post in list_recommendations],
    }


def get_posts_info() -> list[tuple[Post, Annotation]]:
    posts_to_annotation = list()

    if list_posts_json := get_db_data(
        "aggregator/get-all-aggregations", {"limit": POSTS_PULL_LIMIT}
    ):
        for post_json in list_posts_json["list_posts"]:
            post = Post(**post_json)
            post._id = post_json["_id"]

            annotation_json = get_db_data(
                "annotator/get-annotation", {"post_id": post._id}
            )

            if annotation_json and annotation_json["annotations"]:
                annotations = Annotation(**annotation_json["annotations"])
                posts_to_annotation.append((post, annotations))

    return posts_to_annotation


def get_db_data(endpoint: str, params: dict):
    DB_HOST = os.getenv("DB_HOST", "localhost")
    db_url = f"http://{DB_HOST}:8000/{endpoint}"

    encountered_error = False

    try:
        response = requests.get(db_url, params=params, timeout=5)
    except requests.exceptions.RequestException:
        print(f"Could not send data to database service due to timeout")
        encountered_error = True
    else:
        if response.status_code != 200:
            print(f"Received status code {response.status_code} from database service")
            encountered_error = True

    return response.json() if not encountered_error else None
