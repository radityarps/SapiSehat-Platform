export type ApiError = {
	detail?: string;
	message?: string;
};

export type AgencyRole =
	| "admin"
	| "province_officer"
	| "district_officer"
	| "village_officer"
	| "viewer";

export type AgencyMe = {
	id: string;
	email: string;
	name: string;
	account_type: "agency";
	role?: AgencyRole;
	jurisdiction_id?: string;
};

export type AgencyRegistryFarmer = {
	id: string;
	name: string;
	address?: string | null;
	jurisdiction_id: string;
	consent_tier: string;
};

export type AgencyRegistryCattle = {
	id: string;
	farmer_id: string;
	tag: string;
	sex: string;
	breed: string;
	age_months?: number | null;
	birth_year_estimate?: number | null;
	status: string;
	jurisdiction_id: string;
	name?: string | null;
	color?: string | null;
	weight_kg?: number | null;
	reproductive_status?: string | null;
	is_pregnant?: boolean | null;
	last_calving_date?: string | null;
	last_vaccination_date?: string | null;
	last_deworming_date?: string | null;
	health_notes?: string | null;
	purchase_date?: string | null;
	purchase_price_idr?: number | null;
	notes?: string | null;
};

export type SafeLanguage = {
	title?: string;
	description?: string;
	forbidden_terms?: string;
};

export type DetectionMonitoringItem = {
	id: string;
	cattle_id?: string;
	farmer_id: string;
	disease_class: string;
	confidence: number;
	confidence_level?: string;
	reliability?: string;
	conflict_status?: string;
	handling_advice_key?: string;
	model_versions?: Record<string, string>;
	evidence_breakdown?: Record<string, unknown>;
	created_at?: string;
};

export type RiskSignalItem = {
	id: string;
	jurisdiction_id: string;
	disease_class: string;
	signal_count: number;
	risk_level: string;
	priority: string;
	source_result_ids: string[];
};

export type AuditLogItem = {
	id: string;
	actor_type: string;
	action: string;
	actor_id: string;
	resource_type: string;
	resource_id: string;
	created_at: string;
	metadata_json: Record<string, unknown>;
};

export type AgencyFollowUpItem = {
	id: string;
	farmer_id: string;
	cattle_id?: string | null;
	status: string;
	public_message: string;
	internal_notes: string;
};

export type NotificationItem = {
	id: string;
	account_id: string;
	account_type: string;
	title: string;
	body: string;
	link?: string | null;
	is_read: boolean;
	created_at: string;
};
