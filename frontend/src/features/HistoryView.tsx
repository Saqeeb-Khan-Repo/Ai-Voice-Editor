"use client";

import React, { useEffect, useState } from "react";
import { History, Download, Trash2, CheckCircle2, XCircle, Clock, AlertCircle } from "lucide-react";
import { ProcessingJobResponse } from "@/types";
import { listJobs, getOutputDownloadUrl } from "@/services/api";

export const HistoryView: React.FC = () => {
  const [jobs, setJobs] = useState<ProcessingJobResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchJobs = async () => {
    setIsLoading(true);
    try {
      const data = await listJobs();
      setJobs(data.jobs);
    } catch {
      // ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-studio-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <History size={20} className="text-amber-400" /> Enhancement History
          </h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Audit log of all audio enhancement jobs processed locally on this workstation.
          </p>
        </div>
        <button
          onClick={fetchJobs}
          className="text-xs font-mono text-slate-400 hover:text-white px-3 py-1.5 rounded-lg bg-studio-800 border border-studio-700 transition"
        >
          Refresh Log
        </button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-slate-400 text-sm">Loading job records...</div>
      ) : jobs.length === 0 ? (
        <div className="bg-studio-900 border border-studio-800 rounded-2xl p-12 text-center text-slate-400">
          <Clock size={36} className="mx-auto mb-3 text-studio-600" />
          <h3 className="text-base font-semibold text-white">No Previous Jobs Found</h3>
          <p className="text-sm text-slate-400 mt-1 max-w-sm mx-auto">
            Jobs will appear here once audio files are enhanced in the Studio workstation.
          </p>
        </div>
      ) : (
        <div className="bg-studio-900 border border-studio-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-studio-850 border-b border-studio-800 text-slate-400 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Job ID</th>
                  <th className="py-3 px-4">Preset</th>
                  <th className="py-3 px-4">Created At</th>
                  <th className="py-3 px-4">Execution Time</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-studio-800/60">
                {jobs.map((job) => (
                  <tr key={job.job_id} className="hover:bg-studio-850/50 transition">
                    <td className="py-3 px-4">
                      {job.status === "completed" ? (
                        <span className="inline-flex items-center gap-1 text-emerald-400 font-bold">
                          <CheckCircle2 size={13} /> Completed
                        </span>
                      ) : job.status === "failed" ? (
                        <span className="inline-flex items-center gap-1 text-rose-400 font-bold">
                          <XCircle size={13} /> Failed
                        </span>
                      ) : job.status === "cancelled" ? (
                        <span className="inline-flex items-center gap-1 text-slate-400">
                          <AlertCircle size={13} /> Cancelled
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-amber-400 font-bold">
                          <Clock size={13} className="animate-spin" /> {job.current_stage}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-bold">{job.job_id.slice(0, 8)}</td>
                    <td className="py-3 px-4 text-slate-300 capitalize">{job.preset_name.replace("_", " ")}</td>
                    <td className="py-3 px-4 text-slate-400">
                      {job.created_at ? new Date(job.created_at).toLocaleString() : "N/A"}
                    </td>
                    <td className="py-3 px-4 text-slate-400">
                      {job.execution_time_ms ? `${(job.execution_time_ms / 1000).toFixed(2)}s` : "-"}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {job.status === "completed" && job.output_id && (
                        <a
                          href={getOutputDownloadUrl(job.output_id)}
                          download
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500 hover:text-slate-950 font-bold transition"
                        >
                          <Download size={12} /> Download
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
