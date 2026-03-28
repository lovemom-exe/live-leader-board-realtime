from typing import Optional, Tuple, Dict, List

class ListNode:
    def __init__(self, user_id: int, score: int):
        self.user_id = user_id
        self.score = score
        self.next: Optional['ListNode'] = None

class LinkedListLeaderboard:
    def __init__(self):
        self.head: Optional[ListNode] = None
        self.size = 0
        self.user_map: Dict[int, int] = {} # user_id -> score

    def insert(self, user_id: int, score: int):
        """
        Inserts a new user score in sorted order (ascending score).
        """
        if user_id in self.user_map:
            self.update(user_id, score)
            return

        self.user_map[user_id] = score
        new_node = ListNode(user_id, score)
        self.size += 1

        if not self.head or (self.head.score > score) or (self.head.score == score and self.head.user_id > user_id):
            new_node.next = self.head
            self.head = new_node
            return

        current = self.head
        while current.next:
            # Check if next node is greater than new node
            if (current.next.score > score) or (current.next.score == score and current.next.user_id > user_id):
                break
            current = current.next
        
        new_node.next = current.next
        current.next = new_node

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

        if not self.head:
            return

        if self.head.user_id == user_id and self.head.score == score:
            self.head = self.head.next
            self.size -= 1
            return

        current = self.head
        while current.next:
            if current.next.user_id == user_id and current.next.score == score:
                current.next = current.next.next
                self.size -= 1
                return
            current = current.next

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

        current = self.head
        index = 0
        while current:
            if current.user_id == user_id and current.score == score:
                return index
            current = current.next
            index += 1
        return -1

    def top_k(self, k: int) -> List[Tuple[int, int]]:
        """
        Returns the top k users with highest scores.
        Returns list of (user_id, score) tuples.
        """
        # Collect all elements first (list is sorted ascending)
        elements = []
        current = self.head
        while current:
            elements.append((current.user_id, current.score))
            current = current.next
        
        # Return last k in descending order
        if k >= len(elements):
            return [(uid, score) for uid, score in reversed(elements)]
        return [(uid, score) for uid, score in reversed(elements[-k:])]

    def __len__(self):
        return self.size
