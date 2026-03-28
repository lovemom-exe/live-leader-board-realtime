from typing import Optional, Tuple, Dict, List

RED = True
BLACK = False

class RBNode:
    def __init__(self, user_id: int, score: int, color: bool = RED):
        self.user_id = user_id
        self.score = score
        self.color = color
        self.left: Optional['RBNode'] = None
        self.right: Optional['RBNode'] = None
        self.parent: Optional['RBNode'] = None
        self.size = 1  # Subtree size

class RBTreeLeaderboard:
    def __init__(self):
        self.nil = RBNode(0, 0, BLACK) # Sentinel node
        self.nil.size = 0
        self.root = self.nil
        self.user_map: Dict[int, int] = {} # user_id -> score

    def _update_size(self, node: RBNode):
        if node != self.nil:
            node.size = 1 + node.left.size + node.right.size

    def insert(self, user_id: int, score: int):
        if user_id in self.user_map:
            self.update(user_id, score)
            return

        self.user_map[user_id] = score
        new_node = RBNode(user_id, score)
        new_node.left = self.nil
        new_node.right = self.nil
        
        y = self.nil
        x = self.root
        
        while x != self.nil:
            y = x
            x.size += 1 # Increment size on the way down
            if (new_node.score < x.score) or (new_node.score == x.score and new_node.user_id < x.user_id):
                x = x.left
            else:
                x = x.right
        
        new_node.parent = y
        if y == self.nil:
            self.root = new_node
        elif (new_node.score < y.score) or (new_node.score == y.score and new_node.user_id < y.user_id):
            y.left = new_node
        else:
            y.right = new_node
            
        new_node.color = RED
        self._insert_fixup(new_node)

    def _left_rotate(self, x: RBNode):
        y = x.right
        x.right = y.left
        if y.left != self.nil:
            y.left.parent = x
        y.parent = x.parent
        if x.parent == self.nil:
            self.root = y
        elif x == x.parent.left:
            x.parent.left = y
        else:
            x.parent.right = y
        y.left = x
        x.parent = y
        
        y.size = x.size
        self._update_size(x)

    def _right_rotate(self, y: RBNode):
        x = y.left
        y.left = x.right
        if x.right != self.nil:
            x.right.parent = y
        x.parent = y.parent
        if y.parent == self.nil:
            self.root = x
        elif y == y.parent.right:
            y.parent.right = x
        else:
            y.parent.left = x
        x.right = y
        y.parent = x
        
        x.size = y.size
        self._update_size(y)

    def _insert_fixup(self, z: RBNode):
        while z.parent.color == RED:
            if z.parent == z.parent.parent.left:
                y = z.parent.parent.right
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z == z.parent.right:
                        z = z.parent
                        self._left_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._right_rotate(z.parent.parent)
            else:
                y = z.parent.parent.left
                if y.color == RED:
                    z.parent.color = BLACK
                    y.color = BLACK
                    z.parent.parent.color = RED
                    z = z.parent.parent
                else:
                    if z == z.parent.left:
                        z = z.parent
                        self._right_rotate(z)
                    z.parent.color = BLACK
                    z.parent.parent.color = RED
                    self._left_rotate(z.parent.parent)
        self.root.color = BLACK

    def delete(self, user_id: int, score: Optional[int] = None):
        if score is None:
            score = self.user_map.get(user_id)
            if score is None:
                return

        if user_id in self.user_map:
            del self.user_map[user_id]

        z = self._find_node(user_id, score)
        if z == self.nil:
            return

        # Decrement sizes on the path to the node to be deleted is tricky because the node might move.
        # Standard RB delete is complex.
        # For simplicity in this benchmark, I will implement the standard delete logic
        # and then re-traverse to update sizes or update sizes during the operation.
        # Updating sizes during standard RB delete is error-prone.
        # A simpler approach for size maintenance:
        # 1. Find node.
        # 2. Walk up from the *physically removed* node location to root, decrementing size.
        # But rotations also affect size.
        # Actually, rotations already handle size updates in my implementation.
        # So I just need to decrement sizes on the path from the splice point up.
        
        y = z
        y_original_color = y.color
        x = self.nil
        x_parent = self.nil
        
        if z.left == self.nil:
            x = z.right
            x_parent = z.parent # Track parent for size update
            self._transplant(z, z.right)
        elif z.right == self.nil:
            x = z.left
            x_parent = z.parent # Track parent for size update
            self._transplant(z, z.left)
        else:
            y = self._minimum(z.right)
            y_original_color = y.color
            x = y.right
            if y.parent == z:
                x.parent = y # x could be nil
                x_parent = y
            else:
                x_parent = y.parent
                self._transplant(y, y.right)
                y.right = z.right
                y.right.parent = y
            
            self._transplant(z, y)
            y.left = z.left
            y.left.parent = y
            y.color = z.color
            
            # y replaces z. y's size should become z's size.
            # But we moved y. We need to update sizes from x_parent up.
            # And y's size needs to be recalculated or set to z's size?
            # Actually, if we swap y and z, the structure changes.
            # It's easier to just re-calculate sizes on the path? No, O(log N).
            # Let's just walk up from x_parent and update sizes.
            # Note: z is gone. y is in z's spot.
            # The path from where y WAS (x_parent) up to y needs size update.
            # And y needs size update (it takes z's children).
            # Wait, standard transplant doesn't update size.
            pass

        # Correct size update strategy:
        # Walk up from x_parent to root, recalculating size.
        curr = x_parent
        while curr != self.nil and curr is not None:
             self._update_size(curr)
             curr = curr.parent
             
        if y_original_color == BLACK:
            self._delete_fixup(x)

    def _transplant(self, u: RBNode, v: RBNode):
        if u.parent == self.nil:
            self.root = v
        elif u == u.parent.left:
            u.parent.left = v
        else:
            u.parent.right = v
        v.parent = u.parent

    def _minimum(self, node: RBNode):
        while node.left != self.nil:
            node = node.left
        return node

    def _delete_fixup(self, x: RBNode):
        while x != self.root and x.color == BLACK:
            if x == x.parent.left:
                w = x.parent.right
                if w.color == RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._left_rotate(x.parent)
                    w = x.parent.right
                if w.left.color == BLACK and w.right.color == BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.right.color == BLACK:
                        w.left.color = BLACK
                        w.color = RED
                        self._right_rotate(w)
                        w = x.parent.right
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.right.color = BLACK
                    self._left_rotate(x.parent)
                    x = self.root
            else:
                w = x.parent.left
                if w.color == RED:
                    w.color = BLACK
                    x.parent.color = RED
                    self._right_rotate(x.parent)
                    w = x.parent.left
                if w.right.color == BLACK and w.left.color == BLACK:
                    w.color = RED
                    x = x.parent
                else:
                    if w.left.color == BLACK:
                        w.right.color = BLACK
                        w.color = RED
                        self._left_rotate(w)
                        w = x.parent.left
                    w.color = x.parent.color
                    x.parent.color = BLACK
                    w.left.color = BLACK
                    self._right_rotate(x.parent)
                    x = self.root
        x.color = BLACK

    def _find_node(self, user_id: int, score: int) -> RBNode:
        current = self.root
        while current != self.nil:
            if current.user_id == user_id and current.score == score:
                return current
            elif (score < current.score) or (score == current.score and user_id < current.user_id):
                current = current.left
            else:
                current = current.right
        return self.nil

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

        current = self.root
        rank = 0
        while current != self.nil:
            if current.user_id == user_id and current.score == score:
                return rank + current.left.size
            elif (score < current.score) or (score == current.score and user_id < current.user_id):
                current = current.left
            else:
                rank += current.left.size + 1
                current = current.right
        return -1

    def top_k(self, k: int) -> List[Tuple[int, int]]:
        """
        Returns the top k users with highest scores.
        Returns list of (user_id, score) tuples.
        Uses reverse in-order traversal (right -> node -> left).
        """
        result = []
        
        def reverse_inorder(node: RBNode, remaining: int) -> int:
            if node == self.nil or remaining <= 0:
                return remaining
            
            # Visit right subtree first (higher scores)
            remaining = reverse_inorder(node.right, remaining)
            
            # Visit current node
            if remaining > 0:
                result.append((node.user_id, node.score))
                remaining -= 1
            
            # Visit left subtree
            if remaining > 0:
                remaining = reverse_inorder(node.left, remaining)
            
            return remaining
        
        reverse_inorder(self.root, k)
        return result

    def __len__(self):
        return self.root.size
