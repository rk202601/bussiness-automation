/**
 * StatsBar — Summary stat cards that update based on filtered data.
 */

interface StatsBarProps {
  total: number;
  contacted: number;
  notContacted: number;
  interested: number;
  followUp: number;
}

const STAT_CARDS = [
  { key: "total",        label: "Total Leads",    color: "from-blue-600/20 to-blue-800/10",   text: "text-blue-300",    border: "border-blue-500/20" },
  { key: "contacted",    label: "Contacted",      color: "from-sky-600/20 to-sky-800/10",     text: "text-sky-300",     border: "border-sky-500/20" },
  { key: "notContacted", label: "Not Contacted",  color: "from-slate-600/20 to-slate-800/10", text: "text-slate-300",   border: "border-slate-500/20" },
  { key: "interested",   label: "Interested",     color: "from-emerald-600/20 to-emerald-800/10", text: "text-emerald-300", border: "border-emerald-500/20" },
  { key: "followUp",     label: "Follow-up",      color: "from-amber-600/20 to-amber-800/10", text: "text-amber-300",   border: "border-amber-500/20" },
] as const;

export default function StatsBar({
  total,
  contacted,
  notContacted,
  interested,
  followUp,
}: StatsBarProps) {
  const values: Record<string, number> = {
    total,
    contacted,
    notContacted,
    interested,
    followUp,
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
      {STAT_CARDS.map((card) => (
        <div
          key={card.key}
          className={`relative overflow-hidden rounded-xl border ${card.border} bg-gradient-to-br ${card.color} p-4 transition-transform duration-200 hover:scale-[1.02]`}
        >
          <p className="text-xs font-medium text-white/50 uppercase tracking-wide">
            {card.label}
          </p>
          <p className={`mt-1.5 text-2xl font-bold ${card.text} tabular-nums`}>
            {values[card.key].toLocaleString()}
          </p>
        </div>
      ))}
    </div>
  );
}
