"use client";

import { TaskRun } from "@/types";
import { X, CheckCircle2, XCircle, Clock, Cpu, Terminal, AlertCircle } from "lucide-react";

interface TraceModalProps {
  run: TaskRun | null;
  onClose: () => void;
}

export function TraceModal({ run, onClose }: TraceModalProps) {
  if (!run) return null;

  const rawToolCalls = run.tool_call_trace || run.tool_calls || [];
  const toolCalls = rawToolCalls.map((tc, idx) => ({
    id: tc.id || idx,
    step: tc.step || idx + 1,
    tool_name: tc.tool_name,
    arguments: tc.arguments || tc.arguments_json || "{}",
    result: tc.result || tc.result_json || "{}",
    created_at: tc.created_at || "",
  }));

  const startTimeStr = run.start_time || run.created_at;
  const formattedDate = startTimeStr ? new Date(startTimeStr).toLocaleString() : "N/A";

  const formatJson = (str: string) => {
    try {
      const parsed = JSON.parse(str);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return str;
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/40">
          <div className="flex items-center gap-3">
            <Terminal className="w-5 h-5 text-zinc-300" />
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-mono text-base font-bold text-white">{run.id}</h3>
                <span className="text-xs font-mono text-zinc-400 font-medium">({run.task_id})</span>
                {run.container_id && (
                  <span className="bg-blue-950/80 border border-blue-800/80 text-blue-300 text-[10px] font-mono px-2 py-0.5 rounded-full">
                    🐳 container: {run.container_id.slice(0, 12)}
                  </span>
                )}
              </div>
              <p className="text-xs text-zinc-500 mt-0.5">
                Executed: {formattedDate}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Metadata Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-3">
              <span className="text-zinc-500 uppercase tracking-wider text-[10px] block mb-1">Status</span>
              <span className="flex items-center gap-1.5 font-bold text-white capitalize">
                {run.status === "passed" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-400" />
                )}
                {run.status}
              </span>
            </div>

            <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-3">
              <span className="text-zinc-500 uppercase tracking-wider text-[10px] block mb-1">Score</span>
              <span className="font-bold text-white text-sm">
                {run.score !== null ? `${(run.score * 100).toFixed(0)} / 100` : "N/A"}
              </span>
            </div>

            <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-3">
              <span className="text-zinc-500 uppercase tracking-wider text-[10px] block mb-1">Duration</span>
              <span className="font-bold text-white flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-zinc-400" />
                {run.duration_seconds ? `${run.duration_seconds.toFixed(2)}s` : "N/A"}
              </span>
            </div>

            <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-3">
              <span className="text-zinc-500 uppercase tracking-wider text-[10px] block mb-1">Failure Category</span>
              <span className="font-bold text-white flex items-center gap-1">
                <Cpu className="w-3.5 h-3.5 text-amber-400" />
                {run.failure_category}
              </span>
            </div>
          </div>

          {/* Failure Reason Alert */}
          {run.failure_reason && (
            <div className="bg-rose-950/40 border border-rose-900/60 rounded-xl p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-xs font-mono font-bold text-rose-300 uppercase tracking-wider">
                  Verifier Rationale
                </h4>
                <p className="text-xs text-rose-200 mt-1 font-mono">{run.failure_reason}</p>
              </div>
            </div>
          )}

          {/* Tool Calls Execution Timeline */}
          <div>
            <h4 className="text-xs font-mono font-bold text-zinc-400 uppercase tracking-wider mb-3 flex items-center justify-between">
              <span>FastMCP Tool Execution History ({toolCalls.length} Steps)</span>
            </h4>

            {toolCalls.length === 0 ? (
              <div className="bg-zinc-900/40 border border-zinc-800/80 rounded-xl p-6 text-center text-xs text-zinc-500 font-mono">
                No tool calls executed for this run.
              </div>
            ) : (
              <div className="space-y-4">
                {toolCalls.map((call) => (
                  <div
                    key={call.id}
                    className="bg-zinc-900/50 border border-zinc-800/90 rounded-xl p-4 space-y-3 font-mono"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="bg-zinc-800 text-zinc-300 text-[10px] px-2 py-0.5 rounded font-bold">
                          Step {call.step}
                        </span>
                        <span className="text-sm font-bold text-white">{call.tool_name}</span>
                      </div>
                      {call.created_at && <span className="text-[10px] text-zinc-500">{call.created_at}</span>}
                    </div>

                    {/* Arguments */}
                    <div>
                      <span className="text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">
                        Input Arguments
                      </span>
                      <pre className="bg-black/80 border border-zinc-800/80 rounded-lg p-3 text-xs text-zinc-300 overflow-x-auto">
                        {formatJson(call.arguments)}
                      </pre>
                    </div>

                    {/* Result */}
                    <div>
                      <span className="text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">
                        Execution Output
                      </span>
                      <pre className="bg-black/80 border border-zinc-800/80 rounded-lg p-3 text-xs text-emerald-400/90 overflow-x-auto">
                        {formatJson(call.result)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900/40 flex justify-end">
          <button
            onClick={onClose}
            className="bg-zinc-800 hover:bg-zinc-700 text-white font-mono text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
          >
            Close Trace
          </button>
        </div>
      </div>
    </div>
  );
}
