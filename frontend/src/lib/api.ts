import type { SightingsFilter, WhaleSighting, HeatmapCell, SpeciesSummary, FilterOptions } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

function buildQuery(params: Record<string, unknown>): string {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') {
      q.set(k, String(v));
    }
  }
  const s = q.toString();
  return s ? `?${s}` : '';
}

export async function fetchSightings(
  filter: SightingsFilter & { limit?: number }
): Promise<{ sightings: WhaleSighting[]; total: number }> {
  return apiFetch(`/sightings${buildQuery(filter)}`);
}

export async function fetchHeatmap(
  month?: number,
  species?: string
): Promise<{ cells: HeatmapCell[] }> {
  return apiFetch(`/sightings/heatmap${buildQuery({ month, species })}`);
}

export async function fetchSpecies(): Promise<{ species: SpeciesSummary[] }> {
  return apiFetch('/sightings/species');
}

export async function fetchFilterOptions(): Promise<FilterOptions> {
  return apiFetch('/sightings/filters/options');
}

export async function sendChatMessage(
  message: string,
  sessionId?: string,
  context?: Record<string, unknown>
): Promise<{
  session_id: string;
  message: string;
  agent?: string;
  map_actions?: Array<{ action: string; params: Record<string, unknown> }>;
  follow_up_questions?: string[];
}> {
  return apiFetch('/chat', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId, context }),
  });
}

export async function clearChatSession(sessionId: string): Promise<void> {
  await apiFetch(`/chat/session/${sessionId}`, { method: 'DELETE' });
}
