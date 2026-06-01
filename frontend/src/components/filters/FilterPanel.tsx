'use client';

import { useState } from 'react';
import { clsx } from 'clsx';
import { useFilterOptions, useSpecies } from '@/hooks/useSightings';
import type { SightingsFilter } from '@/types';

interface Props {
  filter: SightingsFilter;
  onChange: (f: SightingsFilter) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function FilterPanel({ filter, onChange, isOpen, onClose }: Props) {
  const { data: options } = useFilterOptions();
  const { data: speciesData } = useSpecies();
  const [localFilter, setLocalFilter] = useState<SightingsFilter>(filter);

  function apply() {
    onChange(localFilter);
    onClose();
  }

  function reset() {
    const empty: SightingsFilter = {};
    setLocalFilter(empty);
    onChange(empty);
    onClose();
  }

  function patch(update: Partial<SightingsFilter>) {
    setLocalFilter((prev) => ({ ...prev, ...update }));
  }

  if (!isOpen) return null;

  return (
    <div className="absolute top-0 right-0 h-full w-80 bg-ocean-950/98 border-l border-ocean-800 z-20 flex flex-col shadow-2xl">
      <div className="flex items-center justify-between p-4 border-b border-ocean-800">
        <h2 className="text-white font-semibold">Filter Sightings</h2>
        <button onClick={onClose} className="text-ocean-400 hover:text-white text-xl">×</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Species */}
        <div>
          <label className="block text-xs text-ocean-400 mb-1.5 uppercase tracking-wide">Species</label>
          <select
            value={localFilter.species ?? ''}
            onChange={(e) => patch({ species: e.target.value || undefined })}
            className="w-full bg-ocean-900 border border-ocean-700 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="">All species</option>
            {speciesData?.species.slice(0, 50).map((s) => (
              <option key={s.species} value={s.species}>{s.species}</option>
            ))}
          </select>
        </div>

        {/* Month */}
        <div>
          <label className="block text-xs text-ocean-400 mb-1.5 uppercase tracking-wide">Month</label>
          <div className="grid grid-cols-4 gap-1">
            {options?.months.map((m) => (
              <button
                key={m.value}
                onClick={() => patch({ month: localFilter.month === m.value ? undefined : m.value })}
                className={clsx(
                  'py-1.5 rounded text-xs transition-colors',
                  localFilter.month === m.value
                    ? 'bg-ocean-500 text-white'
                    : 'bg-ocean-800 text-ocean-300 hover:bg-ocean-700'
                )}
              >
                {m.label.slice(0, 3)}
              </button>
            ))}
          </div>
        </div>

        {/* Ocean Basin */}
        <div>
          <label className="block text-xs text-ocean-400 mb-1.5 uppercase tracking-wide">Ocean Basin</label>
          <div className="space-y-1">
            {options?.ocean_basins.map((b) => (
              <button
                key={b}
                onClick={() => patch({ ocean_basin: localFilter.ocean_basin === b ? undefined : b })}
                className={clsx(
                  'w-full text-left px-3 py-1.5 rounded text-xs transition-colors',
                  localFilter.ocean_basin === b
                    ? 'bg-ocean-500 text-white'
                    : 'bg-ocean-800 text-ocean-300 hover:bg-ocean-700'
                )}
              >
                {b}
              </button>
            ))}
          </div>
        </div>

        {/* Climate Zone */}
        <div>
          <label className="block text-xs text-ocean-400 mb-1.5 uppercase tracking-wide">Climate Zone</label>
          <div className="space-y-1">
            {options?.climate_zones.map((z) => (
              <button
                key={z}
                onClick={() => patch({ climate_zone: localFilter.climate_zone === z ? undefined : z })}
                className={clsx(
                  'w-full text-left px-3 py-1.5 rounded text-xs transition-colors',
                  localFilter.climate_zone === z
                    ? 'bg-ocean-500 text-white'
                    : 'bg-ocean-800 text-ocean-300 hover:bg-ocean-700'
                )}
              >
                {z}
              </button>
            ))}
          </div>
        </div>

        {/* Year range */}
        <div>
          <label className="block text-xs text-ocean-400 mb-1.5 uppercase tracking-wide">Year Range</label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="From"
              min={1900}
              max={2030}
              value={localFilter.year_min ?? ''}
              onChange={(e) => patch({ year_min: e.target.value ? Number(e.target.value) : undefined })}
              className="w-full bg-ocean-900 border border-ocean-700 rounded px-3 py-2 text-sm text-white"
            />
            <input
              type="number"
              placeholder="To"
              min={1900}
              max={2030}
              value={localFilter.year_max ?? ''}
              onChange={(e) => patch({ year_max: e.target.value ? Number(e.target.value) : undefined })}
              className="w-full bg-ocean-900 border border-ocean-700 rounded px-3 py-2 text-sm text-white"
            />
          </div>
        </div>
      </div>

      <div className="p-4 border-t border-ocean-800 flex gap-2">
        <button
          onClick={reset}
          className="flex-1 py-2 rounded-lg border border-ocean-700 text-ocean-300 text-sm hover:bg-ocean-800 transition-colors"
        >
          Reset
        </button>
        <button
          onClick={apply}
          className="flex-1 py-2 rounded-lg bg-ocean-600 text-white text-sm font-medium hover:bg-ocean-500 transition-colors"
        >
          Apply
        </button>
      </div>
    </div>
  );
}
