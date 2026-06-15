"use client";

import type { JurisdictionItem } from "@/src/shared/api/client";
import type { RiskSignalItem } from "@/src/shared/types/api";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useEffect, useRef } from "react";

type Bubble = {
	id: string;
	name: string;
	lat: number;
	lng: number;
	count: number;
	riskLevel: string;
};

const RISK_COLORS: Record<string, string> = {
	high: "#dc2626",
	medium: "#f59e0b",
	low: "#16a34a",
};

export function RiskSignalMap({
	signals,
	jurisdictions,
}: {
	signals: RiskSignalItem[];
	jurisdictions: JurisdictionItem[];
}) {
	const containerRef = useRef<HTMLDivElement>(null);
	const mapRef = useRef<maplibregl.Map | null>(null);
	const markersRef = useRef<maplibregl.Marker[]>([]);

	// Aggregate signal counts per jurisdiction
	const bubbles: Bubble[] = (() => {
		const byJur: Record<string, { count: number; riskLevel: string }> = {};
		signals.forEach((s) => {
			if (!byJur[s.jurisdiction_id])
				byJur[s.jurisdiction_id] = { count: 0, riskLevel: s.risk_level };
			byJur[s.jurisdiction_id].count += s.signal_count;
			// escalate displayed risk level: high > medium > low
			const order = { high: 3, medium: 2, low: 1 } as Record<string, number>;
			if (
				(order[s.risk_level] ?? 0) >
				(order[byJur[s.jurisdiction_id].riskLevel] ?? 0)
			) {
				byJur[s.jurisdiction_id].riskLevel = s.risk_level;
			}
		});
		return Object.entries(byJur)
			.map(([id, { count, riskLevel }]) => {
				const j = jurisdictions.find((x) => x.id === id);
				if (!j || j.latitude == null || j.longitude == null) return null;
				return {
					id,
					name: j.name,
					lat: j.latitude,
					lng: j.longitude,
					count,
					riskLevel,
				};
			})
			.filter((b): b is Bubble => b !== null);
	})();

	useEffect(() => {
		if (!containerRef.current || mapRef.current) return;

		const map = new maplibregl.Map({
			container: containerRef.current,
			style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
			center: [110.2, -7.05],
			zoom: 8,
			attributionControl: false,
		});
		map.addControl(
			new maplibregl.NavigationControl({ showCompass: false }),
			"top-right",
		);
		map.addControl(new maplibregl.AttributionControl({ compact: true }));
		mapRef.current = map;

		return () => {
			map.remove();
			mapRef.current = null;
		};
	}, []);

	useEffect(() => {
		const map = mapRef.current;
		if (!map) return;

		// Clear existing markers
		markersRef.current.forEach((m) => m.remove());
		markersRef.current = [];

		if (bubbles.length === 0) return;

		const maxCount = Math.max(...bubbles.map((b) => b.count), 1);

		bubbles.forEach((bubble) => {
			const size = 24 + (bubble.count / maxCount) * 36; // 24-60px
			const color = RISK_COLORS[bubble.riskLevel] ?? "#6b7280";

			const el = document.createElement("div");
			el.style.cssText = `
        width: ${size}px; height: ${size}px;
        background: ${color}33;
        border: 2px solid ${color};
        border-radius: 9999px;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; font-weight: 600; color: ${color};
        cursor: pointer;
      `;
			el.textContent = String(bubble.count);

			const popup = new maplibregl.Popup({
				offset: size / 2,
				closeButton: false,
			}).setHTML(
				`<div style="font-size:12px"><strong>${bubble.name}</strong><br/>${bubble.count} signals · ${bubble.riskLevel} risk</div>`,
			);

			const marker = new maplibregl.Marker({ element: el })
				.setLngLat([bubble.lng, bubble.lat])
				.setPopup(popup)
				.addTo(map);
			markersRef.current.push(marker);
		});

		// Fit bounds to bubbles
		if (bubbles.length > 0) {
			const bounds = new maplibregl.LngLatBounds();
			bubbles.forEach((b) => bounds.extend([b.lng, b.lat]));
			map.fitBounds(bounds, { padding: 80, maxZoom: 10, duration: 0 });
		}
	}, [bubbles]);

	return (
		<div className="relative overflow-hidden rounded-lg border">
			<div ref={containerRef} className="h-[360px] w-full" />
			<div className="absolute bottom-2 left-2 z-10 rounded-md bg-background/90 px-3 py-2 text-xs text-muted-foreground shadow-sm">
				Bubble size = signal count. Color = risk level. Prioritization only, not
				outbreak confirmation.
			</div>
		</div>
	);
}
