import { HTMLAttributes, forwardRef } from "react";

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  tone?: "default" | "success" | "warning" | "danger";
  noPadding?: boolean;
}

const TONE: Record<NonNullable<CardProps["tone"]>, string> = {
  default: "border-border",
  success: "border-success/40",
  warning: "border-warning/40",
  danger: "border-danger/40",
};

const Card = forwardRef<HTMLDivElement, CardProps>(function Card(
  { tone = "default", noPadding = false, className = "", children, ...rest },
  ref,
) {
  return (
    <div
      ref={ref}
      className={[
        "bg-surface border rounded-lg",
        TONE[tone],
        noPadding ? "" : "p-4",
        className,
      ].join(" ")}
      {...rest}
    >
      {children}
    </div>
  );
});

export default Card;

export function CardHeader({ className = "", children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={`mb-3 ${className}`} {...rest}>
      {children}
    </div>
  );
}

export function CardTitle({ className = "", children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <h3 className={`text-base font-semibold ${className}`} {...rest}>
      {children}
    </h3>
  );
}

export function CardDescription({ className = "", children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <p className={`text-xs text-muted mt-1 ${className}`} {...rest}>
      {children}
    </p>
  );
}
