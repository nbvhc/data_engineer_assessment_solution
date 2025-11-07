CREATE TABLE IF NOT EXISTS stg_properties_raw (
  stg_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  raw_json JSON NOT NULL,
  ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_property (
  property_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
  property_bk VARCHAR(128) NOT NULL UNIQUE,
  year_built SMALLINT NULL,
  property_type VARCHAR(64) NULL,
  square_feet INT NULL,
  bedrooms DECIMAL(4,1) NULL,
  bathrooms DECIMAL(4,1) NULL,
  lot_size_sqft INT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_address (
  address_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
  address_line1 VARCHAR(255),
  address_line2 VARCHAR(255),
  city VARCHAR(100),
  state VARCHAR(100),
  postal_code VARCHAR(20),
  county VARCHAR(100),
  country VARCHAR(100),
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6),
  UNIQUE KEY uk_address (address_line1, city, state, postal_code)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_hoa (
  hoa_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
  hoa_name VARCHAR(255),
  hoa_monthly_fee DECIMAL(10,2),
  hoa_phone VARCHAR(50),
  hoa_email VARCHAR(255),
  rules_json JSON NULL,
  UNIQUE KEY uk_hoa (hoa_name, hoa_monthly_fee)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_valuation (
  valuation_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
  provider VARCHAR(100),
  estimate DECIMAL(12,2),
  estimate_low DECIMAL(12,2),
  estimate_high DECIMAL(12,2),
  as_of_date DATE,
  UNIQUE KEY uk_val (provider, as_of_date, estimate, estimate_low, estimate_high)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_rehab (
  rehab_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
  total_estimate DECIMAL(12,2),
  exterior DECIMAL(12,2),
  interior DECIMAL(12,2),
  systems DECIMAL(12,2),
  as_of_date DATE,
  UNIQUE KEY uk_rehab (as_of_date, total_estimate, exterior, interior, systems)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_tax (
  tax_sk BIGINT AUTO_INCREMENT PRIMARY KEY,
  tax_year SMALLINT,
  assessed_value DECIMAL(12,2),
  tax_amount DECIMAL(12,2),
  UNIQUE KEY uk_tax (tax_year, assessed_value, tax_amount)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_property_snapshot (
  snapshot_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  property_sk BIGINT NOT NULL,
  address_sk BIGINT NOT NULL,
  hoa_sk BIGINT NULL,
  valuation_sk BIGINT NULL,
  rehab_sk BIGINT NULL,
  tax_sk BIGINT NULL,
  effective_date DATE NOT NULL,
  source_record_id BIGINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_prop  FOREIGN KEY (property_sk)  REFERENCES dim_property(property_sk),
  CONSTRAINT fk_addr  FOREIGN KEY (address_sk)   REFERENCES dim_address(address_sk),
  CONSTRAINT fk_hoa   FOREIGN KEY (hoa_sk)       REFERENCES dim_hoa(hoa_sk),
  CONSTRAINT fk_val   FOREIGN KEY (valuation_sk) REFERENCES dim_valuation(valuation_sk),
  CONSTRAINT fk_rehab FOREIGN KEY (rehab_sk)     REFERENCES dim_rehab(rehab_sk),
  CONSTRAINT fk_tax   FOREIGN KEY (tax_sk)       REFERENCES dim_tax(tax_sk)
) ENGINE=InnoDB;
