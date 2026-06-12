import { z } from "zod";
import type {
	ApiError,
	AgencyFollowUpItem,
	AgencyMe,
	AgencyRegistryCattle,
	AgencyRegistryFarmer,
	AuditLogItem,
	DetectionMonitoringItem,
	RiskSignalItem,
	SafeLanguage,
} from "@/src/shared/types/api";

const envBase = process.env.NEXT_PUBLIC_API_BASE_URL;
const baseUrl = envBase && envBase.startsWith("http") ? envBase : "";

const agencyMeSchema = z.object({
	id: z.string(),
	email: z.string().email(),
	name: z.string(),
	account_type: z.literal("agency"),
	role: z.string().optional(),
	jurisdiction_id: z.string().optional(),
});

const safeLanguageSchema = z.object({
	title: z.string().optional(),
	description: z.string().optional(),
	forbidden_terms: z.string().optional(),
});

const detectionSchema = z.object({
	id: z.string(),
	cattle_id: z.string().optional(),
	farmer_id: z.string(),
	disease_class: z.string(),
	confidence: z.number(),
	confidence_level: z.string().optional(),
	reliability: z.string().optional(),
	conflict_status: z.string().optional(),
	handling_advice_key: z.string().optional(),
	model_versions: z.record(z.string()).optional(),
	evidence_breakdown: z.record(z.any()).optional(),
	created_at: z.string().optional(),
});

const riskSignalSchema = z.object({
	id: z.string(),
	jurisdiction_id: z.string(),
	disease_class: z.string(),
	signal_count: z.number(),
	risk_level: z.string(),
	priority: z.string(),
	source_result_ids: z.array(z.string()),
});

const auditSchema = z.object({
	id: z.string(),
	actor_type: z.string(),
	action: z.string(),
	actor_id: z.string(),
	resource_type: z.string(),
	resource_id: z.string(),
	created_at: z.string(),
	metadata_json: z.record(z.any()),
});

const followUpSchema = z.object({
	id: z.string(),
	farmer_id: z.string(),
	cattle_id: z.string().nullable().optional(),
	status: z.string(),
	public_message: z.string(),
	internal_notes: z.string(),
});

async function request<T>(
	path: string,
	init: RequestInit = {},
	token?: string,
): Promise<T> {
	const url = baseUrl ? `${baseUrl}${path}` : path;
	const response = await fetch(url, {
		...init,
		headers: {
			"Content-Type": "application/json",
			...(token ? { Authorization: `Bearer ${token}` } : {}),
			...(init.headers ?? {}),
		},
		cache: "no-store",
	});

	if (!response.ok) {
		let detail = `Request failed (${response.status})`;
		try {
			const parsed = (await response.json()) as ApiError;
			detail = parsed.detail ?? parsed.message ?? detail;
		} catch {
			// noop
		}
		throw new Error(detail);
	}

	return (await response.json()) as T;
}

export async function loginAgency(email: string, password: string) {
	return request<{
		access_token: string;
		token_type: "bearer";
		account?: AgencyMe;
	}>("/api/auth/agency/login", {
		method: "POST",
		body: JSON.stringify({ email, password }),
	});
}

export async function getMe(token: string) {
	const data = await request<unknown>("/api/me", {}, token);
	return agencyMeSchema.parse(data) as AgencyMe;
}

export async function getDetectionMonitoring(
	token: string,
	agencyUserId: string,
) {
	const data = await request<{
		detections: unknown[];
		safe_language?: unknown;
	}>(
		"/api/agency/detection-monitoring",
		{
			headers: {
				Authorization: `Bearer ${token}`,
				"X-Agency-User-Id": agencyUserId,
			},
		},
		token,
	);
	const detections = z.array(detectionSchema).parse(data.detections);
	return {
		detections: detections as DetectionMonitoringItem[],
		safeLanguage: data.safe_language
			? (safeLanguageSchema.parse(data.safe_language) as SafeLanguage)
			: undefined,
	};
}

export async function getRiskSignals(token: string, agencyUserId: string) {
	const data = await request<{
		signals: unknown[];
		rule?: Record<string, unknown>;
	}>(
		"/api/agency/risk-signals",
		{
			headers: {
				Authorization: `Bearer ${token}`,
				"X-Agency-User-Id": agencyUserId,
			},
		},
		token,
	);
	const signals = z.array(riskSignalSchema).parse(data.signals);
	return { signals: signals as RiskSignalItem[], rule: data.rule ?? {} };
}

export async function getAuditLogs(token: string, agencyUserId: string) {
	const data = await request<{ audit_logs: unknown[] }>(
		"/api/agency/audit-logs",
		{
			headers: {
				Authorization: `Bearer ${token}`,
				"X-Agency-User-Id": agencyUserId,
			},
		},
		token,
	);
	const logs = z.array(auditSchema).parse(data.audit_logs);
	return { logs: logs as AuditLogItem[] };
}

export async function getAgencyRegistry(token: string, agencyUserId: string) {
	const data = await request<{
		agency_user_id: string;
		farmers: unknown[];
		cattle: unknown[];
		filters?: Record<string, unknown>;
	}>(
		"/api/agency/registry",
		{
			headers: {
				Authorization: `Bearer ${token}`,
				"X-Agency-User-Id": agencyUserId,
			},
		},
		token,
	);
	return {
		agencyUserId: data.agency_user_id,
		farmers: z
			.array(
				z.object({
					id: z.string(),
					name: z.string(),
					jurisdiction_id: z.string(),
					consent_tier: z.string(),
				}),
			)
			.parse(data.farmers) as AgencyRegistryFarmer[],
		cattle: z
			.array(
				z.object({
					id: z.string(),
					farmer_id: z.string(),
					tag: z.string(),
					sex: z.string(),
					breed: z.string(),
					age_months: z.number().nullable().optional(),
					birth_year_estimate: z.number().nullable().optional(),
					status: z.string(),
					jurisdiction_id: z.string(),
				}),
			)
			.parse(data.cattle) as AgencyRegistryCattle[],
		filters: data.filters ?? {},
	};
}

export async function getAgencyFollowUps(token: string, agencyUserId: string) {
	const data = await request<unknown[]>(
		"/api/agency/follow-ups",
		{
			headers: {
				Authorization: `Bearer ${token}`,
				"X-Agency-User-Id": agencyUserId,
			},
		},
		token,
	);
	return {
		followUps: z.array(followUpSchema).parse(data) as AgencyFollowUpItem[],
	};
}

export type CreateFollowUpInput = {
	farmer_id: string;
	cattle_id?: string;
	status: string;
	public_message: string;
	internal_notes?: string;
};

export async function createAgencyFollowUp(
	token: string,
	agencyUserId: string,
	input: CreateFollowUpInput,
) {
	const data = await request<unknown>(
		"/api/agency/follow-ups",
		{
			method: "POST",
			headers: {
				Authorization: `Bearer ${token}`,
				"X-Agency-User-Id": agencyUserId,
			},
			body: JSON.stringify(input),
		},
		token,
	);
	return followUpSchema.parse(data) as AgencyFollowUpItem;
}

export type NlpPlaceholderInput = {
	farmer_id: string;
	cattle_id?: string;
	symptom_text?: string;
	questionnaire_answers?: Record<string, unknown>;
};

const nlpPlaceholderSchema = z.object({
	status: z.literal("unavailable"),
	evidence_state: z.literal("nlp_unavailable"),
	accepted_for_fusion: z.literal(false),
	creates_review_item: z.literal(false),
	creates_risk_signal: z.literal(false),
	message: z.string(),
});

export async function createNlpPlaceholder(
	token: string,
	input: NlpPlaceholderInput,
) {
	const data = await request<unknown>(
		"/api/evidence/nlp/placeholder",
		{
			method: "POST",
			headers: { Authorization: `Bearer ${token}` },
			body: JSON.stringify(input),
		},
		token,
	);
	return nlpPlaceholderSchema.parse(data);
}
