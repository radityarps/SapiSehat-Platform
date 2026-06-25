"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/src/shared/ui/card";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { Button } from "@/src/shared/ui/button";
import { ChartContainer, ChartTooltipContent } from "@/src/shared/ui/chart";
import {
	getAgencyFollowUps,
	getAgencyRegistry,
	getAuditLogs,
	getDetectionMonitoring,
	getRiskSignals,
} from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import { useQuery } from "@tanstack/react-query";
import {
	Activity,
	AlertTriangle,
	ArrowRight,
	ClipboardList,
	ShieldAlert,
	TrendingUp,
	Users,
} from "lucide-react";
import Link from "next/link";
import {
	Bar,
	BarChart,
	CartesianGrid,
	Cell,
	Pie,
	PieChart,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
	Area,
	AreaChart,
} from "recharts";

const CHART_COLORS = [
	"oklch(0.478 0.136 251.8)",
	"oklch(0.680 0.155 62)",
	"oklch(0.520 0.130 155)",
	"oklch(0.530 0.160 25)",
	"oklch(0.560 0.120 240)",
	"oklch(0.620 0.100 320)",
];

export function OverviewClient() {
	const { token, agencyUserId, agency } = useAgencySession();
	const enabled = Boolean(token && agencyUserId);

	const registry = useQuery({
		queryKey: ["overview-registry"],
		queryFn: () => getAgencyRegistry(token, agencyUserId),
		enabled,
	});
	const detections = useQuery({
		queryKey: ["overview-detections"],
		queryFn: () => getDetectionMonitoring(token, agencyUserId),
		enabled,
	});
	const riskSignals = useQuery({
		queryKey: ["overview-risk-signals"],
		queryFn: () => getRiskSignals(token, agencyUserId),
		enabled,
	});
	const auditLogs = useQuery({
		queryKey: ["overview-audit-logs"],
		queryFn: () => getAuditLogs(token, agencyUserId),
		enabled,
	});
	const followUps = useQuery({
		queryKey: ["overview-follow-ups"],
		queryFn: () => getAgencyFollowUps(token, agencyUserId),
		enabled,
	});

	const anyLoading =
		registry.isLoading ||
		detections.isLoading ||
		riskSignals.isLoading ||
		auditLogs.isLoading ||
		followUps.isLoading;

	const totalDetections = detections.data?.detections.length ?? 0;
	const totalSignals = riskSignals.data?.signals.length ?? 0;
	const totalFarmers = registry.data?.farmers.length ?? 0;
	const totalCattle = registry.data?.cattle.length ?? 0;
	const totalFollowUps = followUps.data?.followUps.length ?? 0;
	const pendingFollowUps =
		followUps.data?.followUps.filter((f) => f.status === "pending") ?? [];
	const highRiskSignals =
		riskSignals.data?.signals.filter((s) => s.risk_level === "high") ?? [];
	const recentLogs = auditLogs.data?.logs.slice(0, 5) ?? [];

	// Disease class breakdown for pie chart
	const diseaseBreakdown: Record<string, number> = {};
	detections.data?.detections.forEach((d) => {
		diseaseBreakdown[d.disease_class] =
			(diseaseBreakdown[d.disease_class] ?? 0) + 1;
	});
	const pieData = Object.entries(diseaseBreakdown).map(([name, value]) => ({
		name: name.replace(/_/g, " "),
		value,
	}));

	// Jurisdiction signal breakdown for bar chart
	const jurisdictionBreakdown: Record<string, number> = {};
	riskSignals.data?.signals.forEach((s) => {
		jurisdictionBreakdown[s.jurisdiction_id] =
			(jurisdictionBreakdown[s.jurisdiction_id] ?? 0) + s.signal_count;
	});
	const barData = Object.entries(jurisdictionBreakdown).map(
		([name, signals]) => ({ name, signals }),
	);

	// Risk level distribution for area chart
	const riskLevels: Record<string, number> = {};
	riskSignals.data?.signals.forEach((s) => {
		riskLevels[s.risk_level] = (riskLevels[s.risk_level] ?? 0) + 1;
	});
	const riskAreaData = Object.entries(riskLevels).map(([level, count]) => ({
		level,
		count,
	}));

	// Follow-up status distribution
	const followUpStatuses: Record<string, number> = {};
	followUps.data?.followUps.forEach((f) => {
		followUpStatuses[f.status] = (followUpStatuses[f.status] ?? 0) + 1;
	});
	const followUpBarData = Object.entries(followUpStatuses).map(
		([status, count]) => ({ status, count }),
	);

	if (anyLoading) {
		return (
			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				{Array.from({ length: 8 }).map((_, i) => (
					<Skeleton key={i} className="h-36 w-full rounded-lg" />
				))}
			</div>
		);
	}

	return (
		<div className="space-y-4">
			{/* Jurisdiction scope banner */}
			<div className="flex items-center gap-2 rounded-lg border bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
				<ShieldAlert className="h-4 w-4" />
				<span>
					Viewing data scoped to{" "}
					<strong className="text-foreground">
						{agency?.jurisdiction_id ?? "all"}
					</strong>
				</span>
				<span className="ml-auto text-xs capitalize">
					{agency?.role?.replace(/_/g, " ") ?? "officer"}
				</span>
			</div>

			{/* Row 1: Metric cards */}
			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
				<MetricCard
					title="Review Items"
					value={totalDetections}
					subtitle="Detection submissions"
					icon={ClipboardList}
					href="/agency/detections"
				/>
				<MetricCard
					title="Risk Signals"
					value={totalSignals}
					subtitle={
						highRiskSignals.length > 0
							? `${highRiskSignals.length} high priority`
							: "No high priority"
					}
					icon={AlertTriangle}
					href="/agency/risk-signals"
					badge={
						highRiskSignals.length > 0
							? {
									label: `${highRiskSignals.length} high`,
									variant: "destructive" as const,
								}
							: undefined
					}
				/>
				<MetricCard
					title="Follow-ups"
					value={totalFollowUps}
					subtitle={
						pendingFollowUps.length > 0
							? `${pendingFollowUps.length} pending`
							: "All resolved"
					}
					icon={TrendingUp}
					href="/agency/follow-ups"
					badge={
						pendingFollowUps.length > 0
							? {
									label: `${pendingFollowUps.length} pending`,
									variant: "warning" as const,
								}
							: undefined
					}
				/>
				<MetricCard
					title="Registry"
					value={totalFarmers}
					subtitle={`${totalCattle} cattle registered`}
					icon={Users}
					href="/agency/registry"
				/>
			</div>

			{/* Row 2: Charts */}
			<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
				{/* Disease breakdown pie chart */}
				<Card className="lg:col-span-1">
					<CardHeader className="pb-2">
						<CardTitle className="text-sm font-medium">
							Disease Distribution
						</CardTitle>
					</CardHeader>
					<CardContent>
						{pieData.length === 0 ? (
							<p className="text-sm text-muted-foreground py-8 text-center">
								No detections yet
							</p>
						) : (
							<div className="h-[200px]">
								<ResponsiveContainer
									width="100%"
									height="100%"
									minWidth={0}
									minHeight={0}
								>
									<PieChart>
										<Pie
											data={pieData}
											cx="50%"
											cy="50%"
											innerRadius={50}
											outerRadius={80}
											paddingAngle={2}
											dataKey="value"
										>
											{pieData.map((_, i) => (
												<Cell
													key={i}
													fill={CHART_COLORS[i % CHART_COLORS.length]}
												/>
											))}
										</Pie>
										<Tooltip content={<ChartTooltipContent />} />
									</PieChart>
								</ResponsiveContainer>
								<div className="flex flex-wrap gap-2 justify-center mt-2">
									{pieData.map((d, i) => (
										<div
											key={d.name}
											className="flex items-center gap-1 text-xs"
										>
											<span
												className="h-2 w-2 rounded-full"
												style={{
													backgroundColor:
														CHART_COLORS[i % CHART_COLORS.length],
												}}
											/>
											<span className="capitalize text-muted-foreground">
												{d.name}
											</span>
										</div>
									))}
								</div>
							</div>
						)}
					</CardContent>
				</Card>

				{/* Signal density bar chart */}
				<Card className="lg:col-span-1">
					<CardHeader className="pb-2">
						<CardTitle className="text-sm font-medium">
							Signal Density
						</CardTitle>
					</CardHeader>
					<CardContent>
						{barData.length === 0 ? (
							<p className="text-sm text-muted-foreground py-8 text-center">
								No signals yet
							</p>
						) : (
							<div className="h-[200px]">
								<ResponsiveContainer
									width="100%"
									height="100%"
									minWidth={0}
									minHeight={0}
								>
									<BarChart
										data={barData}
										margin={{ top: 5, right: 5, left: -10, bottom: 5 }}
									>
										<CartesianGrid
											strokeDasharray="3 3"
											className="stroke-border"
										/>
										<XAxis
											dataKey="name"
											tick={{ fontSize: 11 }}
											className="fill-muted-foreground"
										/>
										<YAxis
											tick={{ fontSize: 11 }}
											className="fill-muted-foreground"
										/>
										<Tooltip content={<ChartTooltipContent />} />
										<Bar
											dataKey="signals"
											fill="oklch(0.478 0.136 251.8)"
											radius={[4, 4, 0, 0]}
										/>
									</BarChart>
								</ResponsiveContainer>
							</div>
						)}
					</CardContent>
				</Card>

				{/* Follow-up status breakdown */}
				<Card className="lg:col-span-1">
					<CardHeader className="pb-2">
						<CardTitle className="text-sm font-medium">
							Follow-up Status
						</CardTitle>
					</CardHeader>
					<CardContent>
						{followUpBarData.length === 0 ? (
							<p className="text-sm text-muted-foreground py-8 text-center">
								No follow-ups yet
							</p>
						) : (
							<div className="h-[200px]">
								<ResponsiveContainer
									width="100%"
									height="100%"
									minWidth={0}
									minHeight={0}
								>
									<BarChart
										data={followUpBarData}
										layout="vertical"
										margin={{ top: 5, right: 5, left: 10, bottom: 5 }}
									>
										<CartesianGrid
											strokeDasharray="3 3"
											className="stroke-border"
										/>
										<XAxis
											type="number"
											tick={{ fontSize: 11 }}
											className="fill-muted-foreground"
										/>
										<YAxis
											type="category"
											dataKey="status"
											tick={{ fontSize: 11 }}
											className="fill-muted-foreground"
											width={70}
										/>
										<Tooltip content={<ChartTooltipContent />} />
										<Bar
											dataKey="count"
											fill="oklch(0.680 0.155 62)"
											radius={[0, 4, 4, 0]}
										/>
									</BarChart>
								</ResponsiveContainer>
							</div>
						)}
					</CardContent>
				</Card>
			</div>

			{/* Row 3: Work surfaces */}
			<div className="grid gap-4 md:grid-cols-2">
				{/* Pending work queue */}
				<Card>
					<CardHeader className="flex flex-row items-center justify-between pb-3">
						<CardTitle className="text-sm font-medium">Pending Work</CardTitle>
						<Button variant="ghost" size="sm" asChild>
							<Link href="/agency/follow-ups" className="gap-1 text-xs">
								View all <ArrowRight className="h-3 w-3" />
							</Link>
						</Button>
					</CardHeader>
					<CardContent>
						{pendingFollowUps.length === 0 ? (
							<div className="flex flex-col items-center justify-center py-6 text-center">
								<TrendingUp className="h-8 w-8 text-muted-foreground/40 mb-2" />
								<p className="text-sm text-muted-foreground">
									No pending follow-ups
								</p>
							</div>
						) : (
							<div className="space-y-2">
								{pendingFollowUps.slice(0, 5).map((item) => (
									<div
										key={item.id}
										className="flex items-center justify-between rounded-md border px-3 py-2 transition-colors hover:bg-muted/30"
									>
										<div className="space-y-0.5 overflow-hidden">
											<p className="text-sm font-medium truncate">
												Farmer: {item.farmer_id}
											</p>
											<p className="text-xs text-muted-foreground line-clamp-1">
												{item.public_message}
											</p>
										</div>
										<span className="shrink-0 ml-2 inline-flex items-center rounded-full bg-amber-500/10 px-2 py-0.5 text-xs font-medium text-amber-700">
											{item.status}
										</span>
									</div>
								))}
							</div>
						)}
					</CardContent>
				</Card>

				{/* Recent activity */}
				<Card>
					<CardHeader className="flex flex-row items-center justify-between pb-3">
						<CardTitle className="text-sm font-medium">
							Recent Activity
						</CardTitle>
						<Button variant="ghost" size="sm" asChild>
							<Link href="/agency/audit-logs" className="gap-1 text-xs">
								View all <ArrowRight className="h-3 w-3" />
							</Link>
						</Button>
					</CardHeader>
					<CardContent>
						{recentLogs.length === 0 ? (
							<div className="flex flex-col items-center justify-center py-6 text-center">
								<Activity className="h-8 w-8 text-muted-foreground/40 mb-2" />
								<p className="text-sm text-muted-foreground">
									No recent activity
								</p>
							</div>
						) : (
							<div className="space-y-2">
								{recentLogs.map((log) => (
									<div
										key={log.id}
										className="flex items-center gap-3 rounded-md border px-3 py-2 transition-colors hover:bg-muted/30"
									>
										<Activity className="h-4 w-4 shrink-0 text-muted-foreground" />
										<div className="flex-1 space-y-0.5 overflow-hidden">
											<p className="truncate text-sm">
												<span className="font-medium">{log.actor_id}</span>{" "}
												{log.action}{" "}
												<span className="text-muted-foreground">
													{log.resource_type}
												</span>
											</p>
											<p className="text-xs text-muted-foreground">
												{new Date(log.created_at).toLocaleString()}
											</p>
										</div>
									</div>
								))}
							</div>
						)}
					</CardContent>
				</Card>
			</div>
		</div>
	);
}

function MetricCard({
	title,
	value,
	subtitle,
	icon: Icon,
	href,
	badge,
}: {
	title: string;
	value: number;
	subtitle: string;
	icon: React.ElementType;
	href: string;
	badge?: { label: string; variant: "destructive" | "warning" };
}) {
	return (
		<Card className="relative overflow-hidden transition-colors hover:bg-muted/20">
			<CardHeader className="flex flex-row items-center justify-between pb-2">
				<CardTitle className="text-sm font-medium text-muted-foreground">
					{title}
				</CardTitle>
				<Icon className="h-4 w-4 text-muted-foreground" />
			</CardHeader>
			<CardContent>
				<div className="text-3xl font-bold tabular-nums">{value}</div>
				<div className="flex items-center gap-1.5 mt-1">
					{badge && (
						<span
							className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
								badge.variant === "destructive"
									? "bg-destructive/10 text-destructive"
									: "bg-amber-500/10 text-amber-700"
							}`}
						>
							{badge.label}
						</span>
					)}
					<span className="text-xs text-muted-foreground">{subtitle}</span>
				</div>
			</CardContent>
			<Link
				href={href}
				className="absolute inset-0"
				aria-label={`Go to ${title}`}
			/>
		</Card>
	);
}
