# Kitchen Orders

## Quickstart

### If you are willing to install python

Create virtualenv (virtualenvwrapper must be installed):

```
mkvirtualenv kitchen-orders
```

Activate virtualenv:

```
workon kitchen-orders
```

Install dependencies:

```
pip3 install -r requirements.txt
```

Start containers. Once we start containers we can continue using them on new problems.

```
python3 entrypoint.py start-containers
```

Remove containers. Removes containers, networks, volumes. Removes any previous state.

```
python3 entrypoint.py remove-containers
```

Start cooking (solving problem). Run this command with `--help` flag to see full list of options.

```
python3 entrypoint.py start-cooking
```

### If you don't want to install python

Start containers. Once we start containers we can continue using them on new problems.

```
docker-compose build && docker-compose up
```

Remove containers. Removes containers, networks, volumes. Removes any previous state.

```
docker-compose down --remove-orphans --volumes
```

### Once containers are started you can interact with solver via cURL

Run order scheduling with problem server:

```bash
  curl -X POST http://localhost:8000/schedule-orders \
     -H "Content-Type: application/json" \
     -d '{
            "auth": "<INSERT AUTH TOKEN HERER>",
            "order_rate": 500,
            "min_pickup": 4,
            "max_pickup": 8
        }'
```

Run order scheduling with problem server with more options:

```bash
  curl -X POST http://localhost:8000/schedule-orders \
     -H "Content-Type: application/json" \
     -d '{"auth": "<INSERT AUTH TOKEN HERER>"}'
```

Run order scheduling with local problem file (file location must be `containers_data/problem.json`):

```bash
  curl -X POST http://localhost:8000/schedule-orders \
     -H "Content-Type: application/json" \
     -d '{"problem_file_path": "/home/containers_data/problem.json"}'
```

Run order scheduling with local problem file and full configuration:

```
 curl -X POST http://localhost:8000/schedule-orders \
     -H "Content-Type: application/json" \
     -d '{
            "problem_file_path": "/home/containers_data/problem.json",
            "order_rate": 500,
            "min_pickup": 4,
            "max_pickup": 8
        }'

```

### Requirements

Versions below were used to test this solution.

Python:

```
python3 --version
Python 3.10.12
```

Docker:

```
docker --version
Docker version 24.0.7, build 24.0.7-0ubuntu2~22.04.1
```

Docker compose:

```
docker-compose --version
docker-compose version 1.29.2, build unknown
```

Some containers start on fixed ports:

- PostgresSQL database: 5432
- Web server: 8000
- Adminer: 8080

## Quality Control

Run linter:

```
docker-compose -f docker-compose.lint.yml build && docker-compose -f docker-compose.lint.yml up --abort-on-container-exit --exit-code-from lint
```

Run tests:

```
docker-compose -f docker-compose.test.yml build test && docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test
```

## Thoughts on solution

We would have a "order_storage" table with the following columns:

- storage_type: string
- order_id: string

We would have an "inventory" table with the following columns:

- storage_type: string
- inventory_count: int

Placing an order would insert a row into "order_storage" and increment counter in "inventory".

Discarding order would remove a row from "order_storage" and decrement counter in "inventory".

Moving order would update storage_type in "order_storage" and decrement, increment counters in "inventory".

Table modifications would be done within a transaction using the "read commited" isolation level.
We will avoid database anomalies using database constraints and triggers.

We discard orders in this orders:

1. Oldest past freshness
2. Oldest

### Consistency Assurance

We will ensure that inventory never goes out of valid values by adding constraints.

```
CREATE TABLE inventory (
    storage_type VARCHAR(20),
    inventory_count INT,
    CONSTRAINT inventory_check CHECK (
        (storage_type = 'cold' AND inventory_count >= 0 AND inventory_count <= 6) OR
        (storage_type = 'hot' AND inventory_count >= 0 AND inventory_count <= 6) OR
        (storage_type = 'shelf' AND inventory_count >= 0 AND inventory_count <= 12)
    )
);
```

We will ensure that no duplicate orders are inserted by having primary key "order_id" in "order_storage" table.

When we move and order we will ensure that order is not moved already by having making sure that storage didn't change:

```
WHERE order_id = :order_id and storage_type = :from_storage
```

- Pros:
  - Storage constraints are maintained automatically.
  - Invalid state is automatically handled by a rollback
- Cons:
  - More complex
  - The same state is stored in two places. Inventory counts can be derived from "storage" table and from "inventory" table.
