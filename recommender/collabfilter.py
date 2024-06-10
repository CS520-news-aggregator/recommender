from collections import defaultdict
import networkx as nx
from typing import List
import asyncio
from models.utils.funcs import get_data_from_api, add_data_to_api
from models.utils.constants import DB_HOST, DT_FORMAT
from models.user import UserVotes
from models.user_recommendation import UserRecommendation
from datetime import datetime
import os


class CollabFilteringDaemon:
    """A daemon that executes a task every x seconds"""

    def __init__(self, delay: int) -> None:
        self._delay = delay
        self.first_run = os.getenv("RUN_FIRST", False)

    async def _execute_task(self) -> None:
        await self._task()

    async def start_daemon(self) -> None:
        while True:
            if self.first_run:
                await asyncio.sleep(120)  # Wait for other services to start
                await self._execute_task()
                self.first_run = False

            await asyncio.sleep(self._delay)
            await self._execute_task()

    async def _task(self) -> None:
        all_users = get_data_from_api(DB_HOST, "user/get-all-users")

        all_user_list = [
            get_data_from_api(DB_HOST, "user/get-user", {"user_id": all_users[i]})
            for i in range(len(all_users))
        ]

        G, user_likes = create_user_graph(all_user_list[:-1])

        # Key: user_id, Value: list of recommended posts
        recommended_posts_for_users = dict()

        for user_id in user_likes:
            neighbors = list(G.neighbors(user_id))
            recommended_posts = set()

            total_edge_weight = sum(
                G[user_id][neighbor]["weight"] for neighbor in neighbors
            )

            for neighbor in neighbors:
                neighbor_likes = user_likes.get(neighbor, set())

                edge_weight = G[user_id][neighbor]["weight"]
                score = edge_weight / total_edge_weight if total_edge_weight > 0 else 0

                for post in neighbor_likes:
                    recommended_posts.add((post, score))

            user_posts = set(post for post in user_likes[user_id])

            recommended_posts = {
                (post, score)
                for post, score in recommended_posts
                if post not in user_posts
            }

            recommended_posts_for_users[user_id] = recommended_posts

        for user_id, user_recommendations_tup in recommended_posts_for_users.items():
            user_recommendation = UserRecommendation(
                user_id=user_id,
                post_scores=[(post, score) for post, score in user_recommendations_tup],
                date=datetime.now().strftime(DT_FORMAT),
            )
            add_data_to_api(
                DB_HOST, "user_recommendation/add-recommendation", user_recommendation
            )

        print("Added all user recommendations")


def create_user_graph(all_users_list: List[UserVotes]):
    G = nx.Graph()

    likes_map = defaultdict(list)
    user_likes = {}  # This dictionary stores the posts liked by each user

    for user_votes in all_users_list:
        user = user_votes["votes"]
        user_id = user["user_id"]
        G.add_node(user_id)

        user_likes[user_id] = set(user["list_of_posts_upvotes"])

        for post_id in user["list_of_posts_upvotes"]:
            likes_map[post_id].append(user_id)

    users = list(user_likes.keys())
    for i in range(len(users)):
        for j in range(i + 1, len(users)):
            edge_weight = len(user_likes[users[i]] & user_likes[users[j]])
            G.add_edge(users[i], users[j], weight=edge_weight)

    return G, user_likes
