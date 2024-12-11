import logging
import sys

from flask import Flask, jsonify, request
import multiprocessing

from pydantic import ValidationError


from models.config import Config
from scheduler.scheduler_utils import get_problem

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
        return jsonify({"errors": e.errors()}), 400

    problem = get_problem(config)

    logger.info(f"Starting to schedule orders for problem: {problem.test_id}")

    # TODO schedule orders
    # process = multiprocessing.Process(target=background_task, args=("example",))
    # process.start()
    # return jsonify(
    #     {"message": "Task started in a separate process", "pid": process.pid}
    # )

    return (
        jsonify({"message": "OK"}),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True)
