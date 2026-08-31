export interface Task {
  id: string;
  description: string;
  difficulty: "easy" | "medium" | "hard";
  verifier: string;
}

export interface ToolCallRecord {
  id: number;
  run_id: string;
  step: number;
  tool_name: string;
  arguments_json: string;
  result_json: string;
  created_at: string;
}

export interface TaskRun {
  id: string;
  task_id: string;
  status: "running" | "passed" | "failed" | "error";
  score: number | null;
  failure_category: "NONE" | "MODEL_FAILURE" | "ENVIRONMENT_FAILURE" | "TASK_FAILURE" | string;
  failure_reason: string | null;
  duration_seconds: number | null;
  created_at: string;
  updated_at: string;
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
