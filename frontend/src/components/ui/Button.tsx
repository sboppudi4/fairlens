import { forwardRef, ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "danger" | "outline";
type Size = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

const VARIANT: Record<Variant, string> = {
  primary: "bg-accent text-white hover:bg-accent/90 disabled:bg-accent/40",
  ghost: "bg-transparent text-fg hover:bg-surface border border-border",
  danger: "bg-danger text-white hover:bg-danger/90",
  outline: "bg-transparent border border-accent text-accent hover:bg-accent/10",
};

const SIZE: Record<Size, string> = {
  sm: "py-1 px-2 text-xs gap-1",
  md: "py-2 px-3 text-sm gap-1.5",
  lg: "py-2.5 px-4 text-base gap-2",
};

const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", loading = false, disabled, className = "", children, ...rest },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={[
        "inline-flex items-center justify-center font-medium rounded-md transition-colors disabled:cursor-not-allowed disabled:opacity-60",
        VARIANT[variant],
        SIZE[size],
        className,
      ].join(" ")}
      {...rest}
    >
      {loading && (
        <span
          className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin"
          aria-hidden="true"
        />
      )}
      {children}
    </button>
  );
});

export default Button;
