/**
 * StatusBadge — Color-coded pill for lead status.
 */

interface StatusBadgeProps {
  status: string;
}

const STATUS_COLORS: Record<string, string> = {
  "Not Contacted": "bg-slate-600/20 text-slate-300 border-slate-600/30",
  "Contacted":     "bg-blue-600/20 text-blue-300 border-blue-600/30",
  "Interested":    "bg-emerald-600/20 text-emerald-300 border-emerald-600/30",
  "Not Interested": "bg-red-600/20 text-red-300 border-red-600/30",
  "Follow-up":     "bg-amber-600/20 text-amber-300 border-amber-600/30",
};

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colors = STATUS_COLORS[status] || STATUS_COLORS["Not Contacted"];

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors} transition-colors`}
    >
      {status}
    </span>
  );
}
