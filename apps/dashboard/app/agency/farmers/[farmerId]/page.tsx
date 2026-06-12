import { FarmerDetailClient } from '@/src/features/agency/farmers/farmer-detail-client';

export default async function FarmerDetailPage({ params }: { params: Promise<{ farmerId: string }> }) {
  const { farmerId } = await params;
  return <FarmerDetailClient farmerId={farmerId} />;
}
