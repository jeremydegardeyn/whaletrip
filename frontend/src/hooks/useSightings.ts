import useSWR from 'swr';
import { fetchSightings, fetchHeatmap, fetchSpecies, fetchFilterOptions } from '@/lib/api';
import type { SightingsFilter } from '@/types';

export function useSightings(filter: SightingsFilter & { limit?: number }) {
  const key = ['sightings', JSON.stringify(filter)];
  return useSWR(key, () => fetchSightings(filter), {
    revalidateOnFocus: false,
    dedupingInterval: 30_000,
  });
}

export function useHeatmap(month?: number, species?: string) {
  const key = ['heatmap', month, species];
  return useSWR(key, () => fetchHeatmap(month, species), {
    revalidateOnFocus: false,
    dedupingInterval: 60_000,
  });
}

export function useSpecies() {
  return useSWR('species', fetchSpecies, {
    revalidateOnFocus: false,
    dedupingInterval: 300_000,
  });
}

export function useFilterOptions() {
  return useSWR('filter-options', fetchFilterOptions, {
    revalidateOnFocus: false,
    dedupingInterval: 300_000,
  });
}
