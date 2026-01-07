'use client';

import { EvidenceCard } from './evidence-card';
import { ChevronDown, Info } from 'lucide-react';
import { useState } from 'react';

interface Evidence {
    text: string;
    url?: string;
    stance?: {
        label: string;
        confidence: number;
    };
    credibility?: string;
    score?: number;
}

interface EvidenceStackProps {
    evidence: Evidence[];
    stanceSummary: {
        supports: number;
        refutes: number;
        neutral: number;
    };
}

function Section({ title, items, color, initialLimit = 2 }: { title: string, items: Evidence[], color: string, initialLimit?: number }) {
    const [showAll, setShowAll] = useState(false);
    if (!items || items.length === 0) return null;

    const visibleItems = showAll ? items : items.slice(0, initialLimit);
    const remainingCount = items.length - initialLimit;

    return (
        <div className="space-y-3">
            <div className="flex items-center gap-2">
                <span className={`text-xs font-bold uppercase tracking-wider ${color}`}>{title}</span>
                <span className="text-xs text-gray-400">({items.length})</span>
            </div>

            <div className="space-y-2">
                {visibleItems.map((ev, i) => (
                    <EvidenceCard key={i} evidence={ev} />
                ))}
            </div>

            {remainingCount > 0 && !showAll && (
                <button
                    onClick={() => setShowAll(true)}
                    className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 font-medium"
                >
                    <ChevronDown size={14} />
                    Show {remainingCount} more
                </button>
            )}
        </div>
    );
}

export function EvidenceStack({ evidence, stanceSummary }: EvidenceStackProps) {
    const refutes = evidence.filter(e => e.stance?.label === 'refutes');
    const supports = evidence.filter(e => e.stance?.label === 'supports');
    const neutral = evidence.filter(e => e.stance?.label === 'neutral' || !e.stance?.label);

    const total = evidence.length;
    if (total === 0) return <p className="text-gray-400 italic text-sm">No evidence found.</p>;

    // Detect conflict scenario
    const isConflicting = refutes.length > 0 && supports.length > 0;

    // Brief summary
    let summary = "Mixed evidence found.";
    if (isConflicting) {
        summary = `Conflicting evidence: ${refutes.length} refuting, ${supports.length} supporting.`;
    } else if (refutes.length > 0 && supports.length === 0) {
        summary = "Sources refute this claim.";
    } else if (supports.length > 0 && refutes.length === 0) {
        summary = "Sources support this claim.";
    } else if (neutral.length === total) {
        summary = "Context found, no direct verification.";
    }

    // For conflicting evidence, show 1 of each; otherwise show 2
    const refuteLimit = isConflicting ? 1 : 2;
    const supportLimit = isConflicting ? 1 : 2;

    return (
        <div className="space-y-6">
            {/* Brief Summary */}
            <div className="flex items-start gap-2 text-sm text-gray-600">
                <Info className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                <span>{summary} <span className="text-gray-400">({total} sources)</span></span>
            </div>

            {/* Evidence Sections */}
            <div className="space-y-6">
                {refutes.length > 0 && <Section title="Refuting" items={refutes} color="text-red-600" initialLimit={refuteLimit} />}
                {supports.length > 0 && <Section title="Supporting" items={supports} color="text-green-600" initialLimit={supportLimit} />}
                {neutral.length > 0 && <Section title="Neutral" items={neutral} color="text-gray-500" initialLimit={1} />}
            </div>
        </div>
    );
}
