"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/core/api/client";
import { useAuth } from "@/core/auth/auth-context";
import { useTranslation } from "@/core/i18n/context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { ShieldCheck, Download, Trash2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

export function PrivacyView() {
  const { logout } = useAuth();
  const { t } = useTranslation();
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // Export Data Mutation
  const exportMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.GET("/api/v1/users/me/export");
      return res.data;
    },
    onSuccess: (data: any) => {
      // Trigger browser download as a JSON file
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `user-data-export-${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      toast.success("GDPR export file generated successfully.");
    },
    onError: (err: unknown) => {
      toast.error((err as Error).message || "Failed to generate export file.");
    },
  });

  // Delete Account Mutation
  const deleteAccountMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.DELETE("/api/v1/users/me/account");
      return res.data;
    },
    onSuccess: () => {
      toast.success("Account successfully anonymized and deleted.");
      setIsDeleteOpen(false);
      logout();
    },
    onError: (err: unknown) => {
      toast.error((err as Error).message || "Account deletion was blocked.");
    },
  });

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
          {t.profile.gdprTitle}
        </h1>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
          Exercise your European GDPR data portability and erasure rights.
        </p>
      </div>

      {/* Data Export Card (Art. 15 & 20) */}
      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4">
          <div className="space-y-1">
            <CardTitle className="text-base flex items-center gap-2">
              <Download className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              <span>Right of Access & Data Portability</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Download a machine-readable JSON archive containing all personal data and settings associated with your account.
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportMutation.mutate()}
            isLoading={exportMutation.isPending}
            className="text-xs shrink-0"
          >
            {t.profile.exportData}
          </Button>
        </CardHeader>
      </Card>

      {/* Account Erasure Card (Art. 17) */}
      <Card className="border-rose-200 dark:border-rose-900/60 bg-rose-50/20 dark:bg-rose-950/20">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4">
          <div className="space-y-1">
            <CardTitle className="text-base text-rose-800 dark:text-rose-200 flex items-center gap-2">
              <Trash2 className="h-4 w-4" />
              <span>Right to Erasure (Delete Account)</span>
            </CardTitle>
            <CardDescription className="text-xs text-rose-600/80 dark:text-rose-400/80">
              {t.profile.deleteWarning}
            </CardDescription>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setIsDeleteOpen(true)}
            className="text-xs shrink-0"
          >
            {t.profile.deleteAccount}
          </Button>
        </CardHeader>
      </Card>

      {/* Confirmation Modal */}
      <Dialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Confirm Account Deletion"
        description="This operation cannot be undone. Are you sure you wish to proceed?"
      >
        <div className="space-y-4 pt-2">
          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-800 dark:text-rose-200 flex items-start gap-2.5">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>
              All your personal data will be anonymized and deleted.
            </span>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={() => setIsDeleteOpen(false)}>
              {t.common.cancel}
            </Button>
            <Button
              variant="destructive"
              isLoading={deleteAccountMutation.isPending}
              onClick={() => deleteAccountMutation.mutate()}
            >
              Permanently Delete Account
            </Button>
          </div>
        </div>
      </Dialog>
    </div>
  );
}
