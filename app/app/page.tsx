'use client';

import { useState, useEffect } from 'react';
import { AnalysisForm } from './components/analysis-form';
import { RiskSummary } from './components/risk-summary';
import { LinguisticAnalysis } from './components/linguistic-analysis';
import { EvidenceStack } from './components/evidence-stack';
import { RotateCcw } from "lucide-react";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [completedJobId, setCompletedJobId] = useState<string | null>(null);
  const [analyzedText, setAnalyzedText] = useState<string>('');

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
        setCompletedJobId(id);
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
    setAnalyzedText(text);

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

  const handleReset = () => {
    setResult(null);
    setAnalyzedText('');
    setCompletedJobId(null);
    setError('');
  };

  return (
    <main className="min-h-screen bg-[var(--background)] font-sans selection:bg-gray-200">

      {/* Compact Header Bar (shown after analysis) */}
      {result && (
        <div className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-gray-100 px-6 py-3">
          <div className="max-w-[1100px] mx-auto flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 min-w-0">
              <span className="text-[10px] font-mono uppercase tracking-widest text-gray-400 shrink-0">Analyzed:</span>
              <span className="text-sm text-gray-700 truncate font-medium">"{analyzedText}"</span>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              {completedJobId && (
                <a
                  href={`/report/${completedJobId}`}
                  target="_blank"
                  className="text-xs font-medium text-gray-500 hover:text-gray-900 transition-colors"
                >
                  Export PDF ↗
                </a>
              )}
              <button
                onClick={handleReset}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-900 text-white text-xs font-medium rounded-lg hover:bg-gray-800 transition-colors"
              >
                <RotateCcw size={12} />
                New Analysis
              </button>
            </div>
          </div>
        </div>
      )}

      <div className={`max-w-[1100px] mx-auto px-6 ${result ? 'py-8' : 'py-12'}`}>

        {/* Hero Section (Centered before results) */}
        {!result && (
          <div className="pt-[12vh] pb-8 transition-all duration-500">
            <div className="text-center space-y-2 mb-8">
              <div className="inline-block px-3 py-1 bg-white border border-gray-200 text-gray-400 text-[10px] font-mono uppercase tracking-widest rounded-full mb-4">
                Prism Intelligence
              </div>
            </div>

            <div className="max-w-2xl mx-auto">
              <div className="bg-white p-1 rounded-2xl shadow-sm border border-gray-100/80">
                <div className="bg-white p-6 md:p-8 rounded-xl border border-gray-100">
                  <AnalysisForm onAnalyze={handleAnalyze} isLoading={loading} />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex flex-col justify-center items-center py-16 space-y-4 animate-in fade-in duration-500">
            <div className="h-1 w-24 bg-gray-100 overflow-hidden rounded-full">
              <div className="h-full bg-gray-900 animate-progress origin-left w-full"></div>
            </div>
            <span className="text-xs font-semibold text-gray-400 tracking-widest uppercase">Investigating Sources...</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="max-w-2xl mx-auto bg-red-50 text-red-900 p-4 rounded-lg border border-red-100 text-sm text-center">
            <span className="font-semibold block mb-1">Investigation Error</span>
            {error}
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════════════
            RESULTS: 2-Column Analysis Canvas
        ═══════════════════════════════════════════════════════════════════ */}
        {result && (
          <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Risk Banner (Full Width) */}
            <RiskSummary score={result.style_risk_score} stance={result.stance_summary} />

            {/* Two-Column Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">

              {/* LEFT COLUMN: Linguistic Analysis */}
              <div className="space-y-6">
                <LinguisticAnalysis
                  verdict={result.linguistic_verdict}
                  signals={result.linguistic_signals}
                  heatmap={result.heatmap}
                  riskScore={result.style_risk_score}
                />
              </div>

              {/* RIGHT COLUMN: Verification Context */}
              <div className="space-y-6">
                <div>
                  <h2 className="text-sm font-sans font-bold uppercase tracking-wider text-gray-900 border-b border-gray-200 pb-2 mb-6">
                    Verification Context
                  </h2>
                  <EvidenceStack evidence={result.evidence} stanceSummary={result.stance_summary} />
                </div>
              </div>

            </div>

            {/* Interpretation (Full Width Synthesis) */}
            <div className="pt-6 border-t border-gray-200 mt-2">
              <p className="text-sm text-gray-600 leading-relaxed">
                <span className="font-semibold text-gray-700">Interpretation:</span>{' '}
                {result.style_risk_score < 30
                  ? "The claim is neutrally phrased, allowing evaluation to focus primarily on external evidence."
                  : result.style_risk_score >= 60
                    ? "Loaded language combined with the evidence profile warrants careful independent verification."
                    : "The claim uses some framing patterns, but mixed evidence requires careful source evaluation before drawing conclusions."
                }
              </p>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}

