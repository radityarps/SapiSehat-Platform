import { Badge } from '@/src/shared/ui/badge';
import type { RiskSignalItem } from '@/src/shared/types/api';

const positions: Record<string, string> = {
  tembalang: 'left-[58%] top-[48%]',
  banyumanik: 'left-[46%] top-[62%]',
  'semarang-city': 'left-[52%] top-[54%]',
  'central-java': 'left-[42%] top-[42%]'
};

export function RiskSignalMap({ signals }: { signals: RiskSignalItem[] }) {
  return (
    <div className="relative min-h-[280px] overflow-hidden rounded-lg border bg-[radial-gradient(circle_at_35%_35%,rgba(46,107,79,0.18),transparent_35%),linear-gradient(135deg,#fffaf0,#eef6ef)] p-4">
      <div className="absolute left-4 top-4 max-w-xs rounded-md bg-background/90 p-3 text-xs text-muted-foreground shadow-sm">
        Simple jurisdiction map. Shows prioritization only; not outbreak confirmation.
      </div>
      <div className="absolute inset-x-8 bottom-8 top-16 rounded-[42%_58%_48%_52%] border-2 border-primary/30 bg-primary/5" />
      {signals.map((signal) => (
        <div key={signal.id} className={`absolute ${positions[signal.jurisdiction_id] ?? 'left-1/2 top-1/2'} -translate-x-1/2 -translate-y-1/2`}>
          <div className="flex flex-col items-center gap-1">
            <div className="grid h-10 w-10 place-items-center rounded-full border-4 border-background bg-primary text-sm font-semibold text-primary-foreground shadow-lg">{signal.signal_count}</div>
            <Badge variant="secondary" className="bg-background/95 text-[10px] shadow-sm">{signal.jurisdiction_id}</Badge>
          </div>
        </div>
      ))}
    </div>
  );
}
