import type { WhaleSighting } from '@/types';

interface Props {
  x: number;
  y: number;
  sighting: WhaleSighting;
}

export function SightingTooltip({ x, y, sighting }: Props) {
  return (
    <div
      className="absolute z-50 pointer-events-none bg-ocean-950/95 border border-ocean-600 rounded-lg px-3 py-2 text-xs text-white shadow-xl max-w-xs"
      style={{ left: x + 12, top: y + 12 }}
    >
      <p className="font-semibold text-ocean-300 mb-1">{sighting.species}</p>
      {sighting.observation_date && (
        <p className="text-ocean-400">{sighting.observation_date}</p>
      )}
      <p>{sighting.latitude.toFixed(3)}°, {sighting.longitude.toFixed(3)}°</p>
      {sighting.region && <p className="text-ocean-400">{sighting.region}</p>}
      {sighting.ocean_basin && <p className="text-ocean-500">{sighting.ocean_basin}</p>}
      {sighting.individual_count > 1 && (
        <p className="text-ocean-300">{sighting.individual_count} individuals</p>
      )}
    </div>
  );
}
