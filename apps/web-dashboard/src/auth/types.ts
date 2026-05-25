export type WebRole = "ADMIN" | "MODERATOR" | "BUSINESS_CLIENT";

export interface AuthUser {
  id: string;
  fullName: string;
  email: string;
  role: WebRole;
}
