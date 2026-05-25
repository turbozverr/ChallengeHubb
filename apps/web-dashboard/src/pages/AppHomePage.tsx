import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { CampaignStatsResponse } from "../api/types";
import { useAuth } from "../auth/AuthContext";

export function AppHomePage() {
  const { token } = useAuth();
  const [overview, setOverview] = useState<Record<string, number> | null>(null);
  const [stats, setStats] = useState<CampaignStatsResponse[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      if (!token) return;
      try {
        const [ov, st] = await Promise.all([api.adminOverview(token), api.campaignStats(token)]);
        setOverview(ov);
        setStats(st);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Помилка завантаження");
      }
    };
    void run();
  }, [token]);

  return (
    <div className="card">
      <h1>Глобальний дашборд адміністратора</h1>
      {error ? <p className="error">{error}</p> : null}
      {overview ? (
        <div className="grid3">
          {Object.entries(overview).map(([k, v]) => (
            <div className="stat" key={k}>
              <strong>{v}</strong>
              <span>{k}</span>
            </div>
          ))}
        </div>
      ) : null}
      <h2>Топ кампаній за конверсією</h2>
      <div className="bars">
        {stats.map((s) => (
          <div key={s.challenge_id} className="barRow">
            <span>{s.title}</span>
            <div className="barTrack">
              <div className="barFill" style={{ width: `${Math.min(s.conversion_rate * 4, 100)}%` }} />
            </div>
            <strong>{s.conversion_rate}%</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
