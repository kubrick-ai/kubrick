"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Task } from "@/types";
import dayjs from "dayjs";


import React from "react";

interface TasksListProps {
  tasks: Array<Task>;
  page: number;
  totalTasks: number;
  perPage: number;
  onPageChange: (page: number) => void;
}

const TasksTable = ({
  tasks,
  page,
  totalTasks,
  perPage,
  onPageChange,
}: TasksListProps) => {
  const totalPages = Math.ceil(totalTasks / perPage);

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>SQS Message ID</TableHead>
            <TableHead>S3 Bucket</TableHead>
            <TableHead>S3 Key</TableHead>
            <TableHead>Created At</TableHead>
            <TableHead>Updated At</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tasks.map((task) => (
            <TableRow key={task.id}>
              <TableCell>
                {task.sqs_message_id ? task.sqs_message_id : ""}
              </TableCell>
              <TableCell>{task.s3_bucket}</TableCell>
              <TableCell>{task.s3_key}</TableCell>
              <TableCell>{dayjs(task.created_at).format("YYYY:MM:DD HH:mm:ss")}</TableCell>
              <TableCell>{dayjs(task.created_at).format("YYYY:MM:DD HH:mm:ss")}</TableCell>
              <TableCell>{task.status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <div className="mt-6 flex justify-center items-center gap-4">
        <Button
          variant="outline"
          disabled={page <= 1}
          onClick={() => onPageChange(Math.max(1, page - 1))}
        >
          Previous
        </Button>

        <span>
          Page {page} of {totalPages}
        </span>

        <Button
          variant="outline"
          disabled={page >= totalPages}
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        >
          Next
        </Button>
      </div>
    </>
  );
};

export default TasksTable;
