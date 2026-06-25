"use client";

import { Button } from "@/src/shared/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/src/shared/ui/dialog";
import { Label } from "@/src/shared/ui/label";
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/src/shared/ui/select";
import { Textarea } from "@/src/shared/ui/textarea";
import { createAgencyFollowUp } from "@/src/shared/api/client";
import { useAgencySession } from "@/src/features/auth/session-context";
import type { RiskSignalItem } from "@/src/shared/types/api";
import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";

export function RecordFollowUpDialog({
	signal,
	farmers,
	open,
	onClose,
	onSaved,
}: {
	signal: RiskSignalItem | null;
	farmers: { id: string; name: string }[];
	open: boolean;
	onClose: () => void;
	onSaved: () => void;
}) {
	const { token, agencyUserId } = useAgencySession();
	const [farmerId, setFarmerId] = useState("");
	const [publicMessage, setPublicMessage] = useState(
		"Petugas akan meninjau sinyal risiko ini. Ini bukan diagnosis.",
	);
	const [internalNotes, setInternalNotes] = useState("");

	useEffect(() => {
		if (signal) {
			setFarmerId("");
			setPublicMessage(
				"Petugas akan meninjau sinyal risiko ini. Ini bukan diagnosis.",
			);
			setInternalNotes(
				`Created from risk signal ${signal.id} (${signal.disease_class}, ${signal.jurisdiction_id}, risk=${signal.risk_level}).`,
			);
		}
	}, [signal, open]);

	const mutation = useMutation({
		mutationFn: () =>
			createAgencyFollowUp(token, agencyUserId, {
				farmer_id: farmerId,
				status: "needs_follow_up",
				public_message: publicMessage,
				internal_notes: internalNotes,
			}),
		onSuccess: () => {
			toast.success("Follow-up created.");
			onSaved();
		},
		onError: (error) => {
			toast.error(
				error instanceof Error ? error.message : "Failed to create follow-up.",
			);
		},
	});

	return (
		<Dialog
			open={open}
			onOpenChange={(v) => {
				if (!v) onClose();
			}}
		>
			<DialogContent className="sm:max-w-md">
				<DialogHeader>
					<DialogTitle>Record follow-up</DialogTitle>
					<DialogDescription className="sr-only">
						Create a follow-up from the selected risk signal.
					</DialogDescription>
				</DialogHeader>

				<form
					className="space-y-3"
					onSubmit={(e) => {
						e.preventDefault();
						mutation.mutate();
					}}
				>
					{signal && (
						<div className="rounded-md border bg-muted/20 px-3 py-2 text-xs space-y-1">
							<p>
								<span className="text-muted-foreground">Signal:</span>{" "}
								{signal.id}
							</p>
							<p>
								<span className="text-muted-foreground">Class:</span>{" "}
								{signal.disease_class.replace(/_/g, " ")}
							</p>
							<p>
								<span className="text-muted-foreground">District:</span>{" "}
								{signal.jurisdiction_id}
							</p>
						</div>
					)}
					<div className="space-y-1.5">
						<Label htmlFor="rf-farmer">Farmer</Label>
						<Select value={farmerId} onValueChange={setFarmerId}>
							<SelectTrigger id="rf-farmer">
								<SelectValue placeholder="Select farmer" />
							</SelectTrigger>
							<SelectContent>
								{farmers.map((f) => (
									<SelectItem key={f.id} value={f.id}>
										{f.name} ({f.id})
									</SelectItem>
								))}
							</SelectContent>
						</Select>
					</div>
					<div className="space-y-1.5">
						<Label htmlFor="rf-message">Farmer-safe message</Label>
						<Textarea
							id="rf-message"
							value={publicMessage}
							onChange={(e) => setPublicMessage(e.target.value)}
							rows={2}
							required
						/>
					</div>
					<div className="space-y-1.5">
						<Label htmlFor="rf-notes">Internal notes</Label>
						<Textarea
							id="rf-notes"
							value={internalNotes}
							onChange={(e) => setInternalNotes(e.target.value)}
							rows={2}
							placeholder="Agency-only note; avoid diagnosis or outbreak confirmation."
						/>
					</div>

					{mutation.isError && (
						<p className="text-sm text-destructive">{mutation.error.message}</p>
					)}

					<DialogFooter>
						<Button type="button" variant="ghost" onClick={onClose}>
							Cancel
						</Button>
						<Button type="submit" disabled={mutation.isPending || !farmerId}>
							{mutation.isPending ? "Saving..." : "Create"}
						</Button>
					</DialogFooter>
				</form>
			</DialogContent>
		</Dialog>
	);
}
