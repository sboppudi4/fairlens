import { HTMLAttributes } from "react";

type Variant = "default" | "success" | "warning" | "danger" | "info";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

const VARIANT: Record<Variant, string> = {
  default: "bg-muted/15 text-muted",
  success: "bg-success/15 text-success",
  warning: "bg-warning/15 text-warning",
  danger: "bg-danger/15 text-danger",
  info: "bg-accent/15 text-accent",
};

export default function Badge({ variant = "default", className = "", children, ...rest }: BadgeProps) {
  return (
    <span
      className={[
        "inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium uppercase tracking-wider",
        VARIANT[variant],
        className,
      ].join(" ")}
      {...rest}
    >
      {children}
    </span>
  );
}
