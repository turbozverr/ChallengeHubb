import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { BusinessDashboardAnalyticsResponse, PromoCodeResponse, SponsoredChallengeResponse } from "../api/types";
import { useAuth } from "../auth/AuthContext";

type ChartSeries = { name: string; color: string; values: number[] };

function LineChart({ labels, series, yLabel }: { labels: string[]; series: ChartSeries[]; yLabel: string }) {
  const width = 900;
  const height = 260;
  const left = 48;
  const right = 16;
  const top = 16;
  const bottom = 36;
  const plotW = width - left - right;
  const plotH = height - top - bottom;

  const maxValue = Math.max(1, ...series.flatMap((s) => s.values));
  const xFor = (i: number) => left + (labels.length <= 1 ? 0 : (i / (labels.length - 1)) * plotW);
  const yFor = (v: number) => top + (1 - v / maxValue) * plotH;

  return (
    <div className="chartCard">
      <svg viewBox={`0 0 ${width} ${height}`} className="chartSvg" role="img" aria-label={yLabel}>
        <line x1={left} y1={top} x2={left} y2={top + plotH} stroke="#5a5a5a" />
        <line x1={left} y1={top + plotH} x2={left + plotW} y2={top + plotH} stroke="#5a5a5a" />
        {[0, 0.25, 0.5, 0.75, 1].map((m) => (
          <g key={m}>
            <line x1={left} y1={yFor(maxValue * m)} x2={left + plotW} y2={yFor(maxValue * m)} stroke="#2f2f2f" />
            <text x={8} y={yFor(maxValue * m) + 5} fill="#b8b8b8" fontSize="17">
              {(maxValue * m).toFixed(0)}
            </text>
          </g>
        ))}
        {series.map((s) => {
          const points = s.values.map((v, i) => `${xFor(i)},${yFor(v)}`).join(" ");
          return <polyline key={s.name} fill="none" stroke={s.color} strokeWidth="2.5" points={points} />;
        })}
        {labels.map((l, i) => (
          <text key={l + i} x={xFor(i)} y={height - 10} fill="#9d9d9d" fontSize="14" textAnchor="middle">
            {l.slice(5)}
          </text>
        ))}
      </svg>
      <div className="chartLegend">
        {series.map((s) => (
          <span key={s.name}>
            <i style={{ background: s.color }} /> {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}

export function BusinessPage() {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState<BusinessDashboardAnalyticsResponse | null>(null);
  const [promos, setPromos] = useState<PromoCodeResponse[]>([]);
  const [challenges, setChallenges] = useState<SponsoredChallengeResponse[]>([]);
  const [promoChallengeFilter, setPromoChallengeFilter] = useState("ALL");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!token) return;
      try {
        const [d, p, ch] = await Promise.all([api.businessDashboardAnalytics(token), api.unsentPromoCodes(token), api.listSponsoredChallenges(token)]);
        setDashboard(d);
        setPromos(p);
        setChallenges(ch);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Помилка завантаження");
      }
    };
    void load();
  }, [token]);

  const promosFiltered = useMemo(
    () => promos.filter((p) => promoChallengeFilter === "ALL" || p.challenge_id === promoChallengeFilter),
    [promos, promoChallengeFilter]
  );

  const totals = useMemo(() => {
    const views = (dashboard?.views_by_day ?? []).reduce((a, x) => a + x.value, 0);
    const submissions = (dashboard?.submissions_by_day ?? []).reduce((a, x) => a + x.value, 0);
    const completed = (dashboard?.completed_by_day ?? []).reduce((a, x) => a + x.value, 0);
    const conversion = views > 0 ? Number(((completed / views) * 100).toFixed(2)) : 0;
    return { views, submissions, completed, conversion };
  }, [dashboard]);

  return (
    <div className="card">
      <h1>Аналітика бізнес-кабінету</h1>
      {error ? <p className="error">{error}</p> : null}

      <div className="grid3">
        <div className="stat"><strong>{totals.views}</strong><span>Перегляди</span></div>
        <div className="stat"><strong>{totals.submissions}</strong><span>Відправлені відео</span></div>
        <div className="stat"><strong>{totals.conversion}%</strong><span>Конверсія</span></div>
      </div>

      <div className="chartGrid">
        <section>
          <h2>Перегляди кампаній за днями</h2>
          <LineChart
            labels={dashboard?.views_by_day.map((x) => x.date) ?? []}
            yLabel="Перегляди"
            series={[{ name: "Перегляди", color: "#AD46FF", values: dashboard?.views_by_day.map((x) => x.value) ?? [] }]}
          />
        </section>
        <section>
          <h2>Участь у челенджах за днями</h2>
          <LineChart
            labels={dashboard?.submissions_by_day.map((x) => x.date) ?? []}
            yLabel="Відправки"
            series={[{ name: "Відправлені відео", color: "#F6339A", values: dashboard?.submissions_by_day.map((x) => x.value) ?? [] }]}
          />
        </section>
      </div>

      <div className="chartGrid">
        <section>
          <h2>Завершення челенджів за днями</h2>
          <LineChart
            labels={dashboard?.completed_by_day.map((x) => x.date) ?? []}
            yLabel="Завершення"
            series={[{ name: "Завершені", color: "#36CFC9", values: dashboard?.completed_by_day.map((x) => x.value) ?? [] }]}
          />
        </section>
        <section>
          <h2>Конверсія кампаній за днями</h2>
          <LineChart
            labels={dashboard?.conversion_by_day.map((x) => x.date) ?? []}
            yLabel="%"
            series={[{ name: "Конверсія, %", color: "#AD46FF", values: dashboard?.conversion_by_day.map((x) => x.value) ?? [] }]}
          />
        </section>
      </div>

      <section>
        <h2>Взаємодія з контентом</h2>
        <LineChart
          labels={dashboard?.interactions_by_day.map((x) => x.date) ?? []}
          yLabel="Кількість"
          series={[
            { name: "Лайки", color: "#F6339A", values: dashboard?.interactions_by_day.map((x) => x.likes) ?? [] },
            { name: "Репости", color: "#36CFC9", values: dashboard?.interactions_by_day.map((x) => x.shares) ?? [] },
            { name: "Коментарі", color: "#9FA6B2", values: dashboard?.interactions_by_day.map((x) => x.comments) ?? [] }
          ]}
        />
      </section>

      <h2>Невідправлені промокоди</h2>
      <div className="filtersRow">
        <select value={promoChallengeFilter} onChange={(e) => setPromoChallengeFilter(e.target.value)}>
          <option value="ALL">Всі челенджі</option>
          {challenges.map((c) => (
            <option key={c.id} value={c.id}>{c.title}</option>
          ))}
        </select>
      </div>
      <div className="tableWrap">
        <table>
          <thead><tr><th>ID</th><th>Челендж</th><th>Код</th></tr></thead>
          <tbody>{promosFiltered.map((p) => <tr key={p.id}><td>{p.id}</td><td>{challenges.find((c) => c.id === p.challenge_id)?.title ?? p.challenge_id}</td><td>{p.code}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}


