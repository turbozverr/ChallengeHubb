import { useEffect, useState } from "react";
import { api } from "../api/client";
import { resolveMediaUrl } from "../api/media";
import type { ModerationVideoResponse, ReportResponse } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export function ModerationPage() {
  const { token } = useAuth();
  const [videos, setVideos] = useState<ModerationVideoResponse[]>([]);
  const [reports, setReports] = useState<ReportResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const aiLabels: Record<string, string> = {
    REJECTED: "Відхилено AI",
    APPROVED: "Схвалено AI",
    PENDING: "Очікує AI"
  };

  const load = async () => {
    if (!token) return;
    try {
      const [v, r] = await Promise.all([api.moderationVideoQueue(token), api.moderationReportsQueue(token)]);
      setVideos(v);
      setReports(r);
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
                <td><button onClick={() => setPreviewUrl(resolveMediaUrl(video.url))}>Переглянути</button></td>
                <td>{aiLabels[video.ai_status] ?? video.ai_status}</td>
                <td>{video.reports_count}</td>
                <td className="row">
                  <button onClick={async () => { if (!token) return; await api.decideVideo(token, video.id, "APPROVE"); await load(); }}>Схвалити</button>
                  <button onClick={async () => { if (!token) return; await api.decideVideo(token, video.id, "BLOCK"); await load(); }}>Заблокувати</button>
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
                <td><button disabled={!report.video_url} onClick={() => report.video_url && setPreviewUrl(resolveMediaUrl(report.video_url))}>Переглянути</button></td>
                <td>{report.reason}</td>
                <td className="row">
                  <button onClick={async () => { if (!token) return; await api.decideReport(token, report.id, "REJECT"); await load(); }}>Схвалити</button>
                  <button onClick={async () => { if (!token) return; await api.decideReport(token, report.id, "CONFIRM"); await load(); }}>Заблокувати</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
    {previewUrl ? (
      <div className="modalBackdrop" onClick={() => setPreviewUrl(null)}>
        <div className="modalCard" onClick={(e) => e.stopPropagation()}>
          <h3>Перегляд відео</h3>
          <video controls src={previewUrl} style={{ width: "100%", maxHeight: 420 }} />
          <div className="row"><a href={previewUrl} target="_blank" rel="noreferrer">Відкрити окремо</a><button onClick={() => setPreviewUrl(null)}>Закрити</button></div>
        </div>
      </div>
    ) : null}
    </>
  );
}
