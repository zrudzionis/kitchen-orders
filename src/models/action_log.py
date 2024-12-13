from datetime import datetime
from typing import List


from models.action import Action
from utils import get_is_queue


class ActionLog:
    def __init__(self, actions: List = None):
        if not actions:
            self._actions = []
        else:
            self.actions = actions

    def place(self, order_id: str):
        self.add_action(self.get_place(order_id))

    def move(self, order_id: str):
        self.add_action(self.get_move(order_id))

    def discard(self, order_id: str):
        self.add_action(self.get_discard(order_id))

    def pickup(self, order_id: str):
        self.add_action(self.get_pickup(order_id))

    def add(self, action: Action):
        if get_is_queue(self.actions):
            self.actions.put(action)
        else:
            self.actions.append(action)

    @property
    def actions(self):
        return sorted(self._actions, key=lambda action: action.timestamp)

    @staticmethod
    def get_move(order_id: str):
        return Action(datetime.now(), order_id, Action.MOVE)

    @staticmethod
    def get_place(order_id: str):
        return Action(datetime.now(), order_id, Action.PLACE)

    @staticmethod
    def get_discard(order_id: str):
        return Action(datetime.now(), order_id, Action.DISCARD)

    @staticmethod
    def get_pickup(order_id: str):
        return Action(datetime.now(), order_id, Action.PICKUP)
