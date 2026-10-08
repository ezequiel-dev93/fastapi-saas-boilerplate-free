import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "success" | "warning" | "destructive" | "outline";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variants = {
    default: "bg-indigo-100 text-indigo-700 dark:bg-indigo-950/80 dark:text-indigo-300 border-transparent",
    secondary: "bg-neutral-100 text-neutral-800 dark:bg-neutral-800 dark:text-neutral-200 border-transparent",
    success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/80 dark:text-emerald-300 border-transparent",
    warning: "bg-amber-100 text-amber-700 dark:bg-amber-950/80 dark:text-amber-300 border-transparent",
    destructive: "bg-rose-100 text-rose-700 dark:bg-rose-950/80 dark:text-rose-300 border-transparent",
    outline: "border-neutral-300 dark:border-neutral-700 text-neutral-800 dark:text-neutral-200",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
