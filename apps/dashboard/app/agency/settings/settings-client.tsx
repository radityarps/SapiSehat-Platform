"use client";

import { Button } from "@/src/shared/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/src/shared/ui/card";
import { Input } from "@/src/shared/ui/input";
import { Label } from "@/src/shared/ui/label";
import { Separator } from "@/src/shared/ui/separator";
import { changePassword, updateProfile } from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export function SettingsClient() {
	const { agency, token, refresh, signOut } = useAgencySession();
	const router = useRouter();

	const [name, setName] = useState(agency?.name ?? "");
	const [profileMessage, setProfileMessage] = useState("");
	const [profileError, setProfileError] = useState("");

	const [currentPassword, setCurrentPassword] = useState("");
	const [newPassword, setNewPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [passwordMessage, setPasswordMessage] = useState("");
	const [passwordError, setPasswordError] = useState("");

	useEffect(() => {
		setName(agency?.name ?? "");
	}, [agency?.name]);

	async function handleProfileSubmit(e: React.FormEvent) {
		e.preventDefault();
		setProfileMessage("");
		setProfileError("");
		try {
			await updateProfile(token, { name });
			await refresh();
			setProfileMessage("Profile updated.");
		} catch (err) {
			setProfileError(err instanceof Error ? err.message : "Failed to update profile.");
		}
	}

	async function handlePasswordSubmit(e: React.FormEvent) {
		e.preventDefault();
		setPasswordMessage("");
		setPasswordError("");
		if (newPassword.length < 8) {
			setPasswordError("New password must be at least 8 characters.");
			return;
		}
		if (newPassword !== confirmPassword) {
			setPasswordError("Passwords do not match.");
			return;
		}
		try {
			await changePassword(token, { current_password: currentPassword, new_password: newPassword });
			setCurrentPassword("");
			setNewPassword("");
			setConfirmPassword("");
			setPasswordMessage("Password changed.");
		} catch (err) {
			setPasswordError(err instanceof Error ? err.message : "Failed to change password.");
		}
	}

	function handleLogout() {
		signOut();
		router.push("/login");
	}

	return (
		<div className="mx-auto max-w-2xl space-y-6">
			<div>
				<h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
				<p className="text-sm text-muted-foreground">Manage your account preferences and session.</p>
			</div>

			<Card>
				<CardHeader>
					<CardTitle className="text-base">Profile</CardTitle>
					<CardDescription>Update your display name.</CardDescription>
				</CardHeader>
				<form onSubmit={handleProfileSubmit}>
					<CardContent className="space-y-3">
						<div className="space-y-1">
							<Label htmlFor="email">Email</Label>
						<Input id="email" type="email" value={agency?.email ?? ""} disabled />
					</div>
					<div className="space-y-1">
						<Label htmlFor="name">Name</Label>
						<Input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
					</div>
					{profileMessage && <p className="text-xs text-green-600">{profileMessage}</p>}
					{profileError && <p className="text-xs text-destructive">{profileError}</p>}
				</CardContent>
				<CardFooter>
					<Button type="submit" size="sm">Save name</Button>
				</CardFooter>
			</form>
		</Card>

		<Card>
			<CardHeader>
				<CardTitle className="text-base">Password</CardTitle>
				<CardDescription>Change your account password.</CardDescription>
			</CardHeader>
			<form onSubmit={handlePasswordSubmit}>
				<CardContent className="space-y-3">
					<div className="space-y-1">
						<Label htmlFor="current-password">Current password</Label>
						<Input id="current-password" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
					</div>
					<div className="space-y-1">
						<Label htmlFor="new-password">New password</Label>
						<Input id="new-password" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
					</div>
					<div className="space-y-1">
						<Label htmlFor="confirm-password">Confirm new password</Label>
						<Input id="confirm-password" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
					</div>
					{passwordMessage && <p className="text-xs text-green-600">{passwordMessage}</p>}
					{passwordError && <p className="text-xs text-destructive">{passwordError}</p>}
				</CardContent>
				<CardFooter>
					<Button type="submit" size="sm">Change password</Button>
				</CardFooter>
			</form>
		</Card>

		<Card className="border-destructive/50">
			<CardHeader>
				<CardTitle className="text-base">Session</CardTitle>
				<CardDescription>Sign out of this dashboard session.</CardDescription>
			</CardHeader>
			<CardContent>
				<Button variant="destructive" size="sm" onClick={handleLogout}>Log out</Button>
			</CardContent>
		</Card>
	</div>
);
}

