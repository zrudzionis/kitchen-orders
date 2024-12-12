from src.models.action import Action
from datetime import datetime


class ActionLog:
    def __init__(self):
        self._actions = []

    def place(self, order_id: str):
        self._actions.append(Action(datetime.now(), order_id, Action.PLACE))

    def move(self, order_id: str):
        self._actions.append(Action(datetime.now(), order_id, Action.MOVE))

    def discard(self, order_id: str):
        self._actions.append(Action(datetime.now(), order_id, Action.DISCARD))

    def pickup(self, order_id: str):
        self._actions.append(Action(datetime.now(), order_id, Action.PICKUP))

    @property
    def actions(self):
        return sorted(self.actions, key=lambda action: action.timestamp)
