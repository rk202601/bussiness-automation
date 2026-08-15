/**
 * Leads Dashboard — Main page for viewing and managing leads.
 *
 * Fetches all leads from Firestore on mount, then provides
 * client-side filtering, search, and inline status editing.
 */

"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import StatsBar from "@/components/StatsBar";
import SearchBar from "@/components/SearchBar";
import Filters, { FilterState } from "@/components/Filters";
import LeadsTable from "@/components/LeadsTable";
import { Lead, getAllLeads } from "@/lib/firestore";

export default function LeadsPage() {
  // ── State ─────────────────────────────────────────────
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState<FilterState>({
    state: "",
    area: "",
    status: "",
    keyword: "",
  });

  // ── Fetch leads on mount ──────────────────────────────
  useEffect(() => {
    async function fetchLeads() {
      try {
        setLoading(true);
        setError(null);
        const data = await getAllLeads();
        setLeads(data);
      } catch (err) {
        console.error("Failed to fetch leads:", err);
        setError(
          "Failed to load leads from Firestore. Check your Firebase config in .env.local and Firestore security rules."
        );
      } finally {
        setLoading(false);
      }
    }
    fetchLeads();
  }, []);

  // ── Derive unique states and areas for filter dropdowns ──
  const availableStates = useMemo(() => {
    const states = new Set(leads.map((l) => l.State).filter(Boolean));
    return Array.from(states).sort();
  }, [leads]);

  const availableAreas = useMemo(() => {
    const areas = new Set(leads.map((l) => l.Area).filter(Boolean));
    return Array.from(areas).sort();
  }, [leads]);

  // ── Apply filters + search ────────────────────────────
  const filteredLeads = useMemo(() => {
    let result = leads;

    // Search (name or phone)
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      result = result.filter(
        (l) =>
          l.Name.toLowerCase().includes(q) ||
          l.Phone.toLowerCase().includes(q)
      );
    }

    // Filter: state
    if (filters.state) {
      result = result.filter((l) => l.State === filters.state);
    }

    // Filter: area/city
    if (filters.area) {
      result = result.filter((l) => l.Area === filters.area);
    }

    // Filter: status
    if (filters.status) {
      result = result.filter((l) => l.Status === filters.status);
    }

    // Filter: keyword (searches across all text fields)
    if (filters.keyword.trim()) {
      const kw = filters.keyword.trim().toLowerCase();
      result = result.filter(
        (l) =>
          l.Name.toLowerCase().includes(kw) ||
          l.Phone.toLowerCase().includes(kw) ||
          l.Area.toLowerCase().includes(kw) ||
          l.State.toLowerCase().includes(kw) ||
          l.Source.toLowerCase().includes(kw)
      );
    }

    return result;
  }, [leads, search, filters]);

  // ── Compute stats from filtered data ──────────────────
  const stats = useMemo(() => {
    const total = filteredLeads.length;
    const contacted = filteredLeads.filter(
      (l) => l.Status === "Contacted"
    ).length;
    const notContacted = filteredLeads.filter(
      (l) => l.Status === "Not Contacted"
    ).length;
    const interested = filteredLeads.filter(
      (l) => l.Status === "Interested"
    ).length;
    const followUp = filteredLeads.filter(
      (l) => l.Status === "Follow-up"
    ).length;
    return { total, contacted, notContacted, interested, followUp };
  }, [filteredLeads]);

  // ── Handle status change (optimistic update) ──────────
  const handleStatusChange = useCallback(
    (id: string, collection: string, newStatus: string) => {
      setLeads((prev) =>
        prev.map((l) =>
          l.id === id && l.collection === collection
            ? { ...l, Status: newStatus }
            : l
        )
      );
    },
    []
  );

  // ── Refresh handler ───────────────────────────────────
  const handleRefresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAllLeads();
      setLeads(data);
    } catch (err) {
      console.error("Failed to refresh leads:", err);
      setError("Failed to refresh leads.");
    } finally {
      setLoading(false);
    }
  };

  // ── Loading state ─────────────────────────────────────
  if (loading && leads.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center gap-3">
          <svg
            className="w-8 h-8 text-blue-400 animate-spin-slow"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          <p className="text-sm text-white/40">Loading leads from Firestore...</p>
        </div>
      </div>
    );
  }

  // ── Error state ───────────────────────────────────────
  if (error && leads.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="max-w-md bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center">
          <svg
            className="w-10 h-10 text-red-400 mx-auto mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
          <p className="text-red-300 text-sm mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ── Main render ───────────────────────────────────────
  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Leads
          </h1>
          <p className="text-sm text-white/40 mt-0.5">
            {leads.length.toLocaleString()} total leads across all collections
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] rounded-lg text-sm text-white/60 hover:text-white transition-all disabled:opacity-40"
        >
          <svg
            className={`w-4 h-4 ${loading ? "animate-spin-slow" : ""}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh
        </button>
      </div>

      {/* Stats */}
      <StatsBar {...stats} />

      {/* Search + Filters */}
      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
        <SearchBar value={search} onChange={setSearch} />
        <Filters
          filters={filters}
          onChange={setFilters}
          availableStates={availableStates}
          availableAreas={availableAreas}
        />
      </div>

      {/* Results count */}
      {(search || filters.state || filters.area || filters.status || filters.keyword) && (
        <p className="text-xs text-white/30">
          Showing {filteredLeads.length.toLocaleString()} of{" "}
          {leads.length.toLocaleString()} leads
        </p>
      )}

      {/* Table */}
      <LeadsTable leads={filteredLeads} onStatusChange={handleStatusChange} />
    </div>
  );
}
