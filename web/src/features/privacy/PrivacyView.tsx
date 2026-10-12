"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/core/api/client";
import { useAuth } from "@/core/auth/auth-context";
import { useTranslation } from "@/core/i18n/context";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Download, Trash2, AlertTriangle } from "lucide-react";
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
    onSuccess: (data: unknown) => {
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
      toast.success(t.profile.exportSuccess);
    },
    onError: (err: unknown) => {
      toast.error((err as Error).message || t.profile.exportError);
    },
  });

  // Delete Account Mutation
  const deleteAccountMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.DELETE("/api/v1/users/me/account");
      return res.data;
    },
    onSuccess: () => {
      toast.success(t.profile.deleteSuccess);
      setIsDeleteOpen(false);
      logout();
    },
    onError: (err: unknown) => {
      toast.error((err as Error).message || t.profile.deleteError);
    },
  });

  return (
    <section className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
          {t.profile.gdprTitle}
        </h1>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
          {t.profile.gdprSubtitle}
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4">
          <div className="space-y-1">
            <CardTitle className="text-base flex items-center gap-2">
              <Download className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              <span>{t.profile.exportTitle}</span>
            </CardTitle>
            <CardDescription className="text-xs">
              {t.profile.exportDesc}
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

      <Card className="border-rose-200 dark:border-rose-900/60 bg-rose-50/20 dark:bg-rose-950/20">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4">
          <div className="space-y-1">
            <CardTitle className="text-base text-rose-800 dark:text-rose-200 flex items-center gap-2">
              <Trash2 className="h-4 w-4" />
              <span>{t.profile.deleteTitle}</span>
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

      <Dialog
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title={t.profile.deleteConfirmTitle}
        description={t.profile.deleteConfirmDesc}
      >
        <div className="space-y-4 pt-2">
          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs text-rose-800 dark:text-rose-200 flex items-start gap-2.5">
            <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
            <span>
              {t.profile.deleteWarning}
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
              {t.profile.deleteAccount}
            </Button>
          </div>
        </div>
      </Dialog>
    </section>
  );
}
