import { EvidenceCard } from './evidence-card';
import { ChevronDown, ChevronRight, Info } from 'lucide-react';
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

function Section({ title, items, defaultOpen = true, icon }: { title: string, items: Evidence[], defaultOpen?: boolean, icon?: React.ReactNode }) {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    if (!items || items.length === 0) return null;

    return (
        <div className="border-l-2 border-gray-100 pl-4 py-2">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-gray-900 mb-3 w-full text-left transition-colors"
            >
                {isOpen ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
                {title} <span className="text-gray-400 font-normal">({items.length})</span>
            </button>

            {isOpen && (
                <div className="space-y-1 animate-in slide-in-from-top-2 duration-300">
                    {items.map((ev, i) => (
                        <EvidenceCard key={i} evidence={ev} />
                    ))}
                </div>
            )}
        </div>
    );
}

export function EvidenceStack({ evidence, stanceSummary }: EvidenceStackProps) {
    // 1. Group by stance
    const refutes = evidence.filter(e => e.stance?.label === 'refutes');
    const supports = evidence.filter(e => e.stance?.label === 'supports');
    const neutral = evidence.filter(e => e.stance?.label === 'neutral' || !e.stance?.label);

    const total = evidence.length;
    if (total === 0) return <p className="text-gray-400 italic">No evidence found.</p>;

    // 2. Generate Narrative Summary
    let narrative = "This claim has mixed evidence.";
    if (refutes.length > 0 && supports.length === 0) {
        narrative = "Credible sources directly refute this claim.";
    } else if (supports.length > 0 && refutes.length === 0) {
        narrative = "This claim is supported by multiple sources.";
    } else if (neutral.length === total) {
        narrative = "We found context, but no direct confirmation or refutation.";
    }

    return (
        <div className="space-y-6">
            <div className="flex items-start gap-3 bg-gray-50/50 p-4 rounded-lg border border-gray-100">
                <Info className="w-5 h-5 text-gray-400 mt-0.5 shrink-0" />
                <p className="text-sm text-gray-700 leading-relaxed">
                    {narrative} The system analyzed {total} sources to reach this conclusion.
                </p>
            </div>

            <div className="space-y-2">
                {/* Prioritize showing the 'active' stance first */}
                {refutes.length > 0 && <Section title="Refuting Evidence" items={refutes} defaultOpen={true} />}
                {supports.length > 0 && <Section title="Supporting Evidence" items={supports} defaultOpen={true} />}
                {neutral.length > 0 && <Section title="Neutral Context" items={neutral} defaultOpen={refutes.length === 0 && supports.length === 0} />}
            </div>
        </div>
    );
}
