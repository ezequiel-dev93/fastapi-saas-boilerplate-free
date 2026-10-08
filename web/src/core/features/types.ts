import type { LucideIcon } from "lucide-react";

export type FeatureTier = "free" | "pro";

export interface FeatureManifest {
  id: string;
  tier: FeatureTier;
  titleKey: "overview" | "profile" | "billing" | "teams" | "aiChat" | "usage" | "apiKeys" | "privacy";
  href: string;
  icon: LucideIcon;
  badge?: string;
  order: number;
}
