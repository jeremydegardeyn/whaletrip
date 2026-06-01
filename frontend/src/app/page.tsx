'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import { MapControls } from '@/components/map/MapControls';
import { FilterPanel } from '@/components/filters/FilterPanel';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { useSightings, useHeatmap } from '@/hooks/useSightings';
import type { SightingsFilter, WhaleSighting, MapAction } from '@/types';

// Dynamically import map to avoid SSR issues with WebGL
const WhaleMap = dynamic(
  () => import('@/components/map/WhaleMap').then((m) => m.WhaleMap),
  { ssr: false, loading: () => <div className="w-full h-full bg-ocean-950 animate-pulse" /> }
);

type ViewMode = 'scatter' | 'heatmap' | 'hex';

export default function HomePage() {
  const [filter, setFilter] = useState<SightingsFilter>({});
  const [viewMode, setViewMode] = useState<ViewMode>('scatter');
  const [selectedSighting, setSelectedSighting] = useState<WhaleSighting | null>(null);
  const [filterPanelOpen, setFilterPanelOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [playbackMonth, setPlaybackMonth] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const playbackRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const activeMonth = playbackMonth ?? filter.month;

  const { data: sightingsData } = useSightings({
    ...filter,
    month: activeMonth,
    limit: 8000,
  });

  const { data: heatmapData } = useHeatmap(activeMonth, filter.species);

  // Migration playback animation
  useEffect(() => {
    if (isPlaying) {
      playbackRef.current = setInterval(() => {
        setPlaybackMonth((m) => ((m ?? 0) % 12) + 1);
      }, 1200);
    } else {
      if (playbackRef.current) clearInterval(playbackRef.current);
    }
    return () => {
      if (playbackRef.current) clearInterval(playbackRef.current);
    };
  }, [isPlaying]);

  const handleMapAction = useCallback((actions: MapAction[]) => {
    for (const action of actions) {
      if (action.action === 'filter') {
        setFilter((prev) => ({ ...prev, ...action.params }));
      }
    }
  }, []);

  const mapContext = {
    current_filter: filter,
    active_month: activeMonth,
    sightings_visible: sightingsData?.total ?? 0,
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-ocean-950">
      {/* Map fills the viewport */}
      <div className="absolute inset-0">
        <WhaleMap
          sightings={sightingsData?.sightings ?? []}
          heatmapCells={heatmapData?.cells ?? []}
          viewMode={viewMode}
          selectedSighting={selectedSighting}
          onSelectSighting={setSelectedSighting}
        />
      </div>

      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-3 bg-gradient-to-b from-ocean-950/80 to-transparent pointer-events-none">
        <div className="pointer-events-auto">
          <h1 className="text-white font-bold text-lg tracking-tight">🐋 WhaleTrip</h1>
          <p className="text-ocean-400 text-xs">Global whale sighting explorer</p>
        </div>
        <div className="flex gap-2 pointer-events-auto">
          <button
            onClick={() => setFilterPanelOpen(true)}
            className="bg-ocean-900/90 border border-ocean-700 text-ocean-300 hover:text-white text-xs px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
          >
            <span>⚙</span> Filters
            {Object.keys(filter).length > 0 && (
              <span className="bg-ocean-500 text-white rounded-full w-4 h-4 text-[10px] flex items-center justify-center">
                {Object.keys(filter).length}
              </span>
            )}
          </button>
          <button
            onClick={() => setChatOpen((v) => !v)}
            className="bg-ocean-600 hover:bg-ocean-500 text-white text-xs px-3 py-1.5 rounded-lg transition-colors"
          >
            {chatOpen ? 'Hide Chat' : '🐋 AI Planner'}
          </button>
        </div>
      </div>

      {/* Map controls */}
      <MapControls
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        playbackMonth={playbackMonth}
        onPlaybackMonthChange={setPlaybackMonth}
        isPlaying={isPlaying}
        onTogglePlay={() => setIsPlaying((v) => !v)}
        sightingCount={sightingsData?.total ?? 0}
      />

      {/* Filter panel */}
      <FilterPanel
        filter={filter}
        onChange={setFilter}
        isOpen={filterPanelOpen}
        onClose={() => setFilterPanelOpen(false)}
      />

      {/* Chat panel */}
      <ChatPanel
        onMapAction={handleMapAction}
        mapContext={mapContext}
        isOpen={chatOpen}
        onToggle={() => setChatOpen((v) => !v)}
      />

      {/* Attribution */}
      <div className="absolute bottom-2 left-2 text-[10px] text-ocean-600 pointer-events-none">
        Data: GBIF • Map: CARTO/OpenStreetMap
      </div>
    </div>
  );
}
