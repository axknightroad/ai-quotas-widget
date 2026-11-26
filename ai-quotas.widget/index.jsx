import { css, React, run } from "uebersicht";

export const command = `python3 "$HOME/Library/Application Support/Übersicht/widgets/ai-quotas.widget/fetch_quotas.py"`;

export const refreshFrequency = 60000; // 1 minute

export const className = css`
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  color: rgba(255, 255, 255, 0.92);
  user-select: none;
  -webkit-font-smoothing: antialiased;
`;

const STORAGE_KEY = "ai_quotas_widget_pos_v1";

function defaultPosition() {
  return { x: Math.max(24, window.innerWidth - 354), y: 28 };
}

function loadPosition() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (typeof parsed.x === "number" && typeof parsed.y === "number") {
        return parsed;
      }
    }
  } catch (e) {}
  return defaultPosition();
}

const cardStyle = css`
  position: fixed;
  width: 330px;
  pointer-events: auto;
  background: rgba(20, 22, 28, 0.72);
  backdrop-filter: blur(22px) saturate(160%);
  -webkit-backdrop-filter: blur(22px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.36);
  display: flex;
  flex-direction: column;
  gap: 11px;
`;

const headerStyle = css`
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: grab;
  &:active {
    cursor: grabbing;
  }
`;

const titleStyle = css`
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.01em;
  display: flex;
  align-items: center;
  gap: 7px;
`;

const dotStyle = css`
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.7);
`;

const updatedStyle = css`
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  font-family: "SF Mono", Menlo, monospace;
  display: flex;
  align-items: center;
  gap: 6px;
`;

const refreshBtnStyle = css`
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.78);
  border-radius: 6px;
  width: 20px;
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  line-height: 1;
  cursor: pointer;
  padding: 0;
  transition: background 0.15s ease, color 0.15s ease;
  &:hover {
    background: rgba(255, 255, 255, 0.18);
    color: #fff;
  }
`;

const sectionStyle = css`
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 9px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
`;

const secHeadStyle = css`
  display: flex;
  justify-content: space-between;
  align-items: baseline;
`;

const secNameStyle = css`
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
`;

const secPlanStyle = css`
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.48);
  text-transform: lowercase;
`;

const rowStyle = css`
  display: flex;
  flex-direction: column;
  gap: 3px;
`;

const rowTopStyle = css`
  display: flex;
  justify-content: space-between;
  font-size: 11px;
`;

const labelStyle = css`
  color: rgba(255, 255, 255, 0.65);
`;

const valStyle = css`
  font-family: "SF Mono", Menlo, monospace;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.88);
`;

const resetStyle = css`
  color: rgba(255, 255, 255, 0.42);
  margin-left: 6px;
  font-size: 10px;
`;

const barBgStyle = css`
  height: 5px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.1);
  overflow: hidden;
`;

const balanceStyle = css`
  font-family: "SF Mono", Menlo, monospace;
  font-size: 14px;
  font-weight: 600;
  color: #34d399;
`;

const errStyle = css`
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
`;

function barColor(pct) {
  if (pct <= 15) return "#f87171";
  if (pct <= 45) return "#fbbf24";
  return "#34d399";
}

function DraggableCard({ children }) {
  const [pos, setPos] = React.useState(loadPosition);
  const dragging = React.useRef(null);

  React.useEffect(() => {
    const onMove = (e) => {
      if (!dragging.current) return;
      const nx = Math.max(0, Math.min(window.innerWidth - 330, e.clientX - dragging.current.dx));
      const ny = Math.max(0, Math.min(window.innerHeight - 80, e.clientY - dragging.current.dy));
      setPos({ x: nx, y: ny });
    };
    const onUp = () => {
      if (!dragging.current) return;
      dragging.current = null;
      setPos((curr) => {
        try {
          window.localStorage.setItem(STORAGE_KEY, JSON.stringify(curr));
        } catch (e) {}
        return curr;
      });
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  const onHeaderMouseDown = (e) => {
    dragging.current = { dx: e.clientX - pos.x, dy: e.clientY - pos.y };
  };

  const onHeaderDoubleClick = () => {
    const def = defaultPosition();
    setPos(def);
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(def));
    } catch (e) {}
  };

  return (
    <div className={cardStyle} style={{ left: `${pos.x}px`, top: `${pos.y}px` }}>
      {children({ onHeaderMouseDown, onHeaderDoubleClick })}
    </div>
  );
}

function QuotaWidget({ output, error }) {
  const [manualOutput, setManualOutput] = React.useState(null);
  const [refreshing, setRefreshing] = React.useState(false);

  React.useEffect(() => {
    setManualOutput(null);
  }, [output]);

  const handleRefresh = (e) => {
    e.stopPropagation();
    if (refreshing) return;
    setRefreshing(true);
    run(command)
      .then((res) => {
        setManualOutput(res);
      })
      .catch(() => {})
      .finally(() => {
        setRefreshing(false);
      });
  };

  const activeOutput = manualOutput ?? output;
  let data = null;
  if (!error && activeOutput) {
    try {
      data = JSON.parse(activeOutput);
    } catch (e) {}
  }

  return (
    <DraggableCard>
      {({ onHeaderMouseDown, onHeaderDoubleClick }) => (
        <>
          <div
            className={headerStyle}
            onMouseDown={onHeaderMouseDown}
            onDoubleClick={onHeaderDoubleClick}
            title="拖动移动位置，双击恢复右上角"
          >
            <div className={titleStyle}>
              <span className={dotStyle} />
              AI Quotas
            </div>
            <div className={updatedStyle}>
              <span>{data ? `${data.updatedAt} · 1m` : "..."}</span>
              <button
                className={refreshBtnStyle}
                onMouseDown={(e) => e.stopPropagation()}
                onClick={handleRefresh}
                disabled={refreshing}
                title="手动刷新"
              >
                {refreshing ? "…" : "↻"}
              </button>
            </div>
          </div>

          {error ? <div className={errStyle}>Error: {String(error)}</div> : null}
          {!error && (!data || !data.providers) ? (
            <div className={errStyle}>Fetching quotas...</div>
          ) : null}

          {data &&
            data.providers &&
            data.providers.map((p, idx) => (
              <div key={idx} className={sectionStyle}>
                <div className={secHeadStyle}>
                  <span className={secNameStyle}>{p.name}</span>
                  {p.plan ? <span className={secPlanStyle}>{p.plan}</span> : null}
                </div>

                {p.status === "ok" && p.balanceText ? (
                  <div className={balanceStyle}>{p.balanceText}</div>
                ) : null}

                {p.status === "ok" && Array.isArray(p.bars)
                  ? p.bars.map((b, bIdx) => (
                      <div key={bIdx} className={rowStyle}>
                        <div className={rowTopStyle}>
                          <span className={labelStyle}>{b.label}</span>
                          <span className={valStyle}>
                            {b.percent}%
                            {b.reset ? <span className={resetStyle}>↻ {b.reset}</span> : null}
                          </span>
                        </div>
                        <div className={barBgStyle}>
                          <div
                            style={{
                              width: `${Math.max(0, Math.min(100, b.percent))}%`,
                              height: "100%",
                              borderRadius: "999px",
                              background: barColor(b.percent),
                              transition: "width 0.3s ease",
                            }}
                          />
                        </div>
                      </div>
                    ))
                  : null}

                {p.status !== "ok" ? <div className={errStyle}>{p.error}</div> : null}
              </div>
            ))}
        </>
      )}
    </DraggableCard>
  );
}

export const render = (props) => <QuotaWidget {...props} />;
