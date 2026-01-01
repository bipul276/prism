'use client';

import { useState, useEffect } from 'react';
import { AnalysisForm } from './components/analysis-form';
import { RiskSummary } from './components/risk-summary';
import { HeatmapText } from './components/heatmap-text';
import { EvidenceStack } from './components/evidence-stack';
import { Loader2 } from "lucide-react";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [completedJobId, setCompletedJobId] = useState<string | null>(null);

  // Polling logic
  useEffect(() => {
    let interval: NodeJS.Timeout;

    if (jobId) {
      interval = setInterval(() => {
        pollStatus(jobId);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [jobId]);

  const pollStatus = async (id: string) => {
    try {
      const res = await fetch(`/api/status/${id}`);
      if (!res.ok) return;

      const data = await res.json();

      if (data.status === 'completed') {
        setResult(data.result);
        setCompletedJobId(id); // Save ID for report
        setLoading(false);
        setJobId(null);
      } else if (data.status === 'failed') {
        setError(data.error || 'Analysis failed');
        setLoading(false);
        setJobId(null);
      }
    } catch (err) {
      // Ignore
    }
  };

  const handleAnalyze = async (text: string) => {
    setLoading(true);
    setError('');
    setResult(null);
    setJobId(null);

    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) {
        const body = await res.text();
        throw new Error(`Submission failed: ${body}`);
      }

      const data = await res.json();
      if (data.job_id) {
        setJobId(data.job_id);
      } else {
        setResult(data);
        setLoading(false);
      }

    } catch (err: any) {
      setError(err.message || 'Failed to connect to analysis server');
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[var(--background)] p-6 md:p-12 font-sans selection:bg-gray-200">
      <div className="max-w-3xl mx-auto space-y-12">

        {/* Hero Section (Centred if no result) */}
        <div className={`transition-all duration-700 ease-in-out ${result ? '' : 'pt-[15vh]'}`}>
          {/* Header - Subtle */}
          <div className={`text-center space-y-2 mb-8 ${result ? 'hidden' : ''}`}>
            <div className="inline-block px-3 py-1 bg-white border border-gray-200 text-gray-400 text-[10px] font-mono uppercase tracking-widest rounded-full mb-4">
              Prism Intelligence
            </div>
          </div>

          {/* Input Section - The "Guided Investigation" Card */}
          <div className="bg-white p-1 rounded-2xl shadow-sm border border-gray-100/80">
            <div className="bg-white p-6 md:p-8 rounded-xl border border-gray-100">
              <AnalysisForm onAnalyze={handleAnalyze} isLoading={loading} />
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col justify-center items-center py-12 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <div className="h-1 w-24 bg-gray-100 overflow-hidden rounded-full">
              <div className="h-full bg-gray-900 animate-progress origin-left w-full"></div>
            </div>
            <span className="text-xs font-semibold text-gray-400 tracking-widest uppercase">Investigating Sources...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 text-red-900 p-4 rounded-lg border border-red-100 text-sm text-center">
            <span className="font-semibold block mb-1">Investigation Error</span>
            {error}
          </div>
        )}

        {/* Results Dashboard */}
        {result && (
          <div className="transition-all duration-700 animate-in fade-in slide-in-from-bottom-8 space-y-8">

            {/* 1. Risk Summary Strip */}
            <RiskSummary score={result.style_risk_score} stance={result.stance_summary} />

            {/* 2. Analysis Content (Linear Stack) */}
            <div className="space-y-10">

              {/* Heatmap Section */}
              <div className="space-y-4">
                <div className="flex justify-between items-end border-b border-gray-100 pb-2">
                  <h3 className="text-lg font-medium text-gray-900">Linguistic Analysis</h3>
                  {completedJobId && (
                    <a href={`/report/${completedJobId}`} target="_blank" className="text-xs font-medium text-gray-500 hover:text-gray-900 flex items-center gap-1 transition-colors">
                      EXPORT PDF ↗
                    </a>
                  )}
                </div>
                <div className="bg-white rounded-lg border border-gray-100 p-6 shadow-sm">
                  <HeatmapText tokens={result.heatmap} />
                  <div className="mt-4 flex gap-4 text-xs text-gray-400">
                    <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-100"></span> Low Impact</div>
                    <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-200"></span> Med Impact</div>
                    <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400"></span> High Impact</div>
                  </div>
                </div>
              </div>

              {/* Evidence Section */}
              <div className="space-y-6">
                <h3 className="text-lg font-medium text-gray-900 border-b border-gray-100 pb-2">Verification Context</h3>

                <EvidenceStack evidence={result.evidence} stanceSummary={result.stance_summary} />
              </div>

            </div>
          </div>
        )}
      </div>
    </main>
  );
}
