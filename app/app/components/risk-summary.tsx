import React from 'react';
import { AlertTriangle, CheckCircle, HelpCircle, ShieldAlert } from 'lucide-react';

interface RiskSummaryProps {
    score: number;
    stance: {
        supports: number;
        refutes: number;
        neutral: number;
    };
}

export function RiskSummary({ score, stance }: RiskSummaryProps) {
    // Logic to determine risk level and message
    let level: 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN' = 'LOW';
    let colorClass = "bg-green-50 text-green-900 border-green-200";
    let icon = <CheckCircle className="w-5 h-5 text-green-600" />;
    let message = "This claim matches widely reported events.";

    if (score >= 80) {
        level = 'HIGH';
        colorClass = "bg-red-50 text-red-900 border-red-200";
        icon = <ShieldAlert className="w-5 h-5 text-red-600" />;
        message = "Credible sources directly refute this claim.";
    } else if (score >= 50) {
        level = 'MEDIUM';
        colorClass = "bg-amber-50 text-amber-900 border-amber-200";
        icon = <AlertTriangle className="w-5 h-5 text-amber-600" />;
        message = "Evidence is conflicting or only partially supports the claim.";
    } else if (stance.neutral > 0 && stance.supports === 0 && stance.refutes === 0) {
        level = 'UNKNOWN';
        colorClass = "bg-gray-50 text-gray-700 border-gray-200";
        icon = <HelpCircle className="w-5 h-5 text-gray-500" />;
        message = "Only neutral context found. No direct verification available.";
    }

    return (
        <div className={`w-full rounded-lg border px-6 py-4 flex flex-col md:flex-row items-start md:items-center gap-4 ${colorClass}`}>
            <div className="flex items-center gap-3 shrink-0">
                {icon}
                <div className="font-mono text-xs font-bold uppercase tracking-wider px-2 py-1 bg-white/50 rounded-md border border-black/5">
                    {level} RISK ({Math.round(score)}%)
                </div>
            </div>

            <div className="h-px w-full md:w-px md:h-8 bg-black/10 shrink-0 hidden md:block" />

            <div className="flex-1 text-sm font-medium leading-relaxed">
                {message}
            </div>
        </div>
    );
}
