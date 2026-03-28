import bisect
from typing import List, Tuple, Optional, Dict

class SortedArrayLeaderboard:
    def __init__(self):
        # List of (score, user_id).
        self.data: List[Tuple[int, int]] = []
        self.user_map: Dict[int, int] = {} # user_id -> score

    def insert(self, user_id: int, score: int):
        """
        Inserts a new user score.
        """
        if user_id in self.user_map:
            # If user already exists, update their score
            self.update(user_id, score)
            return

        self.user_map[user_id] = score
        entry = (score, user_id)
        bisect.insort(self.data, entry)

    def delete(self, user_id: int, score: Optional[int] = None):
        """
        Deletes a user score.
        """
        if score is None:
            score = self.user_map.get(user_id)
            if score is None:
                return

        if user_id in self.user_map:
            del self.user_map[user_id]

        entry = (score, user_id)
        idx = bisect.bisect_left(self.data, entry)
        if idx < len(self.data) and self.data[idx] == entry:
            self.data.pop(idx)

    def update(self, user_id: int, new_score: int):
        """
        Updates a user's score.
        """
        if user_id not in self.user_map:
            self.insert(user_id, new_score)
            return

        old_score = self.user_map[user_id]
        if old_score == new_score:
            return

        # Remove old
        self.delete(user_id, old_score)
        # Insert new
        self.insert(user_id, new_score)

    def search(self, user_id: int, score: Optional[int] = None) -> int:
        """
        Finds the rank (index) of the user.
        """
        if score is None:
            score = self.user_map.get(user_id)
            if score is None:
                return -1

        entry = (score, user_id)
        idx = bisect.bisect_left(self.data, entry)
        if idx < len(self.data) and self.data[idx] == entry:
            return idx
        return -1

    def top_k(self, k: int) -> List[Tuple[int, int]]:
        """
        Returns the top k users with highest scores.
        Returns list of (user_id, score) tuples.
        """
        # Data is sorted in ascending order, so top k are at the end
        n = len(self.data)
        if k >= n:
            # Return all in descending order
            return [(uid, score) for score, uid in reversed(self.data)]
        # Return last k elements in descending order
        return [(uid, score) for score, uid in reversed(self.data[-k:])]

    def __len__(self):
        return len(self.data)
