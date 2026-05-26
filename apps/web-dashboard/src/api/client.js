import { API_BASE_URL } from "../config";
async function request(path, init, token) {
    const headers = new Headers(init?.headers);
    headers.set("Content-Type", "application/json");
    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }
    const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
    if (!response.ok) {
        const text = await response.text();
        try {
            const parsed = JSON.parse(text);
            throw new Error(parsed.detail ?? text ?? "Request failed");
        }
        catch {
            throw new Error(text || "Request failed");
        }
    }
    return (await response.json());
}
export const api = {
    login: (email, password) => request("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
    }),
    adminOverview: (token) => request("/admin/overview", undefined, token),
    listWebUsers: (token) => request("/web-users", undefined, token),
    listMobileUsers: (token) => request("/admin/mobile-users", undefined, token),
    createWebUser: (token, payload) => request("/web-users", { method: "POST", body: JSON.stringify(payload) }, token),
    updateWebUser: (token, userId, payload) => request(`/web-users/${userId}`, { method: "PATCH", body: JSON.stringify(payload) }, token),
    deleteWebUser: (token, userId) => request(`/web-users/${userId}`, { method: "DELETE" }, token),
    listSponsoredChallenges: (token) => request("/sponsored-challenges", undefined, token),
    createSponsoredChallenge: (token, payload) => request("/sponsored-challenges", { method: "POST", body: JSON.stringify(payload) }, token),
    publishSponsoredChallenge: (token, challengeId) => request(`/sponsored-challenges/${challengeId}/publish`, { method: "POST" }, token),
    updateSponsoredChallenge: (token, challengeId, payload) => request(`/sponsored-challenges/${challengeId}`, { method: "PATCH", body: JSON.stringify(payload) }, token),
    deleteSponsoredChallenge: (token, challengeId) => request(`/sponsored-challenges/${challengeId}`, { method: "DELETE" }, token),
    unsentPromoCodes: (token) => request("/sponsored-challenges/promo/unsent", undefined, token),
    uploadAdVideo: async (token, payload) => {
        const form = new FormData();
        form.append("title", payload.title);
        form.append("file", payload.file);
        const response = await fetch(`${API_BASE_URL}/sponsored-challenges/ad-videos`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: form
        });
        if (!response.ok)
            throw new Error(await response.text());
        return (await response.json());
    },
    listAdVideos: (token) => request("/sponsored-challenges/ad-videos", undefined, token),
    moderationVideoQueue: (token) => request("/moderation/videos/queue", undefined, token),
    decideVideo: (token, videoId, decision) => request(`/moderation/videos/${videoId}/decision`, { method: "POST", body: JSON.stringify({ decision }) }, token),
    moderationReportsQueue: (token) => request("/moderation/reports/queue", undefined, token),
    decideReport: (token, reportId, decision) => request(`/moderation/reports/${reportId}/decision`, { method: "POST", body: JSON.stringify({ decision }) }, token),
    adminVideos: (token) => request("/moderation/videos", undefined, token),
    updateVideo: (token, videoId, payload) => request(`/moderation/videos/${videoId}`, { method: "PATCH", body: JSON.stringify(payload) }, token),
    deleteVideo: (token, videoId) => request(`/moderation/videos/${videoId}`, { method: "DELETE" }, token),
    campaignStats: (token) => request("/analytics/campaigns", undefined, token),
    adminDashboardAnalytics: (token) => request("/analytics/admin-dashboard", undefined, token),
    businessDashboardAnalytics: (token) => request("/analytics/business-dashboard", undefined, token),
    getSettings: (token) => request("/settings", undefined, token),
    updateSettings: (token, payload) => request("/settings", { method: "PATCH", body: JSON.stringify(payload) }, token)
};
