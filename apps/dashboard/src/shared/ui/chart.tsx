"use client";

import * as React from "react";
import { Tooltip as RechartsTooltip } from "recharts";
import { cn } from "@/src/shared/lib/utils";

// Chart config type
export type ChartConfig = Record<string, { label: string; color: string }>;

type ChartContextProps = {
	config: ChartConfig;
};

const ChartContext = React.createContext<ChartContextProps | null>(null);

export function useChart() {
	const context = React.useContext(ChartContext);
	if (!context)
		throw new Error("useChart must be used within a ChartContainer");
	return context;
}

export function ChartContainer({
	config,
	className,
	children,
}: {
	config: ChartConfig;
	className?: string;
	children: React.ReactNode;
}) {
	return (
		<ChartContext.Provider value={{ config }}>
			<div
				className={cn("w-full", className)}
				style={Object.entries(config).reduce(
					(acc, [key, value]) => {
						acc[`--color-${key}` as string] = value.color;
						return acc;
					},
					{} as Record<string, string>,
				)}
			>
				{children}
			</div>
		</ChartContext.Provider>
	);
}

export function ChartTooltipContent({
	active,
	payload,
	label,
	hideLabel = false,
}: {
	active?: boolean;
	payload?: Array<{
		name: string;
		value: number;
		color: string;
		dataKey: string;
	}>;
	label?: string;
	hideLabel?: boolean;
}) {
	if (!active || !payload?.length) return null;
	return (
		<div className="rounded-md border bg-popover px-3 py-2 text-xs shadow-md">
			{!hideLabel && label && (
				<p className="mb-1 font-medium text-foreground">{label}</p>
			)}
			<div className="space-y-0.5">
				{payload.map((entry, i) => (
					<div key={i} className="flex items-center gap-2">
						<span
							className="h-2.5 w-2.5 rounded-full"
							style={{ backgroundColor: entry.color }}
						/>
						<span className="text-muted-foreground">{entry.name}:</span>
						<span className="font-medium text-foreground">{entry.value}</span>
					</div>
				))}
			</div>
		</div>
	);
}

export { RechartsTooltip as ChartTooltip };
