import { useEffect, useRef } from "react";

type RiskLevel = "low" | "moderate" | "high" | "idle";

const PALETTE: Record<RiskLevel, { line: string; glow: string; amp: number; speed: number }> = {
  idle: { line: "rgba(56, 189, 248, 0.55)", glow: "rgba(56, 189, 248, 0.28)", amp: 0.14, speed: 0.55 },
  low: { line: "rgba(34, 211, 238, 0.62)", glow: "rgba(34, 211, 238, 0.3)", amp: 0.2, speed: 0.7 },
  moderate: { line: "rgba(251, 191, 36, 0.66)", glow: "rgba(251, 191, 36, 0.34)", amp: 0.4, speed: 1.0 },
  high: { line: "rgba(251, 113, 133, 0.75)", glow: "rgba(244, 63, 94, 0.4)", amp: 0.62, speed: 1.5 },
};

function reducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function drawWave(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  t: number,
  baseY: number,
  color: string,
  glow: string,
  amp: number,
  alpha = 1,
) {
  // ECG-style trace driven by time so it scrolls continuously.
  ctx.beginPath();
  const cy = baseY;
  for (let x = 0; x <= w; x += 3) {
    const u = (x / w) * Math.PI * 4 - t;
    // QRS-like spike layered over a smooth pulse
    const smooth = Math.sin(u) * 0.5 + Math.sin(u * 0.5 + 1.2) * 0.3;
    const spike = Math.pow(Math.max(0, Math.sin(u * 3 + 0.4)), 9) * 1.9;
    const v = smooth * 0.6 + spike;
    const y = cy - v * amp * h * 0.5;
    if (x === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.strokeStyle = color;
  ctx.globalAlpha = alpha;
  ctx.lineWidth = 1.6;
  ctx.shadowColor = glow;
  ctx.shadowBlur = 12;
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.shadowBlur = 0;
}

export function SignalBackground({ riskLevel = "idle" }: { riskLevel?: RiskLevel | null }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const level = (riskLevel ?? "idle") as RiskLevel;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let width = 0;
    let height = 0;
    let start = performance.now();

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);

    const render = (now: number) => {
      const t = ((now - start) / 1000) * palette.speed;
      ctx.clearRect(0, 0, width, height);

      // faint grid
      ctx.strokeStyle = "rgba(30, 51, 77, 0.35)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0.5; x < width; x += 48) {
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
      }
      for (let y = 0.5; y < height; y += 48) {
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
      }
      ctx.stroke();

      // echoes behind the main trace
      drawWave(ctx, width, height, t * 0.82, height * 0.62 + Math.sin(t * 0.4) * height * 0.02,
        palette.glow, palette.glow, palette.amp * 1.25, 0.5);
      drawWave(ctx, width, height, t * 0.91, height * 0.55, palette.glow, palette.glow,
        palette.amp * 1.1, 0.65);

      // main trace rides higher + pulses harder as risk climbs
      const lift = level === "high" ? 0.42 : level === "moderate" ? 0.55 : 0.68;
      drawWave(ctx, width, height, t, height * lift, palette.line, palette.glow, palette.amp);

      // moving spill across the trace
      ctx.strokeStyle = palette.glow;
      ctx.lineWidth = 0.8;
      const spillX = ((t * 90) % (width + 400)) - 200;
      ctx.beginPath();
      ctx.moveTo(spillX, 0);
      ctx.lineTo(spillX + 260, height);
      ctx.stroke();

      raf = requestAnimationFrame(render);
    };

    const palette = PALETTE[level];
    if (reducedMotion()) {
      // static, calm trace for reduced-motion users
      ctx.clearRect(0, 0, width, height);
      drawWave(ctx, width, height, 1.2, height * 0.66, palette.line, palette.glow, palette.amp * 0.6);
      return () => window.removeEventListener("resize", resize);
    }

    start = performance.now();
    raf = requestAnimationFrame(render);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [level]);

  return <canvas ref={canvasRef} className="signal-bg" aria-hidden="true" />;
}