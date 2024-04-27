from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from tqdm import tqdm
from models.post import Post
from models.recommendation import Recommendation
from models.utils.funcs import get_data_from_api, add_data_to_api, Response
from models.utils.constants import DB_HOST
from models.recommendation import RecommendationQuery, PostRecommendation
from recommender.preferences import get_all_user_recommendations

recommender_router = APIRouter(prefix="/recommender")


@recommender_router.get("/get-recommendations")
async def get_recommendations(_: Request, user_id: str, limit: int):
    print(f"Received request for recommendations for user: {user_id}")
    if (
        user_recommendations := get_data_from_api(
            DB_HOST, "recommendation/get-recommendations", {"user_id": user_id}
        )
    ) == Response.FAILURE:
        raise HTTPException(status_code=404, detail="Recommendations not found")

    recommendations = [
        Recommendation(**rec) for rec in user_recommendations["recommendations"]
    ]

    user_posts = []

    for rec in recommendations:
        for post in rec.post_recommendations:
            post_id = post.post_id
            if post_json := get_data_from_api(
                DB_HOST, "annotator/get-post", {"post_id": post_id}
            ):
                user_posts.append(post_json["post"])

            if len(user_posts) >= limit:
                break

    # FIXME: for now, put random media
    for post in user_posts:
        post["media"] = (
            "https://t3.ftcdn.net/jpg/05/82/67/96/360_F_582679641_zCnWSvan9oScBHyWzfirpD4MKGp0kylJ.jpg"
        )

    return {
        "message": "Recommendation sent",
        "list_recommendations": user_posts,
    }


# recommender/add-recommendations
@recommender_router.post("/add-recommendations")
async def add_recommendations(
    _: Request,
    background_tasks: BackgroundTasks,
    recommendation_query: RecommendationQuery,
):
    print("Received request to add recommendations")
    background_tasks.add_task(process_posts, recommendation_query)
    return {"message": "Recommendation process started"}


def process_posts(recommendation_query: RecommendationQuery):
    list_posts = []

    for post_id in recommendation_query.post_ids:
        if (
            post_json := get_data_from_api(
                DB_HOST, "annotator/get-post", {"post_id": post_id}
            )
            == Response.SUCCESS
        ):
            list_posts.append(Post(**post_json["post"]))

    # FIXME: user posts empty for new users upon registration
    user_recommendations = get_all_user_recommendations(recommendation_query.post_ids)

    for user_id, user_recomm_posts in tqdm(
        user_recommendations, desc="Adding user recommendations"
    ):
        post_recommendations = [
            PostRecommendation(post_id=post.id, date=post.date)
            for post in user_recomm_posts
        ]

        user_recommendation = Recommendation(
            user_id=user_id, post_recommendations=post_recommendations
        )

        add_data_to_api(
            DB_HOST, "recommendation/add-recommendation", user_recommendation
        )
