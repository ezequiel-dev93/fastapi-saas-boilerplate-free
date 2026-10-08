"use client";

import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/core/api/client";
import { useTranslation } from "@/core/i18n/context";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User, Check, Shield } from "lucide-react";
import { toast } from "sonner";

export function ProfileView() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");

  const { data: userProfile, isLoading } = useQuery({
    queryKey: ["user-me"],
    queryFn: async () => {
      const res = await apiClient.GET("/api/v1/users/me");
      return res.data;
    },
  });

  useEffect(() => {
    if (userProfile?.profile) {
      setFirstName(userProfile.profile.first_name || "");
      setLastName(userProfile.profile.last_name || "");
    }
  }, [userProfile]);

  const updateMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.PATCH("/api/v1/users/me", {
        body: {
          first_name: firstName,
          last_name: lastName,
        },
      });
      return res.data;
    },
    onSuccess: () => {
      toast.success(t.common.success);
      queryClient.invalidateQueries({ queryKey: ["user-me"] });
    },
    onError: (err: unknown) => {
      toast.error((err as Error).message || t.common.error);
    },
  });

  return (
    <div className="space-y-8 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
          {t.profile.title}
        </h1>
        <p className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
          {t.profile.subtitle}
        </p>
      </div>

      {/* Profile Form Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Personal Information</CardTitle>
          <CardDescription className="text-xs">
            Your name and contact details synchronized with your account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              updateMutation.mutate();
            }}
            className="space-y-4"
          >
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs">
                {t.profile.email}
              </Label>
              <Input
                id="email"
                value={userProfile?.profile?.email || ""}
                disabled
                className="bg-neutral-50 dark:bg-neutral-900/50 cursor-not-allowed text-neutral-400"
              />
              <p className="text-[11px] text-neutral-400">
                Email address is managed by your identity provider (Cognito).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="firstName" className="text-xs">
                  {t.profile.firstName}
                </Label>
                <Input
                  id="firstName"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="First name"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="lastName" className="text-xs">
                  {t.profile.lastName}
                </Label>
                <Input
                  id="lastName"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  placeholder="Last name"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button type="submit" isLoading={updateMutation.isPending} className="text-xs">
                {t.common.save}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
