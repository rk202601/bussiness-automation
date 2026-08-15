/**
 * LeadsTable — Displays leads in a responsive table.
 * Supports inline status editing via dropdown.
 */

"use client";

import { useState } from "react";
import StatusBadge from "./StatusBadge";
import { Lead, STATUS_OPTIONS, updateLeadStatus } from "@/lib/firestore";

interface LeadsTableProps {
  leads: Lead[];
  onStatusChange: (id: string, collection: string, newStatus: string) => void;
}

export default function LeadsTable({ leads, onStatusChange }: LeadsTableProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<string | null>(null);

  const handleStatusChange = async (
    lead: Lead,
    newStatus: string
  ) => {
    setSavingId(lead.id);
    setEditingId(null);
    try {
      await updateLeadStatus(lead.collection, lead.id, newStatus);
      onStatusChange(lead.id, lead.collection, newStatus);
    } catch (err) {
      console.error("Failed to update status:", err);
      alert("Failed to update status. Check console for details.");
    } finally {
      setSavingId(null);
    }
  };

  if (leads.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-white/30">
        <svg className="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
        <p className="text-sm font-medium">No leads found</p>
        <p className="text-xs mt-1">Try adjusting your filters or search query</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/[0.06] bg-white/[0.02]">
            <th className="text-left px-4 py-3 font-medium text-white/40 uppercase text-xs tracking-wider">
              Name
            </th>
            <th className="text-left px-4 py-3 font-medium text-white/40 uppercase text-xs tracking-wider">
              Phone
            </th>
            <th className="text-left px-4 py-3 font-medium text-white/40 uppercase text-xs tracking-wider hidden md:table-cell">
              Area
            </th>
            <th className="text-left px-4 py-3 font-medium text-white/40 uppercase text-xs tracking-wider hidden lg:table-cell">
              State
            </th>
            <th className="text-left px-4 py-3 font-medium text-white/40 uppercase text-xs tracking-wider">
              Status
            </th>
            <th className="text-left px-4 py-3 font-medium text-white/40 uppercase text-xs tracking-wider w-24">
              Action
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/[0.04]">
          {leads.map((lead) => (
            <tr
              key={`${lead.collection}-${lead.id}`}
              className="hover:bg-white/[0.02] transition-colors"
            >
              {/* Name */}
              <td className="px-4 py-3">
                <span className="text-white font-medium">{lead.Name || "—"}</span>
              </td>

              {/* Phone */}
              <td className="px-4 py-3">
                <a
                  href={`tel:${lead.Phone}`}
                  className="text-blue-400 hover:text-blue-300 transition-colors font-mono text-[13px]"
                >
                  {lead.Phone || "—"}
                </a>
              </td>

              {/* Area */}
              <td className="px-4 py-3 hidden md:table-cell">
                <span className="text-white/60">{lead.Area || "—"}</span>
              </td>

              {/* State */}
              <td className="px-4 py-3 hidden lg:table-cell">
                <span className="text-white/60">{lead.State || "—"}</span>
              </td>

              {/* Status */}
              <td className="px-4 py-3">
                {editingId === lead.id ? (
                  <select
                    autoFocus
                    defaultValue={lead.Status}
                    onChange={(e) => handleStatusChange(lead, e.target.value)}
                    onBlur={() => setEditingId(null)}
                    className="px-2 py-1 bg-[#1a1b23] border border-blue-500/40 rounded text-xs text-white focus:outline-none cursor-pointer"
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                ) : savingId === lead.id ? (
                  <span className="text-xs text-white/40 animate-pulse">Saving...</span>
                ) : (
                  <StatusBadge status={lead.Status} />
                )}
              </td>

              {/* Action */}
              <td className="px-4 py-3">
                <button
                  onClick={() => setEditingId(lead.id)}
                  disabled={savingId === lead.id}
                  className="text-xs text-white/40 hover:text-white px-2 py-1 rounded hover:bg-white/[0.06] transition-all disabled:opacity-30"
                >
                  Edit
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
