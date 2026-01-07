'use client';
// Force rebuild: v5
import { HeatmapText, HeatmapLegend } from './heatmap-text';
import { AlertTriangle, CheckCircle, Tag, ChevronDown } from 'lucide-react';

interface Signal {
    name: string;
    trigger: string;
    explanation: string;
}

interface LinguisticAnalysisProps {
    verdict: string;
    signals: Signal[];
    heatmap: any[];
    riskScore: number;
}

function getSignalPillLabel(name: string): string {
    const mapping: Record<string, string> = {
        "Causal Absolutes": "Causal verb",
        "Emotional Loading": "Emotional language",
        "Attribution Gap": "No attribution",
        "Conspiracy Framing": "Conspiracy framing"
    };
    return mapping[name] || name;
}

function getWhyThisMatters(riskScore: number): string {
    if (riskScore < 30) {
        return "Neutral phrasing allows claims to be assessed primarily on external evidence.";
    } else if (riskScore < 60) {
        return "Some framing choices may shape interpretation; cross-check with evidence.";
    } else {
        return "Loaded language may bypass critical analysis; verify facts independently.";
    }
}

function getVerdictText(verdict: string, riskScore: number): string {
    if (verdict) return verdict;
    if (riskScore >= 60) return "High-risk language patterns detected.";
    if (riskScore >= 30) return "Some patterns warrant verification.";
    return "Neutral, objective language.";
}

export function LinguisticAnalysis({ verdict, signals, heatmap, riskScore }: LinguisticAnalysisProps) {
    if (!heatmap || heatmap.length === 0) return null;

    const isNeutral = riskScore < 30;
    const VerdictIcon = isNeutral ? CheckCircle : AlertTriangle;
    const iconColor = isNeutral ? "text-green-600" : "text-orange-500";
    const displaySignals = signals?.slice(0, 3) || [];

    return (
        <section className="space-y-6">
            {/* Header */}
            <h2 className="text-sm font-sans font-bold uppercase tracking-wider text-gray-900 border-b border-gray-200 pb-2">
                Linguistic Analysis
            </h2>

            {/* Horizontal Summary Row */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-4 sm:gap-8 text-sm">
                {/* Verdict */}
                <div className="flex items-start gap-2 min-w-0">
                    <VerdictIcon className={`${iconColor} shrink-0 mt-0.5`} size={16} />
                    <div>
                        <span className="font-semibold text-gray-900">Verdict:</span>
                        <span className="text-gray-700 ml-1">{getVerdictText(verdict, riskScore)}</span>
                    </div>
                </div>

                {/* Signals */}
                {displaySignals.length > 0 && (
                    <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-gray-900 shrink-0">Signals:</span>
                        {displaySignals.map((signal, i) => (
                            <span
                                key={i}
                                className="inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-800 text-xs font-medium rounded-full"
                                title={signal.explanation}
                            >
                                <Tag size={10} />
                                {getSignalPillLabel(signal.name)}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Why This Matters (inline) */}
            <p className="text-sm text-gray-500">
                <span className="font-medium text-gray-600">Why:</span> {getWhyThisMatters(riskScore)}
            </p>

            {/* Signal Details (Collapsible) */}
            {displaySignals.length > 0 && (
                <details className="group">
                    <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700 flex items-center gap-1 select-none">
                        <ChevronDown size={14} className="transition-transform group-open:rotate-180" />
                        View signal details
                    </summary>
                    <div className="mt-4 pl-4 border-l-2 border-gray-100 space-y-3">
                        {displaySignals.map((signal, i) => (
                            <div key={i}>
                                <div className="text-sm font-semibold text-gray-800">{signal.name}</div>
                                <div className="text-xs text-gray-400 uppercase">Trigger: {signal.trigger}</div>
                                <p className="text-sm text-gray-600 mt-1">{signal.explanation}</p>
                            </div>
                        ))}
                    </div>
                </details>
            )}

            {/* Annotated Text */}
            <div className="pt-4 border-t border-gray-100">
                <div className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-3">Annotated Text</div>
                <HeatmapText tokens={heatmap} overallRisk={riskScore} />
                <HeatmapLegend overallRisk={riskScore} detectedSignals={displaySignals.map(s => s.name)} />
            </div>
        </section>
    );
}


