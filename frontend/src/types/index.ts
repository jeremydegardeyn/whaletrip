export interface WhaleSighting {
  sighting_id: string;
  species: string;
  genus?: string;
  latitude: number;
  longitude: number;
  observation_date?: string;
  year?: number;
  month?: number;
  country_code?: string;
  region?: string;
  observation_source?: string;
  individual_count: number;
  ocean_basin?: string;
  climate_zone?: string;
  season?: string;
}

export interface HeatmapCell {
  lat_grid: number;
  lng_grid: number;
  month: number;
  species: string;
  ocean_basin?: string;
  sighting_count: number;
  individual_count: number;
  centroid_lat: number;
  centroid_lng: number;
}

export interface SpeciesSummary {
  species: string;
  total_sightings: number;
  total_individuals: number;
  avg_latitude: number;
  avg_longitude: number;
  ocean_basins: string;
  active_months_count: number;
  countries_count: number;
}

export interface SightingsFilter {
  species?: string;
  month?: number;
  ocean_basin?: string;
  climate_zone?: string;
  year_min?: number;
  year_max?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp: Date;
  mapActions?: MapAction[];
  followUpQuestions?: string[];
}

export interface MapAction {
  action: 'filter' | 'zoom' | 'highlight';
  params: Partial<SightingsFilter> & { lat?: number; lng?: number; zoom?: number };
}

export interface FilterOptions {
  ocean_basins: string[];
  climate_zones: string[];
  months: Array<{ value: number; label: string }>;
}
