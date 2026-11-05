import { z } from "zod";
import { roles } from "./api";
export const phoneSchema = z.string().min(9, "Phone numbers must include at least 8 digits and +.").max(16, "Phone numbers cannot exceed 15 digits and +.").regex(/^\+[1-9][0-9]{7,14}$/, "Use an international number, such as +989121234567.");
export const codeSchema = z.string().regex(/^[0-9]{6}$/, "Enter the six-digit verification code.");
export const personNameSchema = z.string().trim().min(1, "Enter a name.").max(150, "Names cannot exceed 150 characters.");
export const userSchema = z.object({ first_name: personNameSchema, last_name: personNameSchema, phone: phoneSchema, role: z.enum(roles), is_active: z.boolean(), is_deleted: z.boolean() });

export const passwordSchema = z.string().min(1, "Enter your password.").max(128, "Password cannot exceed 128 characters.");


export const staffPasswordSchema = z.object({
  password: z.string().max(128, "Password cannot exceed 128 characters."),
  confirmPassword: z.string(),
}).superRefine(({ password, confirmPassword }, context) => {
  if (password && password.length < 8) context.addIssue({ code: "custom", message: "Use at least 8 characters.", path: ["password"] });
  if (password !== confirmPassword) context.addIssue({ code: "custom", message: "Passwords do not match.", path: ["confirmPassword"] });
});
