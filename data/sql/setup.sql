-- Run this once to create the whaletrip dataset and all views.
-- Replace YOUR_PROJECT_ID with your GCP project ID.
--
-- Data source: bigquery-public-data.gbif.occurrences (free public dataset)
-- Cetacea order covers all whales, dolphins, and porpoises (~90 species tracked).

CREATE SCHEMA IF NOT EXISTS `YOUR_PROJECT_ID.whaletrip`
OPTIONS (
  location = 'US',
  description = 'WhaleTrip curated whale sighting data from GBIF'
);
