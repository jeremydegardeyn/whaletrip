-- Species-level summary with peak months and top locations.
-- Used by the Whale Intelligence Agent for species knowledge queries.
-- Replace YOUR_PROJECT_ID before running.

CREATE OR REPLACE VIEW `YOUR_PROJECT_ID.whaletrip.species_summary` AS
WITH monthly_counts AS (
  SELECT
    species,
    month,
    ocean_basin,
    COUNT(*) AS sighting_count
  FROM `YOUR_PROJECT_ID.whaletrip.whale_sightings`
  WHERE month IS NOT NULL
  GROUP BY species, month, ocean_basin
),
species_stats AS (
  SELECT
    species,
    SUM(individual_count)                                  AS total_individuals,
    COUNT(*)                                               AS total_sightings,
    ROUND(AVG(latitude),  2)                               AS avg_latitude,
    ROUND(AVG(longitude), 2)                               AS avg_longitude,
    MIN(year)                                              AS earliest_record,
    MAX(year)                                              AS latest_record,
    COUNT(DISTINCT ocean_basin)                            AS ocean_basins_count,
    COUNT(DISTINCT country_code)                           AS countries_count,
    STRING_AGG(DISTINCT ocean_basin, ', ' ORDER BY ocean_basin) AS ocean_basins,
    COUNT(DISTINCT CAST(month AS STRING))                  AS active_months_count
  FROM `YOUR_PROJECT_ID.whaletrip.whale_sightings`
  GROUP BY species
),
peak_months AS (
  SELECT
    species,
    ARRAY_AGG(
      STRUCT(month, sighting_count, ocean_basin)
      ORDER BY sighting_count DESC
      LIMIT 3
    ) AS top_months_by_basin
  FROM monthly_counts
  GROUP BY species
)
SELECT
  s.species,
  s.total_individuals,
  s.total_sightings,
  s.avg_latitude,
  s.avg_longitude,
  s.earliest_record,
  s.latest_record,
  s.ocean_basins,
  s.ocean_basins_count,
  s.countries_count,
  s.active_months_count,
  p.top_months_by_basin
FROM species_stats s
JOIN peak_months p USING (species)
WHERE s.total_sightings >= 10
ORDER BY s.total_sightings DESC
;
