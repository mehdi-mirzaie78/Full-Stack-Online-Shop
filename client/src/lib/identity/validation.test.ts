import { expect, it } from "vitest";
import { phoneSchema, codeSchema, userSchema } from "./validation";
it("validates phone, code and staff access fields without native form validation", () => {
  expect(phoneSchema.safeParse("+989121234567").success).toBe(true);
  expect(phoneSchema.safeParse("09121234567").success).toBe(false);
  expect(codeSchema.safeParse("012345").success).toBe(true);
  expect(codeSchema.safeParse("123").success).toBe(false);
  expect(userSchema.safeParse({ first_name: "Test", last_name: "User", phone: "+989121234567", role: "OWNER", is_active: true, is_deleted: false }).success).toBe(false);
});
it("enforces phone character length at both boundaries", () => {
  expect(phoneSchema.safeParse("+12345678").success).toBe(true);
  expect(phoneSchema.safeParse("+1234567").success).toBe(false);
  expect(phoneSchema.safeParse("+123456789012345").success).toBe(true);
  expect(phoneSchema.safeParse("+1234567890123456").success).toBe(false);
});

it("allows omitted staff passwords but rejects mismatches and short replacements", async () => {
  const { staffPasswordSchema } = await import("./validation");
  expect(staffPasswordSchema.safeParse({ password: "", confirmPassword: "" }).success).toBe(true);
  expect(staffPasswordSchema.safeParse({ password: "a-long-test-password", confirmPassword: "a-long-test-password" }).success).toBe(true);
  expect(staffPasswordSchema.safeParse({ password: "short", confirmPassword: "short" }).success).toBe(false);
  expect(staffPasswordSchema.safeParse({ password: "a-long-test-password", confirmPassword: "different" }).success).toBe(false);
});


it("requires bounded, trimmed names and accepts Persian names", async () => {
  const { personNameSchema, userSchema } = await import("./validation");
  for (const value of ["", "   ", "x".repeat(151)]) expect(personNameSchema.safeParse(value).success).toBe(false);
  expect(personNameSchema.parse("  علی  ")).toBe("علی");
  expect(userSchema.safeParse({ phone: "+989121234567", role: "CUSTOMER", is_active: true, is_deleted: false, first_name: "علی", last_name: "آزمایشی" }).success).toBe(true);
});
