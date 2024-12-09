# Kitchen Orders

## Thoughts on possible solutions

There are many ways to approach this problem.
I will describe couple of them briefly.

### RDBMS with storage and inventory tables (selected)
We would have a "order_storage" table with the following columns:
* storage_type: string
* order_id: string

We would have an "inventory" table with the following columns:
* storage_type: string
* inventory_count: int

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

* Pros:
    * Transaction isolation level is not highest thus reducing the risk of deadlocks.
    * Storage constraints are maintained automatically.
* Cons:
  * More complex
  * The same state is stored in two places. Inventory counts can be derived from "storage" table and from "inventory" table.


### RDBMS with storage table
We would have a "order_storage" table with the following columns:
* storage_type: string
* order_id: string

Placing an order would insert a row.
Discarding order would remove a row.
Moving order would update storage_type.
Storage capacity can be derived by counting the rows with a specific storage_type.
Table modifications would be done within a transaction using the serializable isolation level to maintain storage capacity constraints and avoid phantom reads.

order_id can be a primary key since the order can be placed to a single storage only.
Move operation is simple since we would only need to change storage_type.

* Pros:
    * The move operation is simple.
* Cons:
    * Serializable isolation:
        * Can cause deadlocks.
        * Counting rows can lock all rows.


### Event sourcing with arbiter
Each order event can be placed in the event log.
Application state can be derived from the event log.
Here we need an arbiter since we can have invalid events.
Example: we want to place two orders at the same time.
We read the log and see that we have one space left on the shelf.
Both orders are placed on the shelf thus exceeding maximum capacity by one (write skew).
To resolve this issue we would have an arbiter.
Arbiter would reject events that would lead to an invalid state.

* Pros:
    * Auditable.
    * Events can be replayed.
    * Easy to track application state changes.
* Cons:
    * Arbiter is a single point of failure.
