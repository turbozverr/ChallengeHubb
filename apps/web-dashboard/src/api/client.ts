import { API_BASE_URL } from "../config";
import type {
  AdminDashboardAnalyticsResponse,
  BusinessDashboardAnalyticsResponse,
  CampaignStatsResponse,
  LoginResponse,
  ModerationVideoResponse,
  PromoCodeResponse,
  ReportResponse,
  AdVideoResponse,
  SystemSettingsResponse,
  SponsoredChallengeResponse,
  WebUserResponse
} from "./types";

async function request<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    const text = await response.text();
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      throw new Error(parsed.detail ?? text ?? "Request failed");
    } catch {
      throw new Error(text || "Request failed");
    }
  }
  return (await response.json()) as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<LoginResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    }),
  adminOverview: (token: string) => request<Record<string, number>>("/admin/overview", undefined, token),
  listWebUsers: (token: string) => request<WebUserResponse[]>("/web-users", undefined, token),
  createWebUser: (
    token: string,
    payload: { full_name: string; email: string; password: string; role: string; company_name?: string }
  ) =>
    request<WebUserResponse>(
      "/web-users",
      { method: "POST", body: JSON.stringify(payload) },
      token
    ),
  updateWebUser: (
    token: string,
    userId: string,
    payload: { full_name?: string; role?: string; company_name?: string; is_active?: boolean }
  ) => request<WebUserResponse>(`/web-users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) }, token),
  deleteWebUser: (token: string, userId: string) =>
    request<{ ok: boolean }>(`/web-users/${userId}`, { method: "DELETE" }, token),
  listSponsoredChallenges: (token: string) =>
    request<SponsoredChallengeResponse[]>("/sponsored-challenges", undefined, token),
  createSponsoredChallenge: (
    token: string,
    payload: {
      title: string;
      description: string;
      reward_text: string;
      difficulty: string;
      duration_days: number;
      xp_reward: number;
      promo_mode: string;
      promo_single_code?: string;
      promo_codes?: string[];
      client_id: string;
    }
  ) =>
    request<SponsoredChallengeResponse>(
      "/sponsored-challenges",
      { method: "POST", body: JSON.stringify(payload) },
      token
    ),
  publishSponsoredChallenge: (token: string, challengeId: string) =>
    request<SponsoredChallengeResponse>(
      `/sponsored-challenges/${challengeId}/publish`,
      { method: "POST" },
      token
    ),
  updateSponsoredChallenge: (
    token: string,
    challengeId: string,
    payload: {
      title?: string;
      description?: string;
      reward_text?: string;
      difficulty?: string;
      duration_days?: number;
      xp_reward?: number;
      status?: string;
    }
  ) =>
    request<SponsoredChallengeResponse>(
      `/sponsored-challenges/${challengeId}`,
      { method: "PATCH", body: JSON.stringify(payload) },
      token
    ),
  deleteSponsoredChallenge: (token: string, challengeId: string) =>
    request<{ ok: boolean }>(`/sponsored-challenges/${challengeId}`, { method: "DELETE" }, token),
  unsentPromoCodes: (token: string) =>
    request<PromoCodeResponse[]>("/sponsored-challenges/promo/unsent", undefined, token),
  uploadAdVideo: async (token: string, payload: { title: string; file: File }) => {
    const form = new FormData();
    form.append("title", payload.title);
    form.append("file", payload.file);
    const response = await fetch(`${API_BASE_URL}/sponsored-challenges/ad-videos`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form
    });
    if (!response.ok) throw new Error(await response.text());
    return (await response.json()) as AdVideoResponse;
  },
  listAdVideos: (token: string) => request<AdVideoResponse[]>("/sponsored-challenges/ad-videos", undefined, token),
  moderationVideoQueue: (token: string) =>
    request<ModerationVideoResponse[]>("/moderation/videos/queue", undefined, token),
  decideVideo: (token: string, videoId: string, decision: "APPROVE" | "BLOCK") =>
    request<ModerationVideoResponse>(
      `/moderation/videos/${videoId}/decision`,
      { method: "POST", body: JSON.stringify({ decision }) },
      token
    ),
  moderationReportsQueue: (token: string) =>
    request<ReportResponse[]>("/moderation/reports/queue", undefined, token),
  decideReport: (token: string, reportId: string, decision: "CONFIRM" | "REJECT") =>
    request<ReportResponse>(
      `/moderation/reports/${reportId}/decision`,
      { method: "POST", body: JSON.stringify({ decision }) },
      token
    ),
  adminVideos: (token: string) => request<ModerationVideoResponse[]>("/moderation/videos", undefined, token),
  updateVideo: (token: string, videoId: string, payload: { url?: string; description?: string; status?: string; is_ad?: boolean }) =>
    request<ModerationVideoResponse>(`/moderation/videos/${videoId}`, { method: "PATCH", body: JSON.stringify(payload) }, token),
  deleteVideo: (token: string, videoId: string) =>
    request<{ ok: boolean }>(`/moderation/videos/${videoId}`, { method: "DELETE" }, token),
  campaignStats: (token: string) => request<CampaignStatsResponse[]>("/analytics/campaigns", undefined, token),
  adminDashboardAnalytics: (token: string) =>
    request<AdminDashboardAnalyticsResponse>("/analytics/admin-dashboard", undefined, token),
  businessDashboardAnalytics: (token: string) =>
    request<BusinessDashboardAnalyticsResponse>("/analytics/business-dashboard", undefined, token),
  getSettings: (token: string) => request<SystemSettingsResponse>("/settings", undefined, token),
  updateSettings: (token: string, payload: { ai_confidence_threshold?: number; report_limit?: number }) =>
    request<SystemSettingsResponse>("/settings", { method: "PATCH", body: JSON.stringify(payload) }, token)
};
