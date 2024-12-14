from datetime import datetime, timezone
from threading import Lock
from typing import List

from models.action import Action
from models.thread_safe_list import ThreadSafeList


class ActionLog:
    def __init__(self, actions: ThreadSafeList = None):
        if actions is None:
            self._actions = ThreadSafeList()
        else:
            self._actions = actions
        self._lock = Lock()
        self._snapshot = []

    def place(self, order_id: str):
        self.add(self.get_place(order_id))

    def move(self, order_id: str):
        self.add(self.get_move(order_id))

    def discard(self, order_id: str):
        self.add(self.get_discard(order_id))

    def pickup(self, order_id: str):
        self.add(self.get_pickup(order_id))

    def add(self, action: Action):
        self._actions.append(action)

    def get_snapshot(self) -> List[Action]:
        actions = self._actions.get_snapshot()
        return sorted(actions, key=lambda action: action.timestamp)

    @staticmethod
    def get_move(order_id: str):
        return Action(ActionLog._get_now(), order_id, Action.MOVE)

    @staticmethod
    def get_place(order_id: str):
        return Action(ActionLog._get_now(), order_id, Action.PLACE)

    @staticmethod
    def get_discard(order_id: str):
        return Action(ActionLog._get_now(), order_id, Action.DISCARD)

    @staticmethod
    def get_pickup(order_id: str):
        return Action(ActionLog._get_now(), order_id, Action.PICKUP)

    @staticmethod
    def _get_now():
        return datetime.now(tz=timezone.utc)
