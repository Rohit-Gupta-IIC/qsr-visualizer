from abc import ABC, abstractmethod
from collections import defaultdict, namedtuple
import math
import numpy as np

class MCTS:

    def __init__(self, exploration_weight=1, env=None):
        self.Q = defaultdict(int)  # total reward of each node
        self.N = defaultdict(int)  # total visit count for each node
        self.children = dict()  # children of each node
        self.exploration_weight = exploration_weight
        self.env = env

    def choose(self, node):
        if node.is_terminal():
            raise RuntimeError(f"choose called on terminal node {node}")

        if node not in self.children:
            return node.find_random_child()

        def score(n):
            if self.N[n] == 0:
                return float("-inf")  # avoid unseen moves
            return self.Q[n] / self.N[n]  # average reward

        return max(self.children[node], key=score), np.max(list(map(score, self.children[node])))

    def do_rollout(self, node):
        path = self._select(node)
        leaf = path[-1]
        self._expand(leaf)
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

    def _select(self, node):
        path = []
        while True:
            path.append(node)
            if node not in self.children or not self.children[node]:
                # node is either unexplored or terminal
                return path
            unexplored = self.children[node] - self.children.keys()
            if unexplored:
                n = unexplored.pop()
                path.append(n)
                return path
            node = self._uct_select(node)  # descend a layer deeper

    def _expand(self, node):
        if node in self.children:
            return  # already expanded
        self.children[node] = node.find_children()

    def _simulate(self, node):
        invert_reward = True
        while True:
            if node.is_terminal():
                reward = node.reward()
                self.env.is_reset = True
                return 1 - reward if invert_reward else reward
            node = node.find_random_child()
            invert_reward = not invert_reward

    def _backpropagate(self, path, reward):
        for node in reversed(path):
            self.N[node] += 1
            self.Q[node] += reward
            reward = 1 - reward  # 1 for me is 0 for my enemy, and vice versa

    def _uct_select(self, node):
        # All children of node should already be expanded:
        assert all(n in self.children for n in self.children[node])
        
        log_N_vertex = math.log(self.N[node])
        
        def uct(item):
            return self.Q[item] / self.N[item] + self.exploration_weight * math.sqrt(
                log_N_vertex / self.N[item]
            )
        
        return max(self.children[node], key=uct)