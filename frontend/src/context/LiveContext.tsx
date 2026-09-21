import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { api } from "../services/api";
import { openWebSocket } from "../services/websocket";
import type { Alert, DemoSessionStatus, Prediction, SensorReading, ScenarioName } from "../types";
import { useAuth } from "./AuthContext";
import { useToast } from "./ToastContext";

function samePrediction(a: Prediction, b: Prediction): boolean {
  if (a.id !== 0 && b.id !== 0 && a.id === b.id) return true;
  return Boolean(a.timestamp && b.timestamp && a.timestamp === b.timestamp);
}

function mergePrediction(list: Prediction[], incoming: Prediction): Prediction[] {
  const idx = list.findIndex((prev) => samePrediction(prev, incoming));
  if (idx >= 0) {
    const copy = [...list];
    copy[idx] = { ...copy[idx], ...incoming };
    return copy;
  }
  return [incoming, ...list].slice(0, 60);
}

interface LiveContextValue {
  connected: boolean;
  prediction: Prediction | null;
  predictionHistory: Prediction[];
  latestReading: SensorReading | null;
  alerts: Alert[];
  sensorHistory: SensorReading[];
  refresh: () => Promise<void>;
  refreshAlerts: () => Promise<void>;
  acknowledgeAlert: (alertId: number) => Promise<void>;
  alertFeedback: (alertId: number, feedback: "yes" | "no" | "not_sure") => Promise<void>;
  sendScenario: (scenario: ScenarioName) => Promise<void>;
  sendSensor: (payload: Record<string, unknown>) => Promise<void>;
  startDemo: (scenario: ScenarioName, values?: Record<string, number>) => Promise<void>;
  stopDemo: () => Promise<void>;
  demoRunning: boolean;
  demoScenario?: string;
}

const LiveContext = createContext<LiveContextValue | undefined>(undefined);

export function LiveProvider({ children }: { children: ReactNode }) {
  const { user, token } = useAuth();
  const { push } = useToast();
  const [connected, setConnected] = useState(false);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [predictionHistory, setPredictionHistory] = useState<Prediction[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [latestReading, setLatestReading] = useState<SensorReading | null>(null);
  const [sensorHistory, setSensorHistory] = useState<SensorReading[]>([]);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoScenario, setDemoScenario] = useState<string | undefined>();
  const wsRef = useRef<ReturnType<typeof openWebSocket> | null>(null);
  const demoTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const connectedRef = useRef(false);
  connectedRef.current = connected;
  const predictionRef = useRef(prediction);
  predictionRef.current = prediction;

  const refreshAlerts = useCallback(async () => {
    try {
      const list = await api.get<Alert[]>("/api/alerts?limit=50");
      setAlerts(list);
    } catch {
      /* ignore */
    }
  }, []);

  const refresh = useCallback(async () => {
    if (!user) return;
    const [pred, hist, read, history, dstatus] = await Promise.allSettled([
      api.get<Prediction>("/api/predictions/current").catch(() => null),
      api.get<Prediction[]>("/api/predictions/history?limit=40").catch(() => [] as Prediction[]),
      api.get<SensorReading>("/api/sensor/latest").catch(() => null),
      api.get<SensorReading[]>("/api/sensor/history?limit=100").catch(() => [] as SensorReading[]),
      api.get<DemoSessionStatus>("/api/demo/status").catch((): DemoSessionStatus => ({ running: false })),
    ]);
    if (pred.status === "fulfilled" && pred.value) setPrediction(pred.value);
    if (hist.status === "fulfilled" && hist.value.length) {
      setPredictionHistory((prev) => hist.value.reduce((acc, item) => mergePrediction(acc, item), prev));
    }
    if (read.status === "fulfilled" && read.value?.id) setLatestReading(read.value);
    if (history.status === "fulfilled") setSensorHistory(history.value);
    if (dstatus.status === "fulfilled") {
      setDemoRunning(dstatus.value.running);
      setDemoScenario(dstatus.value.scenario);
    }
    await refreshAlerts();
  }, [user, refreshAlerts]);

  useEffect(() => {
    if (!user || !token) {
      wsRef.current?.close();
      return;
    }
    void refresh();
    wsRef.current = openWebSocket(
      user.id,
      (event) => {
        if (event.type === "prediction_update") {
          const update = {
            ...(predictionRef.current ?? { id: 0 }),
            risk_score: event.risk_score,
            risk_level: event.risk_level as Prediction["risk_level"],
            timestamp: event.timestamp,
            prediction_window: event.prediction_window_minutes,
            advice: event.advice,
          } as Prediction;
          setPrediction((prev) => ({ ...(prev ?? ({} as Prediction)), ...update } as Prediction));
          setPredictionHistory((prev) => mergePrediction(prev, update));
        } else if (event.type === "alert_update") {
          const newAlert = event as unknown as Alert;
          setAlerts((prev) =>
            prev.some((a) => a.id === newAlert.id)
              ? prev.map((a) => (a.id === newAlert.id ? { ...a, ...newAlert } : a))
              : [newAlert, ...prev].slice(0, 50),
          );
          push({
            kind: newAlert.risk_level === "high" ? "danger" : "warning",
            title:
              newAlert.risk_level === "high"
                ? "High migraine risk detected"
                : "Migraine risk rising",
            message: newAlert.message,
          });
        }
      },
      (state) => {
        setConnected(state);
      },
    );
    return () => {
      wsRef.current?.close();
    };
  }, [user, token, refresh, push]);

  useEffect(() => {
    if (!user) return;
    const interval = setInterval(() => {
      if (!connectedRef.current) void refresh();
    }, 15000);
    return () => clearInterval(interval);
  }, [user, refresh]);

  const acknowledgeAlert = useCallback(async (alertId: number) => {
    await api.post(`/api/alerts/${alertId}/acknowledge`);
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a)));
  }, []);

  const alertFeedback = useCallback(async (alertId: number, feedback: "yes" | "no" | "not_sure") => {
    await api.post(`/api/alerts/${alertId}/feedback`, { feedback });
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, feedback, acknowledged: true } : a)));
  }, []);

  const sendScenario = useCallback(async (scenario: ScenarioName) => {
    const resp = await api.post<{ reading: SensorReading; prediction: Prediction }>("/api/demo/scenario", { scenario });
    if (resp?.reading?.id) setLatestReading(resp.reading);
    if (resp?.prediction) {
      setPrediction(resp.prediction);
      setPredictionHistory((prev) => [resp.prediction, ...prev].slice(0, 60));
    }
    await refreshAlerts();
  }, [refreshAlerts]);

  const sendSensor = useCallback(async (payload: Record<string, unknown>) => {
    const resp = await api.post<{ reading: SensorReading; prediction: Prediction }>("/api/sensor/readings", payload);
    if (resp?.reading?.id) setLatestReading(resp.reading);
    if (resp?.prediction) {
      setPrediction(resp.prediction);
      setPredictionHistory((prev) => [resp.prediction, ...prev].slice(0, 60));
    }
    await refreshAlerts();
  }, [refreshAlerts]);

  const startDemo = useCallback(async (scenario: ScenarioName, values?: Record<string, number>) => {
    const resp = await api.post<{
      running: boolean;
      scenario?: string;
      reading?: SensorReading;
      prediction?: Prediction;
    }>("/api/demo/start", { scenario, signal: values });
    setDemoRunning(resp?.running ?? true);
    setDemoScenario(resp?.scenario ?? scenario);
    if (resp?.reading) setLatestReading(resp.reading);
    if (resp?.prediction) {
      setPrediction(resp.prediction);
      setPredictionHistory((prev) => [resp.prediction as Prediction, ...prev].slice(0, 60));
    }
    await refreshAlerts();
  }, [refreshAlerts]);

  const stopDemo = useCallback(async () => {
    await api.post("/api/demo/stop");
    setDemoRunning(false);
    demoTimer.current && clearInterval(demoTimer.current);
    demoTimer.current = null;
  }, []);

  const value = useMemo<LiveContextValue>(
    () => ({
      connected, prediction, predictionHistory, alerts, latestReading, sensorHistory,
      refresh, refreshAlerts, acknowledgeAlert, alertFeedback,
      sendScenario, sendSensor, startDemo, stopDemo, demoRunning, demoScenario,
    }),
    [connected, prediction, predictionHistory, alerts, latestReading, sensorHistory,
     refresh, refreshAlerts, acknowledgeAlert, alertFeedback,
     sendScenario, sendSensor, startDemo, stopDemo, demoRunning, demoScenario],
  );

  return <LiveContext.Provider value={value}>{children}</LiveContext.Provider>;
}

export function useLive(): LiveContextValue {
  const ctx = useContext(LiveContext);
  if (!ctx) throw new Error("useLive must be used within LiveProvider");
  return ctx;
}