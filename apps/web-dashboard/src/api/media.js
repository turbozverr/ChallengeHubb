import { API_BASE_URL } from "../config";
export function resolveMediaUrl(url) {
    if (!url)
        return "";
    if (url.startsWith("http://") || url.startsWith("https://"))
        return url;
    const origin = API_BASE_URL.split("/api/v1")[0];
    return `${origin}/${url.replace(/^\/+/, "")}`;
}
