export type ApiError = {
	detail?: string;
	message?: string;
};

export type ActiveDetectionClass = "FMD" | "healthy";

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
	disease_class: ActiveDetectionClass;
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
	disease_class: ActiveDetectionClass;
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

export type GuideBlock = {
	type: "heading" | "paragraph" | "bullet_list" | "image";
	text?: string;
	items?: string[];
	media_id?: string;
	alt?: string;
};

export type GuideTranslation = {
	locale: string;
	title: string;
	summary: string;
	blocks: GuideBlock[];
};

export type GuideArticle = {
	id: string;
	category_id: string;
	state: "draft" | "published" | "unpublished" | "archived";
	published_at?: string | null;
	translations: GuideTranslation[];
};

export type GuideCategory = {
	id: string;
	state: "active" | "archived";
	system_owned: boolean;
	display_order: number;
	article_count: number;
	translations: { locale: string; label: string }[];
};

export type GuideMedia = {
	id: string;
	mime_type: "image/jpeg" | "image/png" | "image/webp";
	width: number;
	height: number;
	byte_size: number;
	sha256: string;
};

export type GuideAuditEvent = {
	id: string;
	actor_id: string;
	action: string;
	target_type: string;
	target_id: string;
	created_at: string;
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
