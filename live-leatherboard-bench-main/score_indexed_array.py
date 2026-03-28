from typing import List, Optional, Dict

class ScoreIndexedArrayLeaderboard:
    """
    Leaderboard implementation using a score-indexed array with position tracking.
    Constraint: Maximum score is 15,000.
    
    Each array element buckets[i] stores a list of user IDs with score i.
    Uses swap+pop technique for O(1) delete/update operations.
    
    Key optimization: pos dict tracks each user's position in their bucket,
    allowing O(1) removal via swap with last element + pop.
    """
    
    def __init__(self, max_score: int = 15000):
        self.max_score = max_score
        # Array where index = score, value = list of user_ids with that score
        self.score_buckets: List[List[int]] = [[] for _ in range(max_score + 1)]
        # Map: user_id -> current score
        self.user_map: Dict[int, int] = {}
        # Map: user_id -> position in buckets[score[user_id]]
        self.pos_map: Dict[int, int] = {}
        # Track total number of users
        self.total_users = 0

    def insert(self, user_id: int, score: int):
        """
        Inserts a new user score.
        Time Complexity: O(1)
        """
        if user_id in self.user_map:
            # If user already exists, update their score
            self.update(user_id, score)
            return
        
        if score < 0 or score > self.max_score:
            raise ValueError(f"Score must be between 0 and {self.max_score}")
        
        # Add to bucket
        self.score_buckets[score].append(user_id)
        # Track position and score
        self.pos_map[user_id] = len(self.score_buckets[score]) - 1
        self.user_map[user_id] = score
        self.total_users += 1

    def delete(self, user_id: int, score: Optional[int] = None):
        """
        Deletes a user score using swap+pop technique.
        Time Complexity: O(1)
        """
        if user_id not in self.user_map:
            return
        
        if score is None:
            score = self.user_map[user_id]
        
        # Get position of user in bucket
        idx = self.pos_map[user_id]
        bucket = self.score_buckets[score]
        
        # Swap with last element and pop (O(1) removal)
        last_user = bucket[-1]
        bucket[idx] = last_user
        bucket.pop()
        
        # Update position of swapped user (if it's not the same user)
        if last_user != user_id:
            self.pos_map[last_user] = idx
        
        # Clean up maps
        del self.user_map[user_id]
        del self.pos_map[user_id]
        self.total_users -= 1

    def _move_player(self, user_id: int, old_score: int, new_score: int):
        """
        Internal method to move a player from old_score bucket to new_score bucket.
        Time Complexity: O(1)
        """
        # Remove from old bucket using swap+pop
        idx = self.pos_map[user_id]
        old_bucket = self.score_buckets[old_score]
        last_user = old_bucket[-1]
        old_bucket[idx] = last_user
        old_bucket.pop()
        
        # Update position of swapped user
        if last_user != user_id:
            self.pos_map[last_user] = idx
        
        # Add to new bucket
        self.score_buckets[new_score].append(user_id)
        self.pos_map[user_id] = len(self.score_buckets[new_score]) - 1
        self.user_map[user_id] = new_score

    def update(self, user_id: int, new_score: int):
        """
        Updates a user's score.
        Time Complexity: O(1)
        """
        if new_score < 0 or new_score > self.max_score:
            raise ValueError(f"Score must be between 0 and {self.max_score}")
        
        if user_id not in self.user_map:
            self.insert(user_id, new_score)
            return
        
        old_score = self.user_map[user_id]
        if old_score == new_score:
            return
        
        # Move player between buckets
        self._move_player(user_id, old_score, new_score)

    def search(self, user_id: int, score: Optional[int] = None) -> int:
        """
        Finds the rank (index) of the user.
        Rank is calculated as the number of users with higher scores.
        Time Complexity: O(max_score)
        """
        if user_id not in self.user_map:
            return -1
        
        if score is None:
            score = self.user_map[user_id]
        
        # Count all users with scores higher than this user's score
        rank = 0
        for s in range(score + 1, self.max_score + 1):
            rank += len(self.score_buckets[s])
        
        # Add position within the same score bucket
        rank += self.pos_map[user_id]
        
        return rank

    def top_k(self, k: int) -> List[tuple]:
        """
        Returns the top k users with their scores.
        Time Complexity: O(max_score + k)
        """
        result = []
        count = 0
        
        # Iterate from highest score to lowest
        for score in range(self.max_score, -1, -1):
            for user_id in self.score_buckets[score]:
                result.append((user_id, score))
                count += 1
                if count >= k:
                    return result
        
        return result

    def __len__(self):
        return self.total_users
