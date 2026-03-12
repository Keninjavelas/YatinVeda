import { z } from 'zod'

// ─── Reusable field validators ────────────────────────────────────────
const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .max(71, 'Password must be at most 71 characters')
  .regex(/[A-Z]/, 'Password must include an uppercase letter')
  .regex(/[a-z]/, 'Password must include a lowercase letter')
  .regex(/[0-9]/, 'Password must include a number')

const emailSchema = z.string().email('Please enter a valid email address')

// ─── Login ────────────────────────────────────────────────────────────
export const loginSchema = z.object({
  email: z.string().min(1, 'Email or username is required'),
  password: z.string().min(1, 'Password is required'),
})
export type LoginFormData = z.infer<typeof loginSchema>

// ─── Forgot Password ─────────────────────────────────────────────────
export const forgotPasswordSchema = z.object({
  email: emailSchema,
})
export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>

// ─── Reset Password ──────────────────────────────────────────────────
export const resetPasswordSchema = z
  .object({
    password: passwordSchema,
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })
export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>

// ─── Signup (common) ─────────────────────────────────────────────────
const signupBaseSchema = z.object({
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(30, 'Username must be at most 30 characters'),
  email: emailSchema,
  full_name: z.string().min(1, 'Full name is required'),
  password: passwordSchema,
  confirmPassword: z.string(),
})

export const userSignupSchema = signupBaseSchema.refine(
  (d) => d.password === d.confirmPassword,
  { message: 'Passwords do not match', path: ['confirmPassword'] },
)
export type UserSignupFormData = z.infer<typeof userSignupSchema>

export const practitionerSignupSchema = signupBaseSchema
  .extend({
    professional_title: z.string().min(1, 'Professional title is required'),
    bio: z.string().min(50, 'Bio must be at least 50 characters'),
    specializations: z.array(z.string()).min(1, 'Select at least one specialization'),
    experience_years: z.coerce.number().min(0, 'Experience must be 0 or more'),
    certification_type: z.string().min(1, 'Select a certification type'),
    issuing_authority: z.string().min(1, 'Issuing authority is required'),
    languages: z.array(z.string()).min(1, 'Select at least one language'),
    price_per_hour: z.coerce.number().min(0).optional(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })
export type PractitionerSignupFormData = z.infer<typeof practitionerSignupSchema>

// ─── Birth Chart ─────────────────────────────────────────────────────
export const chartSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  birthDate: z.string().min(1, 'Birth date is required'),
  birthTime: z.string().min(1, 'Birth time is required'),
  birthPlace: z.string().min(1, 'Birth place is required'),
  latitude: z.coerce.number(),
  longitude: z.coerce.number(),
  timezone: z.string(),
})
export type ChartFormData = z.infer<typeof chartSchema>

// ─── MFA Verification ────────────────────────────────────────────────
export const mfaCodeSchema = z.object({
  code: z
    .string()
    .length(6, 'Code must be exactly 6 digits')
    .regex(/^\d+$/, 'Code must be numeric'),
})
export type MfaCodeFormData = z.infer<typeof mfaCodeSchema>

// ─── Video Consult Lookup ────────────────────────────────────────────
export const videoConsultSchema = z.object({
  bookingId: z.string().min(1, 'Booking ID is required'),
})
export type VideoConsultFormData = z.infer<typeof videoConsultSchema>
