import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z.string().default("http://localhost:8000"),
  NEXT_PUBLIC_COGNITO_USER_POOL_ID: z.string().default(""),
  NEXT_PUBLIC_COGNITO_CLIENT_ID: z.string().default(""),
  NEXT_PUBLIC_COGNITO_DOMAIN: z.string().default(""),
  NEXT_PUBLIC_ENVIRONMENT: z.enum(["development", "test", "production"]).default("development"),
});

export const env = envSchema.parse({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  NEXT_PUBLIC_COGNITO_USER_POOL_ID: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID || "",
  NEXT_PUBLIC_COGNITO_CLIENT_ID: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID || "",
  NEXT_PUBLIC_COGNITO_DOMAIN: process.env.NEXT_PUBLIC_COGNITO_DOMAIN || "",
  NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT || "development",
});
