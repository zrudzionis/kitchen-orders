from datetime import datetime, timezone
from typing import List
from models.action import Action


def validate_serialized_actions(serialized_actions: List[dict]):
    actions = [
        Action(
            **{
                **action,
                "timestamp": datetime.fromtimestamp(
                    action.pop("timestamp") / 1_000_000, tz=timezone.utc
                ),
            }
        )
        for action in serialized_actions
    ]
    validate_actions(actions)


def validate_actions(actions: List[Action]):
    _validate_single_place_pickup_discard_per_order(actions)
    _validate_orders_have_place_and_pickup(actions)
    _validate_pickup_or_discard_happens_after_place(actions)


def _validate_single_place_pickup_discard_per_order(actions: List[Action]):
    counter = dict()
    for action in actions:
        order_id = action.id
        key = f"{order_id}-{action.action_type}"
        counter[key] = counter.get(key, 0) + 1
        count = counter[key]
        if (
            action.action_type in (Action.PLACE, Action.PICKUP, Action.DISCARD)
            and count > 1
        ):
            raise ValueError(
                f"Order id: {order_id} has more than one {action.action_type} event. Event count: {count}."
            )


def _validate_orders_have_place_and_pickup(actions: List[Action]):
    order_ids = set([action.id for action in actions])
    action_map = dict(
        (f"{action.id}-{action.action_type}", action.timestamp) for action in actions
    )

    for order_id in order_ids:
        place = action_map.get(f"{order_id}-{Action.PLACE}")
        pickup = action_map.get(f"{order_id}-{Action.PICKUP}")
        discard = action_map.get(f"{order_id}-{Action.DISCARD}")
        if not place:
            raise ValueError(f"Order id: {order_id} doesn't have place event.")
        if not pickup and not discard:
            raise ValueError(
                f"Order id: {order_id} doesn't have pickup or discard event."
            )


def _validate_pickup_or_discard_happens_after_place(actions: List[Action]):
    order_ids = set([action.id for action in actions])
    action_map = dict(
        (f"{action.id}-{action.action_type}", action.timestamp) for action in actions
    )

    for order_id in order_ids:
        place = action_map.get(f"{order_id}-{Action.PLACE}")
        pickup = action_map.get(f"{order_id}-{Action.PICKUP}")
        discard = action_map.get(f"{order_id}-{Action.DISCARD}")
        if place and pickup and place > pickup:
            raise ValueError(
                f"Order id: {order_id} pickup ({pickup}) happens before place ({place})."
            )
        if place and discard and place > discard:
            raise ValueError(
                f"Order id: {order_id} discard ({discard}) happens before place ({place})."
            )
