export const WEB_ROLES = ["ADMIN", "MODERATOR", "BUSINESS_CLIENT"] as const;

export type WebRole = (typeof WEB_ROLES)[number];

export interface WebUserProfile {
  id: string;
  email: string;
  fullName: string;
  role: WebRole;
}
