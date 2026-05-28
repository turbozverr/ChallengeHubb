import type { WebRole } from "../auth/types";

export interface MeResponse {
  id: string;
  full_name: string;
  email: string;
  role: WebRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: MeResponse;
}

export interface WebUserResponse {
  id: string;
  full_name: string;
  email: string;
  role: WebRole;
  company_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface MobileUserResponse {
  id: string;
  username: string;
  full_name: string;
  email: string;
  avatar_url: string | null;
  bio: string | null;
  xp: number;
  is_premium: boolean;
  status: string;
  created_at: string;
}

export interface SponsoredChallengeResponse {
  id: string;
  title: string;
  description: string;
  reward_text: string;
  difficulty: string;
  duration_days: number;
  xp_reward: number;
  promo_mode: string;
  promo_single_code: string | null;
  client_id: string;
  client_company_name: string;
  status: string;
  created_by_admin_id: string;
  created_at: string;
  published_at: string | null;
}

export interface UserChallengeAdminResponse {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  duration_days: number;
  xp_reward: number;
  created_by_user_id: string;
  status: string;
  created_at: string;
}

export interface ModerationVideoResponse {
  id: string;
  challenge_id: string;
  author_user_id: string;
  url: string;
  description: string | null;
  ai_reason: string | null;
  ai_confidence: number | null;
  ai_status: string;
  status: string;
  reports_count: number;
  views_count: number;
  likes_count: number;
  shares_count: number;
  created_at: string;
}

export interface ReportResponse {
  id: string;
  video_id: string;
  video_url: string | null;
  reason: string;
  status: string;
  created_at: string;
}

export interface CampaignStatsResponse {
  challenge_id: string;
  title: string;
  client_company_name: string;
  views: number;
  completed: number;
  conversion_rate: number;
}

export interface DateValuePoint {
  date: string;
  value: number;
}

export interface MobileRegistrationsPoint {
  date: string;
  users: number;
}

export interface TopChallengePoint {
  challenge_id: string;
  title: string;
  submissions: number;
  views: number;
  shares: number;
  completion_rate: number;
}

export interface ContentGrowthPoint {
  date: string;
  ad_videos: number;
  regular_videos: number;
}

export interface AdminDashboardAnalyticsResponse {
  dau_wau_mau: DateValuePoint[];
  mobile_registrations: MobileRegistrationsPoint[];
  moderation_decision_time_hours: DateValuePoint[];
  top_challenges_engagement: TopChallengePoint[];
  content_growth: ContentGrowthPoint[];
  ai_quality_overturned_rate: DateValuePoint[];
}

export interface InteractionPoint {
  date: string;
  likes: number;
  shares: number;
  comments: number;
}

export interface BusinessDashboardAnalyticsResponse {
  views_by_day: DateValuePoint[];
  submissions_by_day: DateValuePoint[];
  completed_by_day: DateValuePoint[];
  conversion_by_day: DateValuePoint[];
  interactions_by_day: InteractionPoint[];
}

export interface PromoCodeResponse {
  id: string;
  challenge_id: string;
  code: string;
  is_sent: boolean;
}

export interface AdVideoResponse {
  id: string;
  description: string | null;
  url: string | null;
  file_path: string | null;
  status: string;
  created_by_admin_id: string | null;
  views_count: number;
  shares_count: number;
  created_at: string;
}

export interface SystemSettingsResponse {
  id: string;
  ai_confidence_threshold: number;
  report_limit: number;
}
