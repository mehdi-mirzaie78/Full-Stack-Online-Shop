import { expect, it } from "vitest";
import { phoneSchema, codeSchema, userSchema } from "./validation";
it("validates phone, code and staff access fields without native form validation", () => {
  expect(phoneSchema.safeParse("+989121234567").success).toBe(true);
  expect(phoneSchema.safeParse("09121234567").success).toBe(false);
  expect(codeSchema.safeParse("012345").success).toBe(true);
  expect(codeSchema.safeParse("123").success).toBe(false);
  expect(userSchema.safeParse({ phone: "+989121234567", role: "OWNER", is_active: true, is_deleted: false }).success).toBe(false);
});
it("enforces phone character length at both boundaries", () => {
  expect(phoneSchema.safeParse("+12345678").success).toBe(true);
  expect(phoneSchema.safeParse("+1234567").success).toBe(false);
  expect(phoneSchema.safeParse("+123456789012345").success).toBe(true);
  expect(phoneSchema.safeParse("+1234567890123456").success).toBe(false);
});
