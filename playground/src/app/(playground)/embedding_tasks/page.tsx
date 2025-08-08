"use client";

import TasksTable from "@/components/TasksTable";
import { useGetAndPrefetchTasks } from "@/hooks/useKubrickAPI";
import { useState } from "react";
import ErrorDisplay from "@/components/ErrorDisplay";
import LoadingOverlay from "@/components/LoadingOverlay";

const PAGE_LIMIT = 15;

const Tasks = () => {
  const [page, setPage] = useState(1);
  const { data, isLoading, error } = useGetAndPrefetchTasks(
    page - 1,
    PAGE_LIMIT,
  );
  const tasks = data?.data ?? [];
  const total = data?.metadata?.total ?? 0;

  return (
    <div className="px-6 py-1 flex flex-col grow">
      <h1 className="text-2xl font-bold mb-6">Playground - Embedding Tasks</h1>
      {isLoading && <LoadingOverlay isVisible={true} />}
      {error && <ErrorDisplay error={error} className="mb-4 mt-4 max-w-md" />}
      {tasks && tasks.length > 0 ? (
        <TasksTable
          tasks={tasks}
          page={page}
          totalTasks={total}
          perPage={PAGE_LIMIT}
          onPageChange={setPage}
        />
      ) : (
        !isLoading && <p>No tasks found.</p>
      )}
    </div>
  );
};

export default Tasks;
