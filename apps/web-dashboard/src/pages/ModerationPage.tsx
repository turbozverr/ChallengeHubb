import { useEffect, useState } from "react";
import { api } from "../api/client";
import { resolveMediaUrl } from "../api/media";
import type { ModerationVideoResponse, ReportResponse } from "../api/types";
import { useAuth } from "../auth/AuthContext";

const aiLabels: Record<string, string> = {
  REJECTED: "Відхилено AI",
  APPROVED: "Схвалено AI",
  PENDING: "Очікує AI"
};

export function ModerationPage() {
  const { token } = useAuth();
  const [videos, setVideos] = useState<ModerationVideoResponse[]>([]);
  const [reports, setReports] = useState<ReportResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const load = async () => {
    if (!token) return;
    try {
      const [v, r] = await Promise.all([api.moderationVideoQueue(token), api.moderationReportsQueue(token)]);
      setVideos(v);
      setReports(r);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Помилка завантаження модерації");
    }
  };

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <>
      <div className="card">
        <h1>Центр модерації</h1>
        {error ? <p className="error">{error}</p> : null}

        <h2>Черга відео, відхилених AI</h2>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Контент</th>
                <th>Рішення AI</th>
                <th>Скарги</th>
                <th>Рішення</th>
              </tr>
            </thead>
            <tbody>
              {videos.map((video) => (
                <tr key={video.id}>
                  <td>{video.id}</td>
                  <td>
                    <button className="actionBtn iconOnly view" title="Перегляд" aria-label="Перегляд" onClick={() => setPreviewUrl(resolveMediaUrl(video.url))}>
                      ▶
                    </button>
                  </td>
                  <td>{aiLabels[video.ai_status] ?? video.ai_status}</td>
                  <td>{video.reports_count}</td>
                  <td>
                    <div className="actionBar">
                      <button className="actionBtn iconOnly publish" title="Схвалити" aria-label="Схвалити" onClick={async () => { if (!token) return; await api.decideVideo(token, video.id, "APPROVE"); await load(); }}>
                        ✓
                      </button>
                      <button className="actionBtn iconOnly danger" title="Заблокувати" aria-label="Заблокувати" onClick={async () => { if (!token) return; await api.decideVideo(token, video.id, "BLOCK"); await load(); }}>
                        ×
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h2>Черга скарг</h2>
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Відео</th>
                <th>Причина</th>
                <th>Рішення</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>{report.id}</td>
                  <td>
                    <button
                      className="actionBtn iconOnly view"
                      title="Перегляд"
                      aria-label="Перегляд"
                      disabled={!report.video_url}
                      onClick={() => report.video_url && setPreviewUrl(resolveMediaUrl(report.video_url))}
                    >
                      ▶
                    </button>
                  </td>
                  <td>{report.reason}</td>
                  <td>
                    <div className="actionBar">
                      <button className="actionBtn iconOnly publish" title="Схвалити" aria-label="Схвалити" onClick={async () => { if (!token) return; await api.decideReport(token, report.id, "REJECT"); await load(); }}>
                        ✓
                      </button>
                      <button className="actionBtn iconOnly danger" title="Заблокувати" aria-label="Заблокувати" onClick={async () => { if (!token) return; await api.decideReport(token, report.id, "CONFIRM"); await load(); }}>
                        ×
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {previewUrl ? (
        <div className="modalBackdrop" onClick={() => setPreviewUrl(null)}>
          <div className="modalCard videoPreviewModal" onClick={(e) => e.stopPropagation()}>
            <div className="modalHeader">
              <div>
                <h3>Перегляд відео</h3>
                <p className="muted">Перевірте контент перед рішенням модерації.</p>
              </div>
              <button className="iconClose" onClick={() => setPreviewUrl(null)} aria-label="Закрити">×</button>
            </div>
            <div className="videoFrame">
              <video controls src={previewUrl} />
            </div>
            <div className="modalActions">
              <a className="button secondary" href={previewUrl} target="_blank" rel="noreferrer">Відкрити окремо</a>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
