import { forwardRef, InputHTMLAttributes, TextareaHTMLAttributes } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  invalid?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { invalid = false, className = "", ...rest },
  ref,
) {
  return (
    <input
      ref={ref}
      className={[
        "w-full px-3.5 py-2.5 rounded-xl bg-bg border text-sm text-fg outline-none transition",
        invalid
          ? "border-danger focus:border-danger"
          : "border-border focus:border-accent",
        "placeholder:text-muted",
        className,
      ].join(" ")}
      {...rest}
    />
  );
});

export default Input;

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean }>(
  function Textarea({ invalid = false, className = "", ...rest }, ref) {
    return (
      <textarea
        ref={ref}
        className={[
          "w-full px-3.5 py-2.5 rounded-xl bg-bg border text-sm text-fg outline-none transition resize-y",
          invalid ? "border-danger focus:border-danger" : "border-border focus:border-accent",
          "placeholder:text-muted",
          className,
        ].join(" ")}
        {...rest}
      />
    );
  },
);
