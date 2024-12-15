import logging
import sys

from flask import Flask, jsonify, request
from pydantic import ValidationError

from models.config import Config
from scheduler.scheduler import schedule_problem_orders
from src.scheduler.scheduler_utils import load_problem
from src.validators.actions_validators import validate_actions

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/schedule-orders", methods=["POST"])
def schedule_orders():
    if not request.is_json:
        return jsonify({"error": "Request must be in JSON format"}), 400

    raw_config = request.get_json()
    try:
        config = Config(**raw_config)
    except ValidationError as e:
        errors = [error["msg"] for error in e.errors()]
        return jsonify({"errors": errors}), 400

    problem = load_problem(config)
    if len(problem.orders) == 0:
        return jsonify(
            {"errors": f"Problem has no orders: {problem.to_dict()}"}), 400

    actions = schedule_problem_orders(problem, config)

    try:
        validate_actions(actions)
        logger.info("Order actions are valid.")
    except ValueError as e:
        logger.error("Order actions are invalid. Validation error: %s", e)

    return (
        jsonify({"actions": [action.to_dict() for action in actions]}),
        200,
    )


if __name__ == "__main__":
    # we would't do this in production
    app.run(debug=True)
