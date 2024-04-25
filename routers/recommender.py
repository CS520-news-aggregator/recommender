from fastapi import APIRouter, Body, Request
from fastapi.encoders import jsonable_encoder
from models.source import Source
from models.post import Post
import os
import requests
import spacy

# pip install spacy
# python -m spacy download en_core_web_lg
import numpy as np

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
    # user_votes = Counter(user["votes"])

    # post_matches = Counter()
    # for i in range(len(list_posts)):
    #     post, annotation = list_posts[i]
    #     annotation_counts = Counter(annotation)
    #     post_matches[post] = sum((user_prefs & annotation_counts).values())

    nlp = spacy.load("en_core_web_lg")
    recommendations = get_top_posts(user["preferences"], list_posts, nlp, limit)

    list_recommendations = [change_db_id_to_str(jsonable_encoder(post)) for post in recommendations]

    list_recommendations = list(filter(lambda post: post["summary"] and post["title"], list_recommendations))

    # FIXME: for now, put random media
    for post in list_recommendations:
        post["title"] = "Random title"
        post["summary"] = "Random summary"
        post["media"] = "https://t3.ftcdn.net/jpg/05/82/67/96/360_F_582679641_zCnWSvan9oScBHyWzfirpD4MKGp0kylJ.jpg"

    return {
        "message": "Recommendation sent",
        "list_recommendations": list_recommendations,
    }


def get_user_info(user_id: str) -> dict | None:
    return get_db_data("user/get-user", {"user_id": user_id})


def get_posts() -> list[Post]:
    list_posts = list()

    if list_posts_json := get_db_data("annotator/get-all-posts", {"limit": POSTS_PULL_LIMIT}):
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


def calculate_similarity(nlp, topic1, topic2):
    topic1_vector = nlp(topic1).vector
    topic2_vector = nlp(topic2).vector
    return topic1_vector.dot(topic2_vector) / (np.linalg.norm(topic1_vector) * np.linalg.norm(topic2_vector))


def get_top_posts(user_interests, posts, nlp, x):
    similarity_scores = []
    for post in posts:
        post_similarity = sum(
            calculate_similarity(nlp, user_interest, post_topic) for user_interest in user_interests for post_topic in post.topics
        )
        similarity_scores.append((post, post_similarity))

    sorted_posts = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    return [post for post, _ in sorted_posts[:x]]
