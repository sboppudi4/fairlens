import { LabelHTMLAttributes } from "react";

export interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

export default function Label({ required, className = "", children, ...rest }: LabelProps) {
  return (
    <label className={`block text-sm font-medium mb-1 text-fg ${className}`} {...rest}>
      {children}
      {required && <span className="text-danger ml-0.5">*</span>}
    </label>
  );
}
