"use client";

import { Metrics } from "@/types";
import { Activity, CheckCircle2, Clock, Cpu, AlertTriangle } from "lucide-react";

interface MetricsHeaderProps {
  metrics: Metrics | null;
  loading: boolean;
}

export function MetricsHeader({ metrics, loading }: MetricsHeaderProps) {
  if (loading || !metrics) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            className="h-28 bg-zinc-900/60 border border-zinc-800/80 rounded-xl p-4 animate-skeleton"
          />
        ))}
      </div>
    );
  }

  const modelFailures = metrics.failure_category_counts?.MODEL_FAILURE || 0;
  const envFailures = metrics.failure_category_counts?.ENVIRONMENT_FAILURE || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* Card 1: Total Runs */}
      <div className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 transition-colors rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400">
          <span className="text-xs uppercase tracking-wider font-medium">Total Runs</span>
          <Activity className="w-4 h-4 text-zinc-400" />
        </div>
        <div className="mt-2">
          <div className="text-3xl font-mono font-bold text-white">{metrics.total_runs}</div>
          <p className="text-xs text-zinc-500 mt-1">{metrics.active_runs} currently running</p>
        </div>
      </div>

      {/* Card 2: Success Rate */}
      <div className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 transition-colors rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400">
          <span className="text-xs uppercase tracking-wider font-medium">Success Rate</span>
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
        </div>
        <div className="mt-2">
          <div className="text-3xl font-mono font-bold text-white">
            {metrics.success_rate_percent.toFixed(1)}%
          </div>
          <p className="text-xs text-zinc-500 mt-1">Avg Score: {(metrics.avg_score * 100).toFixed(0)}/100</p>
        </div>
      </div>

      {/* Card 3: P95 Latency */}
      <div className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 transition-colors rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400">
          <span className="text-xs uppercase tracking-wider font-medium">P95 Runtime</span>
          <Clock className="w-4 h-4 text-zinc-400" />
        </div>
        <div className="mt-2">
          <div className="text-3xl font-mono font-bold text-white">
            {metrics.p95_runtime_seconds.toFixed(2)}s
          </div>
          <p className="text-xs text-zinc-500 mt-1">Task execution latency</p>
        </div>
      </div>

      {/* Card 4: Model Failures */}
      <div className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 transition-colors rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400">
          <span className="text-xs uppercase tracking-wider font-medium">Model Failures</span>
          <Cpu className="w-4 h-4 text-amber-400" />
        </div>
        <div className="mt-2">
          <div className="text-3xl font-mono font-bold text-white">{modelFailures}</div>
          <p className="text-xs text-zinc-500 mt-1">LLM reasoning / tool error</p>
        </div>
      </div>

      {/* Card 5: Environment Failures */}
      <div className="bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700 transition-colors rounded-xl p-4 flex flex-col justify-between">
        <div className="flex items-center justify-between text-zinc-400">
          <span className="text-xs uppercase tracking-wider font-medium">Env Failures</span>
          <AlertTriangle className="w-4 h-4 text-zinc-400" />
        </div>
        <div className="mt-2">
          <div className="text-3xl font-mono font-bold text-white">{envFailures}</div>
          <p className="text-xs text-zinc-500 mt-1">System / DB exceptions</p>
        </div>
      </div>
    </div>
  );
}
