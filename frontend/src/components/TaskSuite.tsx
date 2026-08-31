"use client";

import { Task } from "@/types";
import { Play, Loader2, Zap } from "lucide-react";

interface TaskSuiteProps {
  tasks: Task[];
  loading: boolean;
  runningTasks: Record<string, boolean>;
  onRunTask: (taskId: string) => void;
}

export function TaskSuite({ tasks, loading, runningTasks, onRunTask }: TaskSuiteProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            className="h-44 bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 animate-skeleton"
          />
        ))}
      </div>
    );
  }

  const getDifficultyBadge = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case "easy":
        return "bg-zinc-800 text-zinc-300 border-zinc-700";
      case "medium":
        return "bg-zinc-800 text-amber-300 border-zinc-700";
      case "hard":
        return "bg-zinc-800 text-rose-300 border-zinc-700";
      default:
        return "bg-zinc-800 text-zinc-400 border-zinc-700";
    }
  };

  const taskList = Array.isArray(tasks) ? tasks : [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {taskList.map((task) => {
        const isRunning = runningTasks[task.id];
        return (
          <div
            key={task.id}
            className="bg-zinc-900/60 border border-zinc-800/90 hover:border-zinc-700 transition-all rounded-xl p-5 flex flex-col justify-between group"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-3">
                <span className="font-mono text-sm font-semibold text-white tracking-wide">
                  {task.id}
                </span>
                <span
                  className={`text-xs px-2.5 py-0.5 rounded-full border font-mono uppercase tracking-wider ${getDifficultyBadge(
                    task.difficulty
                  )}`}
                >
                  {task.difficulty}
                </span>
              </div>
              <p className="text-xs text-zinc-400 line-clamp-3 leading-relaxed mb-4">
                {task.description}
              </p>
            </div>

            <div className="pt-3 border-t border-zinc-800/60 flex items-center justify-between">
              <span className="text-[11px] font-mono text-zinc-500 flex items-center gap-1">
                <Zap className="w-3 h-3 text-zinc-400" />
                {task.verifier}
              </span>
              <button
                onClick={() => onRunTask(task.id)}
                disabled={isRunning}
                className="bg-zinc-100 hover:bg-white text-zinc-950 disabled:bg-zinc-800 disabled:text-zinc-500 font-mono text-xs font-semibold px-3.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed shadow-sm"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    Run Task
                  </>
                )}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
