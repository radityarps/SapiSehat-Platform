import { Badge } from '@/src/shared/ui/badge';
import type { DetectionMonitoringItem } from '@/src/shared/types/api';

type EvidenceBlock = { source?: string; quality_status?: string; accepted_for_fusion?: boolean };

function evidence(item: DetectionMonitoringItem, key: 'image' | 'nlp'): EvidenceBlock | null {
  const value = item.evidence_breakdown?.[key];
  return value && typeof value === 'object' ? value as EvidenceBlock : null;
}

export function EvidenceLabel({ item }: { item: DetectionMonitoringItem }) {
  const image = evidence(item, 'image');
  const nlp = evidence(item, 'nlp');
  if (image && !nlp) return <Badge variant="warning">Image-only evidence</Badge>;
  if (!image && nlp) return <Badge variant="warning">NLP-only evidence</Badge>;
  if (image && nlp) return <Badge variant="secondary">Image + NLP</Badge>;
  return <Badge variant="outline">Evidence missing</Badge>;
}

export function EvidenceDetail({ item }: { item: DetectionMonitoringItem }) {
  const image = evidence(item, 'image');
  const nlp = evidence(item, 'nlp');
  const imageLabel = image?.quality_status ? `image: ${image.quality_status}` : image ? 'image: present' : 'image: missing';
  const nlpLabel = nlp?.accepted_for_fusion === false ? 'nlp: unavailable' : nlp ? 'nlp: present' : 'nlp: missing';
  return <span className="text-xs text-muted-foreground">{imageLabel}; {nlpLabel}</span>;
}
