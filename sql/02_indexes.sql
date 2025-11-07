CREATE INDEX ix_fact_prop ON fact_property_snapshot (property_sk, effective_date);
CREATE INDEX ix_dim_address_postal ON dim_address (postal_code);
CREATE INDEX ix_dim_property_bk ON dim_property (property_bk);
CREATE INDEX ix_dim_address_city_state ON dim_address (city, state);
