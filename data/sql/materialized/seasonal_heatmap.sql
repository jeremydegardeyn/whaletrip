-- Materialized table for seasonal heatmap data powering the map animation.
-- Pre-aggregated to 1-degree grid cells by month — avoids scanning 4M rows on every map load.
-- Replace YOUR_PROJECT_ID before running. Schedule refresh weekly via Cloud Scheduler.

CREATE OR REPLACE TABLE `YOUR_PROJECT_ID.whaletrip.seasonal_heatmap`
PARTITION BY RANGE_BUCKET(month, GENERATE_ARRAY(1, 13, 1))
CLUSTER BY ocean_basin, species
OPTIONS (
  description = 'Pre-aggregated whale sightings on 1-degree grid for map heatmap'
)
AS
SELECT
  -- Snap to 1-degree grid cells for aggregation
  ROUND(latitude)                                   AS lat_grid,
  ROUND(longitude)                                  AS lng_grid,
  month,
  species,
  ocean_basin,
  climate_zone,
  COUNT(*)                                          AS sighting_count,
  SUM(individual_count)                             AS individual_count,
  COUNT(DISTINCT year)                              AS years_observed,
  COUNT(DISTINCT country_code)                      AS country_count,
  ROUND(AVG(latitude),  4)                          AS centroid_lat,
  ROUND(AVG(longitude), 4)                          AS centroid_lng,
  ARRAY_AGG(DISTINCT season IGNORE NULLS)           AS seasons,
  CURRENT_TIMESTAMP()                               AS last_refreshed
FROM `YOUR_PROJECT_ID.whaletrip.whale_sightings`
WHERE
  month IS NOT NULL
  AND latitude  BETWEEN -90  AND 90
  AND longitude BETWEEN -180 AND 180
GROUP BY
  lat_grid, lng_grid, month, species, ocean_basin, climate_zone
HAVING sighting_count >= 1
;

-- Index-style view for fast API queries (top species per region per month)
CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.whaletrip.top_species_by_region_month` AS
SELECT
  ocean_basin,
  month,
  species,
  SUM(sighting_count)    AS total_sightings,
  SUM(individual_count)  AS total_individuals,
  ROUND(AVG(centroid_lat),  3) AS region_lat,
  ROUND(AVG(centroid_lng), 3)  AS region_lng
FROM `YOUR_PROJECT_ID.whaletrip.seasonal_heatmap`
GROUP BY ocean_basin, month, species
QUALIFY ROW_NUMBER() OVER (PARTITION BY ocean_basin, month ORDER BY SUM(sighting_count) DESC) <= 5
ORDER BY ocean_basin, month, total_sightings DESC
;
