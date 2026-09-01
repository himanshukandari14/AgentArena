export interface Task {
  id: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  verifier: string;
}

export interface ToolCallRecord {
  id?: number;
  run_id?: string;
  step: number;
  tool_name: string;
  arguments: string;
  result: string;
  created_at?: string;
}

export interface TaskRun {
  id: string;
  task_id: string;
  status: "queued" | "running" | "passed" | "failed" | "timed_out" | "error";
  score: number | null;
  failure_category: "NONE" | "MODEL_FAILURE" | "ENVIRONMENT_FAILURE" | "TASK_FAILURE" | string;
  failure_reason: string | null;
  agent_output?: string;
  duration_seconds: number | null;
  container_id?: string | null;
  env_version?: string | null;
  start_time?: string | null;
  end_time?: string | null;
  created_at?: string;
  tool_call_trace?: ToolCallRecord[];
  tool_calls?: ToolCallRecord[];
}

export interface Metrics {
  total_runs: number;
  active_runs: number;
  success_rate_percent: number;
  avg_score: number;
  p95_runtime_seconds: number;
  failure_category_counts: Record<string, number>;
}

