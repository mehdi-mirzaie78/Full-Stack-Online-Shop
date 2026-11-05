import { z } from "zod";
import { roles } from "./api";
export const phoneSchema = z.string().min(9, "Phone numbers must include at least 8 digits and +.").max(16, "Phone numbers cannot exceed 15 digits and +.").regex(/^\+[1-9][0-9]{7,14}$/, "Use an international number, such as +989121234567.");
export const codeSchema = z.string().regex(/^[0-9]{6}$/, "Enter the six-digit verification code.");
export const userSchema = z.object({ phone: phoneSchema, role: z.enum(roles), is_active: z.boolean(), is_deleted: z.boolean() });

export const passwordSchema = z.string().min(1, "Enter your password.").max(128, "Password cannot exceed 128 characters.");
