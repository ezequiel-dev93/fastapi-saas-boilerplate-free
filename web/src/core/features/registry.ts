import {
  LayoutDashboard,
  User,
  ShieldCheck,
} from "lucide-react";
import type { FeatureManifest } from "./types";

export const FEATURE_REGISTRY: FeatureManifest[] = [
  {
    id: "overview",
    tier: "free",
    titleKey: "overview",
    href: "/dashboard",
    icon: LayoutDashboard,
    order: 1,
  },
  {
    id: "profile",
    tier: "free",
    titleKey: "profile",
    href: "/dashboard/profile",
    icon: User,
    order: 2,
  },
  {
    id: "privacy",
    tier: "free",
    titleKey: "privacy",
    href: "/dashboard/privacy",
    icon: ShieldCheck,
    order: 3,
  },
];

export function getRegisteredFeatures(filterTier?: "free" | "pro"): FeatureManifest[] {
  if (filterTier === "free") {
    return FEATURE_REGISTRY.filter((f) => f.tier === "free");
  }
  return [...FEATURE_REGISTRY].sort((a, b) => a.order - b.order);
}
