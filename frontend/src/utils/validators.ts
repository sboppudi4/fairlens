import { z } from "zod";

export const emailSchema = z.string().email("Invalid email address");
export const passwordSchema = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .max(128, "Password is too long");

export const loginSchema = z.object({
  email: emailSchema,
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z.object({
  email: emailSchema,
  password: passwordSchema,
  full_name: z.string().min(1, "Full name is required").max(255),
});

export const auditConfigSchema = z.object({
  name: z.string().min(1, "Audit name is required").max(255),
  description: z.string().max(2000).optional(),
  label_column: z.string().min(1, "Select the ground-truth label column"),
  prediction_column: z.string().min(1, "Select the model prediction column"),
  sensitive_attributes: z
    .array(z.string())
    .min(1, "Select at least one sensitive attribute")
    .max(5, "At most 5 sensitive attributes"),
  positive_label: z.string().min(1, "Specify the positive label value"),
  favorable_prediction: z.string().min(1, "Specify the favorable prediction value"),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
export type AuditConfigInput = z.infer<typeof auditConfigSchema>;
