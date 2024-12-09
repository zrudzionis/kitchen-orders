CREATE TABLE inventory (
    storage_type VARCHAR(20) PRIMARY KEY,
    inventory_count INT,
    CONSTRAINT inventory_check CHECK (
        (storage_type = 'hot' AND inventory_count >= 0 AND inventory_count <= 6) OR
        (storage_type = 'cold' AND inventory_count >= 0 AND inventory_count <= 6) OR
        (storage_type = 'shelf' AND inventory_count >= 0 AND inventory_count <= 12)
    )
);

INSERT INTO inventory (storage_type, inventory_count) VALUES ('hot', 0);
INSERT INTO inventory (storage_type, inventory_count) VALUES ('cold', 0);
INSERT INTO inventory (storage_type, inventory_count) VALUES ('shelf', 0);

CREATE TABLE order_storage (
    order_id VARCHAR(50) PRIMARY KEY,
    storage_type VARCHAR(20),
    CONSTRAINT storage_type_check CHECK (storage_type IN ('hot', 'cold', 'shelf'))
);
