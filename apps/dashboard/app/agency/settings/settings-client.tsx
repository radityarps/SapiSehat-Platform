"use client";

import {
	AlertDialog,
	AlertDialogAction,
	AlertDialogCancel,
	AlertDialogContent,
	AlertDialogDescription,
	AlertDialogFooter,
	AlertDialogHeader,
	AlertDialogTitle,
	AlertDialogTrigger,
} from "@/src/shared/ui/alert-dialog";
import { Button } from "@/src/shared/ui/button";
import {
	Card,
	CardContent,
	CardDescription,
	CardFooter,
	CardHeader,
	CardTitle,
} from "@/src/shared/ui/card";
import { Input } from "@/src/shared/ui/input";
import { Label } from "@/src/shared/ui/label";
import { changePassword, updateProfile } from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { toast } from "sonner";

export function SettingsClient() {
	const { agency, token, refresh, signOut } = useAgencySession();
	const router = useRouter();

	const [name, setName] = useState(agency?.name ?? "");
	const [currentPassword, setCurrentPassword] = useState("");
	const [newPassword, setNewPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");

	useEffect(() => {
		setName(agency?.name ?? "");
	}, [agency?.name]);

	async function doSaveName() {
		try {
			await updateProfile(token, { name });
			await refresh();
			toast.success("Profile updated.");
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : "Failed to update profile.",
			);
		}
	}

	async function doChangePassword() {
		if (newPassword.length < 8) {
			toast.error("New password must be at least 8 characters.");
			return;
		}
		if (newPassword !== confirmPassword) {
			toast.error("Passwords do not match.");
			return;
		}
		try {
			await changePassword(token, {
				current_password: currentPassword,
				new_password: newPassword,
			});
			toast.success("Password changed. Signing you out…");
			setTimeout(() => {
				signOut();
				router.push("/login");
			}, 1500);
		} catch (err) {
			toast.error(
				err instanceof Error ? err.message : "Failed to change password.",
			);
		}
	}

	function doLogout() {
		signOut();
		router.push("/login");
	}

	return (
		<div className="mx-auto max-w-2xl space-y-6">
			<div>
				<h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
				<p className="text-sm text-muted-foreground">
					Manage your account preferences and session.
				</p>
			</div>

			{/* Profile */}
			<Card>
				<CardHeader>
					<CardTitle className="text-base">Profile</CardTitle>
					<CardDescription>Update your display name.</CardDescription>
				</CardHeader>
				<CardContent className="space-y-3">
					<div className="space-y-1">
						<Label htmlFor="email">Email</Label>
						<Input
							id="email"
							type="email"
							value={agency?.email ?? ""}
							disabled
						/>
					</div>
					<div className="space-y-1">
						<Label htmlFor="name">Name</Label>
						<Input
							id="name"
							value={name}
							onChange={(e) => setName(e.target.value)}
						/>
					</div>
				</CardContent>
				<CardFooter className="pt-2">
					<AlertDialog>
						<AlertDialogTrigger asChild>
							<Button
								size="sm"
								disabled={!name.trim() || name === agency?.name}
							>
								Save name
							</Button>
						</AlertDialogTrigger>
						<AlertDialogContent>
							<AlertDialogHeader>
								<AlertDialogTitle>Save profile changes?</AlertDialogTitle>
								<AlertDialogDescription>
									Your display name will be updated to <strong>{name}</strong>.
								</AlertDialogDescription>
							</AlertDialogHeader>
							<AlertDialogFooter>
								<AlertDialogCancel>Cancel</AlertDialogCancel>
								<AlertDialogAction onClick={doSaveName}>Save</AlertDialogAction>
							</AlertDialogFooter>
						</AlertDialogContent>
					</AlertDialog>
				</CardFooter>
			</Card>

			{/* Password */}
			<Card>
				<CardHeader>
					<CardTitle className="text-base">Password</CardTitle>
					<CardDescription>
						Change your account password. You will be signed out after.
					</CardDescription>
				</CardHeader>
				<CardContent className="space-y-3">
					<div className="space-y-1">
						<Label htmlFor="current-password">Current password</Label>
						<Input
							id="current-password"
							type="password"
							value={currentPassword}
							onChange={(e) => setCurrentPassword(e.target.value)}
						/>
					</div>
					<div className="space-y-1">
						<Label htmlFor="new-password">New password</Label>
						<Input
							id="new-password"
							type="password"
							value={newPassword}
							onChange={(e) => setNewPassword(e.target.value)}
						/>
					</div>
					<div className="space-y-1">
						<Label htmlFor="confirm-password">Confirm new password</Label>
						<Input
							id="confirm-password"
							type="password"
							value={confirmPassword}
							onChange={(e) => setConfirmPassword(e.target.value)}
						/>
					</div>
				</CardContent>
				<CardFooter className="pt-4">
					<AlertDialog>
						<AlertDialogTrigger asChild>
							<Button
								size="sm"
								disabled={!currentPassword || !newPassword || !confirmPassword}
							>
								Change password
							</Button>
						</AlertDialogTrigger>
						<AlertDialogContent>
							<AlertDialogHeader>
								<AlertDialogTitle>Change password?</AlertDialogTitle>
								<AlertDialogDescription>
									You will be signed out immediately after your password is
									changed.
								</AlertDialogDescription>
							</AlertDialogHeader>
							<AlertDialogFooter>
								<AlertDialogCancel>Cancel</AlertDialogCancel>
								<AlertDialogAction onClick={doChangePassword}>
									Change &amp; sign out
								</AlertDialogAction>
							</AlertDialogFooter>
						</AlertDialogContent>
					</AlertDialog>
				</CardFooter>
			</Card>

			{/* Logout */}
			<Card className="border-destructive/50">
				<CardHeader>
					<CardTitle className="text-base">Session</CardTitle>
					<CardDescription>Sign out of this dashboard session.</CardDescription>
				</CardHeader>
				<CardContent>
					<AlertDialog>
						<AlertDialogTrigger asChild>
							<Button variant="destructive" size="sm">
								Log out
							</Button>
						</AlertDialogTrigger>
						<AlertDialogContent>
							<AlertDialogHeader>
								<AlertDialogTitle>Sign out?</AlertDialogTitle>
								<AlertDialogDescription>
									You will be returned to the login screen.
								</AlertDialogDescription>
							</AlertDialogHeader>
							<AlertDialogFooter>
								<AlertDialogCancel>Cancel</AlertDialogCancel>
								<AlertDialogAction
									onClick={doLogout}
									className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
								>
									Sign out
								</AlertDialogAction>
							</AlertDialogFooter>
						</AlertDialogContent>
					</AlertDialog>
				</CardContent>
			</Card>
		</div>
	);
}
