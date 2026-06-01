-- Core whale sightings view built on GBIF public dataset.
-- Replace YOUR_PROJECT_ID before running.
--
-- GBIF occurrences table has ~2B rows; the WHERE clause filters to ~4M cetacean records.
-- This view is the foundation for all map and agent queries.

CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.whaletrip.whale_sightings` AS
SELECT
  CAST(gbifid AS STRING)                                              AS sighting_id,
  COALESCE(species, genus, family, 'Unknown Cetacean')               AS species,
  genus,
  family,
  CAST(decimallatitude AS FLOAT64)                                   AS latitude,
  CAST(decimallongitude AS FLOAT64)                                  AS longitude,

  -- Robust date parsing — GBIF eventdate is inconsistently formatted
  SAFE.PARSE_DATE('%Y-%m-%d', SUBSTR(SAFE_CAST(eventdate AS STRING), 1, 10)) AS observation_date,
  SAFE_CAST(SUBSTR(SAFE_CAST(eventdate AS STRING), 1, 4) AS INT64)   AS year,
  SAFE_CAST(
    SUBSTR(SAFE_CAST(eventdate AS STRING), 6, 2) AS INT64
  )                                                                   AS month,

  countrycode                                                         AS country_code,
  COALESCE(stateprovince, countrycode)                               AS region,
  datasetname                                                         AS observation_source,
  COALESCE(SAFE_CAST(individualcount AS INT64), 1)                   AS individual_count,
  occurrencestatus                                                    AS status,

  -- Derived geographic zones for filtering
  CASE
    WHEN CAST(decimallatitude AS FLOAT64) > 66.5  THEN 'Arctic'
    WHEN CAST(decimallatitude AS FLOAT64) > 23.5  THEN 'North Temperate'
    WHEN CAST(decimallatitude AS FLOAT64) > -23.5 THEN 'Tropical'
    WHEN CAST(decimallatitude AS FLOAT64) > -66.5 THEN 'South Temperate'
    ELSE                                                'Antarctic'
  END AS climate_zone,

  CASE
    WHEN CAST(decimallongitude AS FLOAT64) BETWEEN -180 AND -100 THEN 'Eastern Pacific'
    WHEN CAST(decimallongitude AS FLOAT64) BETWEEN -100 AND -30  THEN 'Western Atlantic'
    WHEN CAST(decimallongitude AS FLOAT64) BETWEEN -30  AND 20   THEN 'Eastern Atlantic'
    WHEN CAST(decimallongitude AS FLOAT64) BETWEEN 20   AND 80   THEN 'Indian Ocean'
    WHEN CAST(decimallongitude AS FLOAT64) BETWEEN 80   AND 180  THEN 'Western Pacific'
    ELSE                                                               'Unknown'
  END AS ocean_basin,

  -- Season derived from month (Northern Hemisphere convention)
  CASE
    WHEN SAFE_CAST(SUBSTR(SAFE_CAST(eventdate AS STRING), 6, 2) AS INT64) IN (12, 1, 2) THEN 'Winter'
    WHEN SAFE_CAST(SUBSTR(SAFE_CAST(eventdate AS STRING), 6, 2) AS INT64) IN (3, 4, 5)  THEN 'Spring'
    WHEN SAFE_CAST(SUBSTR(SAFE_CAST(eventdate AS STRING), 6, 2) AS INT64) IN (6, 7, 8)  THEN 'Summer'
    ELSE 'Autumn'
  END AS season

FROM `bigquery-public-data.gbif.occurrences`
WHERE
  class = 'Mammalia'
  AND `order` = 'Cetacea'
  AND decimallatitude  IS NOT NULL
  AND decimallongitude IS NOT NULL
  AND occurrencestatus = 'PRESENT'
  AND SAFE_CAST(decimallatitude  AS FLOAT64) BETWEEN -90  AND 90
  AND SAFE_CAST(decimallongitude AS FLOAT64) BETWEEN -180 AND 180
  AND species IS NOT NULL
;
