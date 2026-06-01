'use client';

import { useState, useCallback, useMemo } from 'react';
import Map, { NavigationControl, ScaleControl } from 'react-map-gl/maplibre';
import { DeckGL } from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HexagonLayer } from '@deck.gl/aggregation-layers';
import type { PickingInfo } from '@deck.gl/core';
import 'maplibre-gl/dist/maplibre-gl.css';

import { SightingTooltip } from './SightingTooltip';
import type { WhaleSighting, HeatmapCell } from '@/types';

const CARTO_DARK_TILES = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
const CARTO_LIGHT_TILES = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

const INITIAL_VIEW = {
  longitude: 0,
  latitude: 20,
  zoom: 1.8,
  pitch: 0,
  bearing: 0,
};

// Species → colour mapping (ocean palette)
const SPECIES_COLORS: Record<string, [number, number, number]> = {
  'Balaenoptera musculus':    [0,   149, 255],  // blue whale → blue
  'Megaptera novaeangliae':   [0,   220, 160],  // humpback → teal
  'Physeter macrocephalus':   [160, 80,  220],  // sperm whale → purple
  'Eschrichtius robustus':    [255, 180, 0],    // gray whale → amber
  'Orcinus orca':             [255, 255, 255],  // orca → white
  'Eubalaena australis':      [255, 100, 100],  // southern right → coral
  'Delphinapterus leucas':    [200, 240, 255],  // beluga → ice blue
};

const DEFAULT_COLOR: [number, number, number] = [0, 180, 220];

function speciesColor(species: string): [number, number, number] {
  for (const [key, color] of Object.entries(SPECIES_COLORS)) {
    if (species.toLowerCase().includes(key.split(' ')[1]?.toLowerCase() ?? '')) return color;
  }
  return DEFAULT_COLOR;
}

interface Props {
  sightings: WhaleSighting[];
  heatmapCells: HeatmapCell[];
  viewMode: 'scatter' | 'heatmap' | 'hex';
  selectedSighting: WhaleSighting | null;
  onSelectSighting: (s: WhaleSighting | null) => void;
}

export function WhaleMap({
  sightings,
  heatmapCells,
  viewMode,
  selectedSighting,
  onSelectSighting,
}: Props) {
  const [hoverInfo, setHoverInfo] = useState<{ x: number; y: number; object: WhaleSighting } | null>(null);
  const [viewState, setViewState] = useState(INITIAL_VIEW);

  const scatterLayer = useMemo(
    () =>
      new ScatterplotLayer<WhaleSighting>({
        id: 'whale-scatter',
        data: sightings,
        visible: viewMode === 'scatter',
        getPosition: (d) => [d.longitude, d.latitude],
        getRadius: (d) => Math.sqrt(d.individual_count) * 8000 + 4000,
        radiusMinPixels: 3,
        radiusMaxPixels: 18,
        getFillColor: (d) => [...speciesColor(d.species), 180],
        getLineColor: [255, 255, 255, 60],
        lineWidthMinPixels: 0.5,
        stroked: true,
        pickable: true,
        onHover: ({ x, y, object }: PickingInfo<WhaleSighting>) => {
          setHoverInfo(object ? { x, y, object } : null);
        },
        onClick: ({ object }: PickingInfo<WhaleSighting>) => {
          if (object) onSelectSighting(object);
        },
        updateTriggers: { getPosition: sightings, getFillColor: sightings },
      }),
    [sightings, viewMode, onSelectSighting]
  );

  const hexLayer = useMemo(
    () =>
      new HexagonLayer<WhaleSighting>({
        id: 'whale-hex',
        data: sightings,
        visible: viewMode === 'hex',
        getPosition: (d) => [d.longitude, d.latitude],
        radius: 80000,
        elevationScale: 4,
        extruded: true,
        pickable: true,
        opacity: 0.6,
        colorRange: [
          [1, 152, 189],
          [73, 227, 206],
          [216, 254, 181],
          [254, 237, 177],
          [254, 173, 84],
          [209, 55,  78],
        ],
        updateTriggers: { getPosition: sightings },
      }),
    [sightings, viewMode]
  );

  const heatmapScatter = useMemo(
    () =>
      new ScatterplotLayer<HeatmapCell>({
        id: 'heatmap-scatter',
        data: heatmapCells,
        visible: viewMode === 'heatmap',
        getPosition: (d) => [d.centroid_lng, d.centroid_lat],
        getRadius: (d) => Math.sqrt(d.sighting_count) * 15000,
        radiusMinPixels: 4,
        radiusMaxPixels: 40,
        getFillColor: (d) => {
          const intensity = Math.min(d.sighting_count / 100, 1);
          return [
            Math.round(255 * intensity),
            Math.round(100 * (1 - intensity)),
            Math.round(200 * (1 - intensity)),
            160,
          ];
        },
        pickable: false,
        updateTriggers: { getPosition: heatmapCells },
      }),
    [heatmapCells, viewMode]
  );

  const layers = [scatterLayer, hexLayer, heatmapScatter];

  return (
    <div className="relative w-full h-full">
      <DeckGL
        viewState={viewState}
        controller
        layers={layers}
        onViewStateChange={({ viewState: vs }) => setViewState(vs as typeof INITIAL_VIEW)}
        style={{ position: 'absolute', inset: '0' }}
      >
        <Map
          mapStyle={CARTO_DARK_TILES}
          attributionControl={false}
        >
          <NavigationControl position="top-right" />
          <ScaleControl position="bottom-right" />
        </Map>
      </DeckGL>

      {hoverInfo && (
        <SightingTooltip x={hoverInfo.x} y={hoverInfo.y} sighting={hoverInfo.object} />
      )}

      {selectedSighting && (
        <div className="absolute bottom-6 left-6 right-6 md:right-auto md:w-96 bg-ocean-950/95 border border-ocean-700 rounded-xl p-4 shadow-2xl text-white">
          <div className="flex justify-between items-start mb-2">
            <h3 className="font-semibold text-ocean-300 text-sm">{selectedSighting.species}</h3>
            <button
              onClick={() => onSelectSighting(null)}
              className="text-ocean-500 hover:text-white text-lg leading-none"
            >
              ×
            </button>
          </div>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {selectedSighting.observation_date && (
              <><dt className="text-ocean-400">Date</dt><dd>{selectedSighting.observation_date}</dd></>
            )}
            <dt className="text-ocean-400">Latitude</dt>
            <dd>{selectedSighting.latitude.toFixed(4)}°</dd>
            <dt className="text-ocean-400">Longitude</dt>
            <dd>{selectedSighting.longitude.toFixed(4)}°</dd>
            {selectedSighting.region && (
              <><dt className="text-ocean-400">Region</dt><dd>{selectedSighting.region}</dd></>
            )}
            {selectedSighting.ocean_basin && (
              <><dt className="text-ocean-400">Ocean</dt><dd>{selectedSighting.ocean_basin}</dd></>
            )}
            {selectedSighting.individual_count > 1 && (
              <><dt className="text-ocean-400">Count</dt><dd>{selectedSighting.individual_count}</dd></>
            )}
            {selectedSighting.observation_source && (
              <><dt className="text-ocean-400 col-span-1">Source</dt>
              <dd className="truncate">{selectedSighting.observation_source}</dd></>
            )}
          </dl>
        </div>
      )}
    </div>
  );
}
