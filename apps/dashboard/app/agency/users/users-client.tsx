"use client";

import { useAgencySession } from "@/src/features/auth/session-context";
import { Button } from "@/src/shared/ui/button";
import { Input } from "@/src/shared/ui/input";
import { Label } from "@/src/shared/ui/label";
import { Skeleton } from "@/src/shared/ui/skeleton";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

type AgencyUserItem = { id: string; role: string; jurisdiction_id: string };
type JurisdictionItem = {
	id: string;
	name: string;
	level: string;
	parent_id: string | null;
};

const ROLES = [
	"admin",
	"province_officer",
	"district_officer",
	"village_officer",
	"viewer",
];

async function fetchUsers(
	token: string,
	agencyUserId: string,
): Promise<{ users: AgencyUserItem[] }> {
	const res = await fetch("/api/agency/users", {
		headers: {
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
	});
	if (!res.ok) throw new Error("Failed to fetch users");
	return res.json();
}

async function fetchJurisdictions(
	token: string,
	agencyUserId: string,
): Promise<{ jurisdictions: JurisdictionItem[] }> {
	const res = await fetch("/api/agency/jurisdictions", {
		headers: {
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
	});
	if (!res.ok) throw new Error("Failed to fetch jurisdictions");
	return res.json();
}

async function createUser(
	token: string,
	agencyUserId: string,
	data: AgencyUserItem,
) {
	const res = await fetch("/api/agency/users", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
		body: JSON.stringify(data),
	});
	if (!res.ok) throw new Error("Failed to create user");
	return res.json();
}

async function updateUser(
	token: string,
	agencyUserId: string,
	userId: string,
	data: { role: string; jurisdiction_id?: string },
) {
	const res = await fetch(`/api/agency/users/${userId}`, {
		method: "PUT",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
		body: JSON.stringify(data),
	});
	if (!res.ok) throw new Error("Failed to update user");
	return res.json();
}

async function deleteUser(token: string, agencyUserId: string, userId: string) {
	const res = await fetch(`/api/agency/users/${userId}`, {
		method: "DELETE",
		headers: {
			Authorization: `Bearer ${token}`,
			"X-Agency-User-Id": agencyUserId,
		},
	});
	if (!res.ok) throw new Error("Failed to delete user");
	return res.json();
}

export function UsersClient() {
	const { token, agencyUserId } = useAgencySession();
	const queryClient = useQueryClient();
	const [showForm, setShowForm] = useState(false);
	const [editingUser, setEditingUser] = useState<AgencyUserItem | null>(null);
	const [formId, setFormId] = useState("");
	const [formRole, setFormRole] = useState("district_officer");
	const [formJurisdiction, setFormJurisdiction] = useState("");

	const usersQuery = useQuery({
		queryKey: ["agency-users"],
		queryFn: () => fetchUsers(token, agencyUserId),
		enabled: Boolean(token && agencyUserId),
	});

	const jurisdictionsQuery = useQuery({
		queryKey: ["jurisdictions"],
		queryFn: () => fetchJurisdictions(token, agencyUserId),
		enabled: Boolean(token && agencyUserId),
	});

	const createMutation = useMutation({
		mutationFn: (data: AgencyUserItem) => createUser(token, agencyUserId, data),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["agency-users"] });
			resetForm();
		},
	});

	const updateMutation = useMutation({
		mutationFn: (data: {
			userId: string;
			role: string;
			jurisdiction_id: string;
		}) =>
			updateUser(token, agencyUserId, data.userId, {
				role: data.role,
				jurisdiction_id: data.jurisdiction_id,
			}),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["agency-users"] });
			resetForm();
		},
	});

	const deleteMutation = useMutation({
		mutationFn: (userId: string) => deleteUser(token, agencyUserId, userId),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["agency-users"] });
		},
	});

	function resetForm() {
		setShowForm(false);
		setEditingUser(null);
		setFormId("");
		setFormRole("district_officer");
		setFormJurisdiction("");
	}

	function startEdit(user: AgencyUserItem) {
		setEditingUser(user);
		setFormId(user.id);
		setFormRole(user.role);
		setFormJurisdiction(user.jurisdiction_id);
		setShowForm(true);
	}

	function handleSubmit(e: React.FormEvent) {
		e.preventDefault();
		if (editingUser) {
			updateMutation.mutate({
				userId: editingUser.id,
				role: formRole,
				jurisdiction_id: formJurisdiction,
			});
		} else {
			createMutation.mutate({
				id: formId,
				role: formRole,
				jurisdiction_id: formJurisdiction,
			});
		}
	}

	if (usersQuery.isPending) {
		return (
			<div className="space-y-3">
				<Skeleton className="h-10 w-full" />
				<Skeleton className="h-10 w-full" />
				<Skeleton className="h-10 w-full" />
			</div>
		);
	}

	const users = usersQuery.data?.users ?? [];
	const jurisdictions = jurisdictionsQuery.data?.jurisdictions ?? [];

	return (
		<div className="space-y-4">
			<div className="flex items-center justify-between">
				<p className="text-sm text-muted-foreground">{users.length} users</p>
				<Button
					size="sm"
					onClick={() => {
						resetForm();
						setShowForm(true);
					}}
				>
					<Plus className="mr-1.5 h-3.5 w-3.5" />
					Add user
				</Button>
			</div>

			{showForm && (
				<form
					onSubmit={handleSubmit}
					className="rounded-md border bg-card p-4 space-y-3"
				>
					<p className="text-sm font-medium">
						{editingUser ? `Edit: ${editingUser.id}` : "New agency user"}
					</p>
					{!editingUser && (
						<div className="space-y-1">
							<Label htmlFor="user-id">User ID</Label>
							<Input
								id="user-id"
								value={formId}
								onChange={(e) => setFormId(e.target.value)}
								placeholder="e.g. agency-6"
								required
							/>
						</div>
					)}
					<div className="space-y-1">
						<Label htmlFor="user-role">Role</Label>
						<select
							id="user-role"
							value={formRole}
							onChange={(e) => setFormRole(e.target.value)}
							className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
						>
							{ROLES.map((r) => (
								<option key={r} value={r}>
									{r}
								</option>
							))}
						</select>
					</div>
					<div className="space-y-1">
						<Label htmlFor="user-jurisdiction">Jurisdiction</Label>
						<select
							id="user-jurisdiction"
							value={formJurisdiction}
							onChange={(e) => setFormJurisdiction(e.target.value)}
							className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm"
							required
						>
							<option value="">Select jurisdiction</option>
							{jurisdictions.map((j) => (
								<option key={j.id} value={j.id}>
									{j.name} ({j.level})
								</option>
							))}
						</select>
					</div>
					<div className="flex gap-2">
						<Button
							type="submit"
							size="sm"
							disabled={createMutation.isPending || updateMutation.isPending}
						>
							{editingUser ? "Update" : "Create"}
						</Button>
						<Button type="button" variant="ghost" size="sm" onClick={resetForm}>
							Cancel
						</Button>
					</div>
				</form>
			)}

			<div className="rounded-md border">
				<table className="w-full text-sm">
					<thead>
						<tr className="border-b bg-muted/40">
							<th className="px-4 py-2 text-left font-medium">ID</th>
							<th className="px-4 py-2 text-left font-medium">Role</th>
							<th className="px-4 py-2 text-left font-medium">Jurisdiction</th>
							<th className="px-4 py-2 text-right font-medium">Actions</th>
						</tr>
					</thead>
					<tbody>
						{users.map((user) => (
							<tr
								key={user.id}
								className="border-b last:border-0 hover:bg-muted/20"
							>
								<td className="px-4 py-2 font-mono text-xs">{user.id}</td>
								<td className="px-4 py-2">{user.role}</td>
								<td className="px-4 py-2">{user.jurisdiction_id}</td>
								<td className="px-4 py-2 text-right">
									<div className="flex items-center justify-end gap-1">
										<Button
											variant="ghost"
											size="icon"
											className="h-7 w-7"
											onClick={() => startEdit(user)}
										>
											<Pencil className="h-3.5 w-3.5" />
										</Button>
										<Button
											variant="ghost"
											size="icon"
											className="h-7 w-7 text-destructive"
											onClick={() => {
												if (confirm(`Delete user ${user.id}?`))
													deleteMutation.mutate(user.id);
											}}
										>
											<Trash2 className="h-3.5 w-3.5" />
										</Button>
									</div>
								</td>
							</tr>
						))}
						{users.length === 0 && (
							<tr>
								<td
									colSpan={4}
									className="px-4 py-6 text-center text-muted-foreground"
								>
									No users found.
								</td>
							</tr>
						)}
					</tbody>
				</table>
			</div>
		</div>
	);
}
