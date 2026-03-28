import random
from typing import Optional, List, Dict, Tuple

class SkipNode:
    def __init__(self, user_id: int, score: int, level: int):
        self.user_id = user_id
        self.score = score
        # forward[i] points to the next node at level i
        self.forward: List[Optional['SkipNode']] = [None] * (level + 1)
        # span[i] is the distance to the next node at level i
        self.span: List[int] = [0] * (level + 1)

class SkipListLeaderboard:
    def __init__(self, max_level: int = 16, p: float = 0.5):
        self.max_level = max_level
        self.p = p
        self.header = SkipNode(-1, -1, max_level)
        self.level = 0
        self.size = 0
        self.user_map: Dict[int, int] = {} # user_id -> score

    def _random_level(self) -> int:
        lvl = 0
        while random.random() < self.p and lvl < self.max_level:
            lvl += 1
        return lvl

    def insert(self, user_id: int, score: int):
        if user_id in self.user_map:
            self.update(user_id, score)
            return

        self.user_map[user_id] = score
        update = [None] * (self.max_level + 1)
        rank = [0] * (self.max_level + 1)
        x = self.header

        # Find position
        for i in range(self.level, -1, -1):
            rank[i] = rank[i + 1] if i + 1 <= self.level else 0
            while x.forward[i] and (x.forward[i].score < score or (x.forward[i].score == score and x.forward[i].user_id < user_id)):
                rank[i] += x.span[i]
                x = x.forward[i]
            update[i] = x

        lvl = self._random_level()
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1):
                rank[i] = 0
                update[i] = self.header
                update[i].span[i] = self.size
            self.level = lvl

        x = SkipNode(user_id, score, lvl)
        for i in range(lvl + 1):
            x.forward[i] = update[i].forward[i]
            update[i].forward[i] = x

            # update span covered by update[i] as x is inserted here
            x.span[i] = update[i].span[i] - (rank[0] - rank[i])
            update[i].span[i] = (rank[0] - rank[i]) + 1

        # increment span for untouched levels
        for i in range(lvl + 1, self.level + 1):
            update[i].span[i] += 1

        self.size += 1

    def delete(self, user_id: int, score: Optional[int] = None):
        if score is None:
            score = self.user_map.get(user_id)
            if score is None:
                return

        if user_id in self.user_map:
            del self.user_map[user_id]

        update = [None] * (self.max_level + 1)
        x = self.header
        for i in range(self.level, -1, -1):
            while x.forward[i] and (x.forward[i].score < score or (x.forward[i].score == score and x.forward[i].user_id < user_id)):
                x = x.forward[i]
            update[i] = x

        x = x.forward[0]
        if x and x.score == score and x.user_id == user_id:
            for i in range(self.level + 1):
                if update[i].forward[i] != x:
                    break
                update[i].forward[i] = x.forward[i]
                update[i].span[i] += x.span[i] - 1
            
            # Correct loop for higher levels
            for i in range(self.level + 1):
                if update[i].forward[i] != x:
                     update[i].span[i] -= 1

            while self.level > 0 and self.header.forward[self.level] is None:
                self.level -= 1
            self.size -= 1

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
        Finds the rank (0-based index) of the user.
        """
        if score is None:
            score = self.user_map.get(user_id)
            if score is None:
                return -1

        x = self.header
        rank = 0
        for i in range(self.level, -1, -1):
            while x.forward[i] and (x.forward[i].score < score or (x.forward[i].score == score and x.forward[i].user_id < user_id)):
                rank += x.span[i]
                x = x.forward[i]
        
        # Check if next node is the target
        if x.forward[0] and x.forward[0].score == score and x.forward[0].user_id == user_id:
            return rank
        return -1

    def top_k(self, k: int) -> List[Tuple[int, int]]:
        """
        Returns the top k users with highest scores.
        Returns list of (user_id, score) tuples.
        """
        # Traverse the skip list at level 0 to collect all elements
        elements = []
        current = self.header.forward[0]
        while current:
            elements.append((current.user_id, current.score))
            current = current.forward[0]
        
        # Return last k in descending order (list is sorted ascending)
        if k >= len(elements):
            return [(uid, score) for uid, score in reversed(elements)]
        return [(uid, score) for uid, score in reversed(elements[-k:])]

    def __len__(self):
        return self.size
