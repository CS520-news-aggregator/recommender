from typing import List, Tuple
from recommender.spacy import get_spacy_preprocessor
from models.utils.constants import DB_HOST
from models.post import Post
import numpy as np
from models.utils.funcs import get_data_from_api, Response


def get_all_user_recommendations(
    list_posts: List[Post],
) -> List[Tuple[str, List[Post]]]:
    print("Received request for all user recommendations")
    list_user_recommendations = []

    if (
        list_users_ids := get_data_from_api(DB_HOST, "user/get-all-users")
    ) != Response.FAILURE:
        for user_id in list_users_ids:
            recommendations = get_user_recommendations(list_posts, user_id)
            list_user_recommendations.append((user_id, recommendations))
    else:
        print("Could not retrieve user data")

    return list_user_recommendations


def get_user_recommendations(list_posts: List[Post], user_id: str) -> List[Post]:
    if (user := get_user_info(user_id)) == Response.FAILURE:
        print(f"Could not retrieve user data for user: {user_id}")
        return []

    recommendations = get_top_posts(user["preferences"], list_posts)

    list_recommendations = list(
        filter(lambda post: post.summary and post.title, recommendations)
    )

    # FIXME: for now, put random media
    for post in list_recommendations:
        post.media = "https://t3.ftcdn.net/jpg/05/82/67/96/360_F_582679641_zCnWSvan9oScBHyWzfirpD4MKGp0kylJ.jpg"

    return list_recommendations


def get_user_info(user_id: str) -> dict | Response:
    return get_data_from_api(DB_HOST, "user/get-user", {"user_id": user_id})


def calculate_similarity(topic1, topic2):
    nlp = get_spacy_preprocessor().nlp

    topic1_vector = nlp(topic1).vector
    topic2_vector = nlp(topic2).vector

    similarity = (topic1_vector.dot(topic2_vector) + 1) / (
        np.linalg.norm(topic1_vector) * np.linalg.norm(topic2_vector)
        + len(topic1_vector)
    )

    return similarity


def get_top_posts(user_interests: List[str], posts: List[Post]) -> List[Post]:
    # Calculate similarity score for each post
    similarity_scores = []
    for post in posts:
        post_similarity = sum(
            calculate_similarity(user_interest, post_topic)
            for user_interest in user_interests
            for post_topic in post.topics
        )
        similarity_scores.append((post, post_similarity))

    # Sort posts based on similarity scores
    return [
        post for post, _ in sorted(similarity_scores, key=lambda x: x[1], reverse=True)
    ]
