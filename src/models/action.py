from datetime import datetime, timezone


class Action:
    PLACE = "place"
    MOVE = "move"
    PICKUP = "pickup"
    DISCARD = "discard"

    def __init__(self, timestamp: datetime, id: str, action: str):
        # Convert datetime to Unix timestamp in microseconds
        self.timestamp = int(
            (timestamp - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds()
            * 1_000_000
        )
        self.id = id
        self.action = action

    def get_timestamp(self) -> int:
        return self.timestamp

    def get_id(self) -> str:
        return self.id

    def get_action(self) -> str:
        return self.action

    def __str__(self) -> str:
        return str(self.to_dict())

    def to_dict(self) -> str:
        return dict(
            id=self.id,
            timestamp=self.timestamp,
            action=self.action,
        )
