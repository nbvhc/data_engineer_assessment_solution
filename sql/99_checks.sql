SELECT COUNT(*) AS raw_rows FROM stg_properties_raw;
SELECT COUNT(*) AS properties FROM dim_property;
SELECT COUNT(*) AS facts FROM fact_property_snapshot;

SELECT COUNT(*) AS bad_addr FROM fact_property_snapshot WHERE address_sk IS NULL;

SELECT COUNT(*) AS val_mismatch
FROM fact_property_snapshot fps
LEFT JOIN dim_valuation v ON v.valuation_sk = fps.valuation_sk
WHERE (fps.valuation_sk IS NOT NULL) AND (v.provider IS NULL);
