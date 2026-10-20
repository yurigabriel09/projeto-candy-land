const API_BASE = "http://127.0.0.1:5000";

export function resolverImagemUrl(url) {
    if (!url) return null;
    if (/^https?:\/\//i.test(url)) return url;
    return `${API_BASE}${url}`;
}