'use client';

import { clsx } from 'clsx';

type ViewMode = 'scatter' | 'heatmap' | 'hex';

interface Props {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  playbackMonth: number | null;
  onPlaybackMonthChange: (month: number | null) => void;
  isPlaying: boolean;
  onTogglePlay: () => void;
  sightingCount: number;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function MapControls({
  viewMode,
  onViewModeChange,
  playbackMonth,
  onPlaybackMonthChange,
  isPlaying,
  onTogglePlay,
  sightingCount,
}: Props) {
  return (
    <div className="absolute top-4 left-4 flex flex-col gap-2 z-10">
      {/* View mode toggle */}
      <div className="flex rounded-lg overflow-hidden shadow-lg border border-ocean-700">
        {(['scatter', 'heatmap', 'hex'] as ViewMode[]).map((mode) => (
          <button
            key={mode}
            onClick={() => onViewModeChange(mode)}
            className={clsx(
              'px-3 py-1.5 text-xs font-medium capitalize transition-colors',
              viewMode === mode
                ? 'bg-ocean-600 text-white'
                : 'bg-ocean-950/90 text-ocean-300 hover:bg-ocean-800'
            )}
          >
            {mode}
          </button>
        ))}
      </div>

      {/* Month playback */}
      <div className="bg-ocean-950/90 border border-ocean-700 rounded-lg p-3 shadow-lg min-w-56">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-ocean-400 font-medium">Migration Playback</span>
          <button
            onClick={onTogglePlay}
            className="text-xs px-2 py-0.5 rounded bg-ocean-700 hover:bg-ocean-600 text-white transition-colors"
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
        </div>
        <div className="flex gap-0.5 mb-1">
          {MONTHS.map((label, idx) => (
            <button
              key={label}
              onClick={() => onPlaybackMonthChange(playbackMonth === idx + 1 ? null : idx + 1)}
              className={clsx(
                'flex-1 text-[9px] py-1 rounded transition-colors',
                playbackMonth === idx + 1
                  ? 'bg-ocean-500 text-white'
                  : 'bg-ocean-800 text-ocean-400 hover:bg-ocean-700'
              )}
              title={label}
            >
              {label[0]}
            </button>
          ))}
        </div>
        {playbackMonth && (
          <p className="text-xs text-ocean-300 text-center">
            {MONTHS[playbackMonth - 1]} — {sightingCount.toLocaleString()} sightings
          </p>
        )}
        {!playbackMonth && (
          <p className="text-xs text-ocean-500 text-center">
            All months — {sightingCount.toLocaleString()} sightings
          </p>
        )}
      </div>
    </div>
  );
}
