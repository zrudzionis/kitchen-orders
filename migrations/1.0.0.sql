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
    order_name VARCHAR(150),
    best_storage_type VARCHAR(20),
    fresh_max_age BIGINT DEFAULT 0,
    storage_type VARCHAR(20),
    cumulative_age BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT storage_type_check CHECK (storage_type IN ('hot', 'cold', 'shelf')),
    CONSTRAINT best_storage_type_check CHECK (best_storage_type IN ('hot', 'cold', 'shelf'))
);

CREATE OR REPLACE FUNCTION update_order_age()
RETURNS TRIGGER AS $$
BEGIN
    NEW.cumulative_age = NEW.cumulative_age +
        CASE
            WHEN OLD.storage_type = OLD.best_storage_type THEN
                EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - OLD.updated_at))
            ELSE
                2 * EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - OLD.updated_at))
        END;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_age_trigger
BEFORE UPDATE ON order_storage
FOR EACH ROW
EXECUTE FUNCTION update_order_age();


CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_order_storage_updated_at
AFTER UPDATE ON order_storage
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
