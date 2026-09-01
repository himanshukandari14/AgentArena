"use client";

import { useState, useEffect, useCallback } from "react";
import { Task, TaskRun, Metrics } from "@/types";
import { MetricsHeader } from "@/components/MetricsHeader";
import { TaskSuite } from "@/components/TaskSuite";
import { RunsTable } from "@/components/RunsTable";
import { TraceModal } from "@/components/TraceModal";
import { Shield, RefreshCw, Terminal, Layers, Activity } from "lucide-react";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [runs, setRuns] = useState<TaskRun[]>([]);

  const [loadingMetrics, setLoadingMetrics] = useState(true);
  const [loadingTasks, setLoadingTasks] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(true);

  const [runningTasks, setRunningTasks] = useState<Record<string, boolean>>({});
  const [replayingRuns, setReplayingRuns] = useState<Record<string, boolean>>({});
  const [selectedRun, setSelectedRun] = useState<TaskRun | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch("/api/metrics");
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (e) {
      console.error("Failed to fetch metrics", e);
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch("/api/tasks");
      if (res.ok) {
        const data = await res.json();
        setTasks(Array.isArray(data) ? data : data.tasks || []);
      }
    } catch (e) {
      console.error("Failed to fetch tasks", e);
    } finally {
      setLoadingTasks(false);
    }
  }, []);

  const fetchRuns = useCallback(async () => {
    try {
      const res = await fetch("/api/runs");
      if (res.ok) {
        const data = await res.json();
        setRuns(Array.isArray(data) ? data : data.runs || []);
      }
    } catch (e) {
      console.error("Failed to fetch runs", e);
    } finally {
      setLoadingRuns(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    fetchMetrics();
    fetchTasks();
    fetchRuns();
  }, [fetchMetrics, fetchTasks, fetchRuns]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, 3000);
    return () => clearInterval(interval);
  }, [refreshAll]);

  const handleRunTask = async (taskId: string) => {
    setRunningTasks((prev) => ({ ...prev, [taskId]: true }));
    try {
      const res = await fetch("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId }),
      });
      if (res.ok) {
        refreshAll();
      }
    } catch (e) {
      console.error("Failed to run task", e);
    } finally {
      setTimeout(() => {
        setRunningTasks((prev) => ({ ...prev, [taskId]: false }));
      }, 1000);
    }
  };

  const handleReplayRun = async (runId: string) => {
    setReplayingRuns((prev) => ({ ...prev, [runId]: true }));
    try {
      const res = await fetch(`/api/runs/${runId}/replay`, {
        method: "POST",
      });
      if (res.ok) {
        refreshAll();
      }
    } catch (e) {
      console.error("Failed to replay run", e);
    } finally {
      setTimeout(() => {
        setReplayingRuns((prev) => ({ ...prev, [runId]: false }));
      }, 1000);
    }
  };

  const handleViewTrace = async (run: TaskRun) => {
    try {
      const res = await fetch(`/api/runs/${run.id}`);
      if (res.ok) {
        const fullRun = await res.json();
        setSelectedRun(fullRun);
      } else {
        setSelectedRun(run);
      }
    } catch {
      setSelectedRun(run);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 font-sans selection:bg-white selection:text-black">
      {/* Top Header */}
      <header className="sticky top-0 z-40 bg-black/80 backdrop-blur-md border-b border-zinc-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-white text-black flex items-center justify-center font-mono font-bold text-sm shadow-md">
              AF
            </div>
            <div>
              <h1 className="font-mono text-base font-bold text-white tracking-wider flex items-center gap-2">
                AGENTARENA
                <span className="text-[10px] bg-zinc-800 border border-zinc-700 text-zinc-300 font-normal px-2 py-0.5 rounded-full">
                  v0.1.0
                </span>
              </h1>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={refreshAll}
              className="bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 px-3 py-1.5 rounded-lg font-mono text-xs transition-colors flex items-center gap-1.5 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
            <div className="flex items-center gap-2 border-l border-zinc-800 pl-3">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-mono text-zinc-400">Live Evaluation Engine</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
        {/* Section 1: Observability Metrics Header */}
        <section className="space-y-3">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-zinc-400" />
            <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-zinc-300">
              System Observability & Failure Attribution
            </h2>
          </div>
          <MetricsHeader metrics={metrics} loading={loadingMetrics} />
        </section>

        {/* Section 2: Task Execution Suite */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-zinc-400" />
              <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-zinc-300">
                Evaluation Task Suite ({tasks.length} Benchmarks)
              </h2>
            </div>
            <span className="text-xs font-mono text-zinc-500">FastMCP Sandbox Isolation</span>
          </div>
          <TaskSuite
            tasks={tasks}
            loading={loadingTasks}
            runningTasks={runningTasks}
            onRunTask={handleRunTask}
          />
        </section>

        {/* Section 3: Execution History & Trace Log */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-zinc-400" />
              <h2 className="font-mono text-sm font-bold uppercase tracking-wider text-zinc-300">
                Run Execution History & OpenTelemetry Traces
              </h2>
            </div>
            <span className="text-xs font-mono text-zinc-500">Auto-polling active</span>
          </div>
          <RunsTable
            runs={runs}
            loading={loadingRuns}
            onViewTrace={handleViewTrace}
            onReplayRun={handleReplayRun}
            replayingRuns={replayingRuns}
          />
        </section>
      </main>

      {/* Trace Inspector Modal */}
      <TraceModal run={selectedRun} onClose={() => setSelectedRun(null)} />
    </div>
  );
}
