'use client';
// Force rebuild: v4
import { HeatmapText, HeatmapLegend } from './heatmap-text';
import { AlertTriangle, CheckCircle, Info, Tag } from 'lucide-react';

interface Signal {
    name: string;
    trigger: string;
    explanation: string;
}

interface LinguisticAnalysisProps {
    verdict: string;
    signals: Signal[];
    heatmap: any[]; // Token list
    riskScore: number;
}

// Map signal names to short pill labels
function getSignalPillLabel(name: string): string {
    const mapping: Record<string, string> = {
        "Causal Absolutes": "Causal verb",
        "Emotional Loading": "Emotional language",
        "Attribution Gap": "No attribution",
        "Conspiracy Framing": "Conspiracy framing"
    };
    return mapping[name] || name;
}

// Get "Why this matters" text based on risk
function getWhyThisMatters(riskScore: number): string {
    if (riskScore < 30) {
        return "Neutral wording makes it easier to verify using external sources.";
    } else if (riskScore < 60) {
        return "Some linguistic patterns may influence interpretation; cross-check with evidence.";
    } else {
        return "Loaded language may bypass critical analysis; verify facts independently.";
    }
}

export function LinguisticAnalysis({ verdict, signals, heatmap, riskScore }: LinguisticAnalysisProps) {
    if (!heatmap || heatmap.length === 0) return null;

    // Consistent thresholds: <30 neutral, 30-60 medium, >=60 high
    const isNeutral = riskScore < 30;
    const VerdictIcon = isNeutral ? CheckCircle : AlertTriangle;
    const verdictBgColor = isNeutral ? "bg-green-50 border-green-400" : "bg-orange-50 border-orange-400";
    const verdictIconColor = isNeutral ? "text-green-500" : "text-orange-500";
    const verdictTitleColor = isNeutral ? "text-green-800" : "text-orange-800";

    // Limit signals to max 3
    const displaySignals = signals?.slice(0, 3) || [];

    return (
        <section className="mb-12 page-break-inside-avoid">
            <div className="flex items-center justify-between border-b border-gray-200 pb-2 mb-6">
                <h2 className="text-sm font-sans font-bold uppercase tracking-wider text-gray-900">Linguistic Analysis</h2>
            </div>

            {/* Layer 1: Verdict */}
            <div className={`${verdictBgColor} border-l-4 p-5 mb-4`}>
                <div className="flex items-start gap-4">
                    <VerdictIcon className={`${verdictIconColor} mt-1 shrink-0`} size={20} />
                    <div>
                        <h4 className={`text-xs font-bold ${verdictTitleColor} uppercase tracking-widest mb-2`}>Linguistic Verdict</h4>
                        <p className="text-gray-900 font-serif text-lg leading-relaxed">
                            {verdict || (riskScore >= 60
                                ? "This text employs language or structure often associated with high-risk or unverified content."
                                : riskScore >= 30
                                    ? "This text contains some patterns that may warrant additional verification."
                                    : "This claim uses generally neutral language, facilitating objective verification.")}
                        </p>
                    </div>
                </div>
            </div>

            {/* Why This Matters */}
            <p className="text-sm text-gray-500 mb-8 italic">
                <span className="font-semibold not-italic">Why this matters:</span> {getWhyThisMatters(riskScore)}
            </p>

            {/* Signal Pills (Quick View) */}
            {displaySignals.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-6">
                    {displaySignals.map((signal, i) => (
                        <span
                            key={i}
                            className="inline-flex items-center gap-1 px-3 py-1 bg-amber-100 text-amber-800 text-xs font-medium rounded-full"
                            title={signal.explanation}
                        >
                            <Tag size={12} />
                            {getSignalPillLabel(signal.name)}
                        </span>
                    ))}
                </div>
            )}

            {/* Layer 2: Signals (Detailed, only if signals exist) */}
            {displaySignals.length > 0 && (
                <div className="mb-10">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Info size={14} /> Signal Details
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {displaySignals.map((signal, i) => (
                            <div key={i} className="pl-4 border-l-2 border-gray-200">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm font-bold font-sans text-gray-900">{signal.name}</span>
                                </div>
                                <div className="flex flex-col gap-1">
                                    <span className="text-[10px] text-gray-400 uppercase tracking-wide">Trigger: {signal.trigger}</span>
                                    <p className="text-sm text-gray-600 leading-snug">
                                        {signal.explanation}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Layer 3: Visuals */}
            <div>
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                    <Info size={14} /> Annotated Text
                </h4>
                <div className="pl-2 border-l border-gray-100">
                    <HeatmapText tokens={heatmap} overallRisk={riskScore} />
                </div>
                <HeatmapLegend overallRisk={riskScore} />
            </div>
        </section>
    );
}

