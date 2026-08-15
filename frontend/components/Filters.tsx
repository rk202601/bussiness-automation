/**
 * Filters — Composable filter controls for leads.
 * All filters use AND logic.
 */

"use client";

import { STATUS_OPTIONS } from "@/lib/firestore";

export interface FilterState {
  state: string;
  area: string;
  status: string;
  keyword: string;
}

interface FiltersProps {
  filters: FilterState;
  onChange: (filters: FilterState) => void;
  availableStates: string[];
  availableAreas: string[];
}

export default function Filters({
  filters,
  onChange,
  availableStates,
  availableAreas,
}: FiltersProps) {
  const update = (key: keyof FilterState, value: string) => {
    onChange({ ...filters, [key]: value });
  };

  const hasActiveFilters =
    filters.state || filters.area || filters.status || filters.keyword;

  const clearAll = () => {
    onChange({ state: "", area: "", status: "", keyword: "" });
  };

  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* State filter */}
      <select
        id="filter-state"
        value={filters.state}
        onChange={(e) => update("state", e.target.value)}
        className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors cursor-pointer appearance-none min-w-[130px]"
      >
        <option value="" className="bg-[#1a1b23]">All States</option>
        {availableStates.map((s) => (
          <option key={s} value={s} className="bg-[#1a1b23]">{s}</option>
        ))}
      </select>

      {/* Area / City filter */}
      <select
        id="filter-area"
        value={filters.area}
        onChange={(e) => update("area", e.target.value)}
        className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors cursor-pointer appearance-none min-w-[130px]"
      >
        <option value="" className="bg-[#1a1b23]">All Cities</option>
        {availableAreas.map((a) => (
          <option key={a} value={a} className="bg-[#1a1b23]">{a}</option>
        ))}
      </select>

      {/* Status filter */}
      <select
        id="filter-status"
        value={filters.status}
        onChange={(e) => update("status", e.target.value)}
        className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors cursor-pointer appearance-none min-w-[150px]"
      >
        <option value="" className="bg-[#1a1b23]">All Statuses</option>
        {STATUS_OPTIONS.map((s) => (
          <option key={s} value={s} className="bg-[#1a1b23]">{s}</option>
        ))}
      </select>

      {/* Keyword filter */}
      <input
        id="filter-keyword"
        type="text"
        placeholder="Keyword..."
        value={filters.keyword}
        onChange={(e) => update("keyword", e.target.value)}
        className="px-3 py-2 bg-white/[0.04] border border-white/[0.08] rounded-lg text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-blue-500/50 transition-colors w-32"
      />

      {/* Clear all */}
      {hasActiveFilters && (
        <button
          onClick={clearAll}
          className="px-3 py-2 text-xs font-medium text-white/50 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] rounded-lg transition-all"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}
