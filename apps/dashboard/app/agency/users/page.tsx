import { UsersClient } from "./users-client";

export default function UsersPage() {
	return (
		<div className="space-y-6">
			<section className="space-y-2">
				<h1 className="text-3xl font-semibold tracking-tight">
					User Management
				</h1>
				<p className="max-w-2xl text-sm text-muted-foreground">
					Manage agency users, assign roles, and set jurisdiction scopes.
				</p>
			</section>

			<UsersClient />
		</div>
	);
}
