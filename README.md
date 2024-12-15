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

Run tests:

```
docker-compose -f docker-compose.test.yml build && docker-compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test
```

## Thoughts on possible solutions

There are many ways to approach this problem.
I will describe couple of them briefly.

### RDBMS with storage and inventory tables (selected)

We would have a "order_storage" table with the following columns:

- storage_type: string
- order_id: string

We would have an "inventory" table with the following columns:

- storage_type: string
- inventory_count: int

Placing an order would insert a row into "order_storage" and increment counter in "inventory".

Discarding order would remove a row from "order_storage" and decrement counter in "inventory".

Moving order would update storage_type in "order_storage" and decrement, increment counters in "inventory".

Table modifications would be done within a transaction using the "repeatable read" isolation level to avoid "lost update" problem. To maintain storage capacity constraints and avoid phantom reads we would add inventory constraints like this:

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

In "order_storage" table order_id can be a primary key since the order can be placed to a single storage only.
Move operation is simple since we would only need to change storage_type.

- Pros:
  - Transaction isolation level is not highest thus reducing the risk of deadlocks.
  - Storage constraints are maintained automatically.
- Cons:
  - More complex
  - The same state is stored in two places. Inventory counts can be derived from "storage" table and from "inventory" table.

### RDBMS with storage table

We would have a "order_storage" table with the following columns:

- storage_type: string
- order_id: string

Placing an order would insert a row.
Discarding order would remove a row.
Moving order would update storage_type.
Storage capacity can be derived by counting the rows with a specific storage_type.
Table modifications would be done within a transaction using the serializable isolation level to maintain storage capacity constraints and avoid phantom reads.

order_id can be a primary key since the order can be placed to a single storage only.
Move operation is simple since we would only need to change storage_type.

- Pros:
  - The move operation is simple.
- Cons:
  - Serializable isolation:
    - Can cause deadlocks.
    - Counting rows can lock all rows.

### Event sourcing with arbiter

Each order event can be placed in the event log.
Application state can be derived from the event log.
Here we need an arbiter since we can have invalid events.
Example: we want to place two orders at the same time.
We read the log and see that we have one space left on the shelf.
Both orders are placed on the shelf thus exceeding maximum capacity by one (write skew).
To resolve this issue we would have an arbiter.
Arbiter would reject events that would lead to an invalid state.

- Pros:
  - Auditable.
  - Events can be replayed.
  - Easy to track application state changes.
- Cons:
  - Arbiter is a single point of failure.
