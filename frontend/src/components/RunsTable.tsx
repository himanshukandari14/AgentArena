"use client";

import { useState } from "react";
import { TaskRun } from "@/types";
import { Search, Eye, RotateCw, CheckCircle2, XCircle, Clock, Loader2 } from "lucide-react";

interface RunsTableProps {
  runs: TaskRun[];
  loading: boolean;
  onViewTrace: (run: TaskRun) => void;
  onReplayRun: (runId: string) => void;
  replayingRuns: Record<string, boolean>;
}

export function RunsTable({
  runs,
  loading,
  onViewTrace,
  onReplayRun,
  replayingRuns,
}: RunsTableProps) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const runList = Array.isArray(runs) ? runs : [];

  const filteredRuns = runList.filter((run) => {
    const matchesSearch =
      run.id.toLowerCase().includes(search.toLowerCase()) ||
      run.task_id.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === "all" || run.status.toLowerCase() === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "passed":
        return (
          <span className="bg-zinc-900 text-white border border-zinc-700 text-[11px] font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1 w-fit">
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            Passed
          </span>
        );
      case "failed":
        return (
          <span className="bg-zinc-900 text-white border border-zinc-700 text-[11px] font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1 w-fit">
            <XCircle className="w-3 h-3 text-rose-400" />
            Failed
          </span>
        );
      case "running":
        return (
          <span className="bg-zinc-900 text-white border border-zinc-700 text-[11px] font-mono px-2.5 py-0.5 rounded-full flex items-center gap-1 w-fit animate-pulse">
            <Clock className="w-3 h-3 text-amber-400" />
            Running
          </span>
        );
      default:
        return (
          <span className="bg-zinc-900 text-zinc-400 border border-zinc-800 text-[11px] font-mono px-2.5 py-0.5 rounded-full w-fit">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl overflow-hidden">
      {/* Controls Bar */}
      <div className="p-4 border-b border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-3 bg-zinc-900/60">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search run ID or task..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-black/80 border border-zinc-800 focus:border-zinc-600 rounded-xl pl-9 pr-4 py-2 text-xs font-mono text-white placeholder-zinc-500 outline-none transition-colors"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-xs font-mono text-zinc-400 whitespace-nowrap">Filter Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-black/80 border border-zinc-800 focus:border-zinc-600 rounded-xl px-3 py-2 text-xs font-mono text-white outline-none cursor-pointer"
          >
            <option value="all">All Runs</option>
            <option value="passed">Passed</option>
            <option value="failed">Failed</option>
            <option value="running">Running</option>
          </select>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-zinc-950/80 border-b border-zinc-800 text-zinc-400 uppercase tracking-wider text-[10px]">
            <tr>
              <th className="py-3.5 px-4 font-semibold">Run ID</th>
              <th className="py-3.5 px-4 font-semibold">Task ID</th>
              <th className="py-3.5 px-4 font-semibold">Status</th>
              <th className="py-3.5 px-4 font-semibold">Score</th>
              <th className="py-3.5 px-4 font-semibold">Failure Attribution</th>
              <th className="py-3.5 px-4 font-semibold">Duration</th>
              <th className="py-3.5 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {loading ? (
              [1, 2, 3, 4, 5].map((i) => (
                <tr key={i} className="animate-skeleton">
                  <td colSpan={7} className="py-4 px-4">
                    <div className="h-6 bg-zinc-900 rounded-lg w-full" />
                  </td>
                </tr>
              ))
            ) : filteredRuns.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-zinc-500 font-mono">
                  No execution runs found.
                </td>
              </tr>
            ) : (
              filteredRuns.map((run) => {
                const isReplaying = replayingRuns[run.id];
                return (
                  <tr key={run.id} className="hover:bg-zinc-900/40 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-white">{run.id}</td>
                    <td className="py-3.5 px-4 text-zinc-300">{run.task_id}</td>
                    <td className="py-3.5 px-4">{getStatusBadge(run.status)}</td>
                    <td className="py-3.5 px-4">
                      {run.score !== null ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                            <div
                              className="bg-white h-full transition-all"
                              style={{ width: `${Math.min(100, (run.score || 0) * 100)}%` }}
                            />
                          </div>
                          <span className="text-white font-bold">{(run.score * 100).toFixed(0)}%</span>
                        </div>
                      ) : (
                        <span className="text-zinc-600">--</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-zinc-400">
                      <span className="px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-[10px] text-zinc-300">
                        {run.failure_category}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-zinc-400">
                      {run.duration_seconds ? `${run.duration_seconds.toFixed(2)}s` : "--"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => onViewTrace(run)}
                          className="bg-zinc-800 hover:bg-zinc-700 text-zinc-200 px-2.5 py-1 rounded-lg text-xs transition-colors flex items-center gap-1 cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Trace
                        </button>
                        <button
                          onClick={() => onReplayRun(run.id)}
                          disabled={isReplaying}
                          className="bg-zinc-100 hover:bg-white text-zinc-950 px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1 cursor-pointer disabled:opacity-50"
                        >
                          {isReplaying ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <RotateCw className="w-3.5 h-3.5" />
                          )}
                          Replay
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
