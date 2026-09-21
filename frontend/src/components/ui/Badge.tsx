import type { ReactNode } from "react";

type BadgeTone = "cyan" | "purple" | "success" | "warning" | "danger";

interface BadgeProps {
  children: ReactNode;
  tone?: BadgeTone;
}

export function Badge({ children, tone = "cyan" }: BadgeProps) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}