'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Loader2, Printer } from 'lucide-react';

export default function ReportPage() {
    const params = useParams();
    const [result, setResult] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (params.jobId) {
            fetch(`/api/status/${params.jobId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'completed') {
                        setResult(data.result);
                    }
                    setLoading(false);
                })
                .catch(() => setLoading(false));
        }
    }, [params.jobId]);

    if (loading) return <div className="p-8 flex items-center justify-center h-screen"><Loader2 className="animate-spin mr-2" /> Generatiing briefing...</div>;
    if (!result) return <div className="p-8 text-center text-red-600">Report not found or processing incomplete.</div>;

    // Helper to format evidence URL
    const formatSource = (url: string) => {
        try {
            return new URL(url).hostname.replace('www.', '');
        } catch {
            return 'Unknown Source';
        }
    };

    // Stance groupings
    const refutes = result.evidence?.filter((e: any) => e.stance?.label === 'refutes') || [];
    const supports = result.evidence?.filter((e: any) => e.stance?.label === 'supports') || [];
    const neutral = result.evidence?.filter((e: any) => (!e.stance?.label || e.stance?.label === 'neutral')) || [];

    // Narrative Logic for Summary
    let narrative = "This claim has mixed or inconclusive evidence.";
    if (result.style_risk_score > 70) {
        narrative = "Linguistic analysis suggests high potential for sensationalism or manipulation. ";
    }
    if (refutes.length > 0) {
        narrative += "Credible sources directly refute the core assertions of this claim.";
    } else if (supports.length > 0) {
        narrative += "Multiple sources confirm the details of this event.";
    }

    return (
        <div className="max-w-3xl mx-auto bg-white min-h-screen p-8 print:p-0 text-black font-serif print:max-w-full">

            {/* Print Controls */}
            <div className="mb-12 flex justify-end print:hidden no-print">
                <button
                    onClick={() => window.print()}
                    className="flex items-center gap-2 px-6 py-2 bg-gray-900 text-white text-sm font-sans font-medium rounded hover:bg-black transition-colors"
                >
                    <Printer size={16} /> Print Briefing Note
                </button>
            </div>

            <div className="print-page">
                {/* 1. Header: Analyst Briefing Style */}
                <header className="border-b-4 border-black pb-6 mb-8">
                    <div className="flex justify-between items-start">
                        <div>
                            <h5 className="text-xs font-sans font-bold uppercase tracking-widest text-gray-500 mb-2">PRISM INTELLIGENCE • ANALYSIS BRIEFING</h5>
                            <h1 className="text-3xl font-bold leading-tight font-sans">Verification Report</h1>
                        </div>
                        <div className="text-right text-xs font-mono text-gray-500">
                            <p>{new Date().toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                            <p>REF: {params.jobId?.toString().slice(0, 8)}</p>
                        </div>
                    </div>
                </header>

                {/* 2. Claim Hero */}
                <section className="mb-10 bg-gray-50 print:bg-transparent border-l-4 border-gray-900 p-6">
                    <h3 className="text-xs font-sans font-bold uppercase text-gray-400 mb-2">SUBJECT CLAIM</h3>
                    <p className="text-xl md:text-2xl italic font-serif leading-relaxed text-gray-900">
                        "{result.text?.length > 300 ? result.text.substring(0, 300) + "..." : result.text}"
                    </p>
                </section>

                {/* 3. Analysis Summary (Replace 95% Card) */}
                <section className="mb-10">
                    <h2 className="text-sm font-sans font-bold uppercase tracking-wider border-b border-gray-200 pb-2 mb-4">Executive Summary</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <div className="md:col-span-2">
                            <p className="text-base text-gray-800 leading-relaxed mb-4">
                                <strong>Risk Assessment:</strong> {result.style_risk_score > 60 ? 'HIGH' : result.style_risk_score > 30 ? 'MEDIUM' : 'LOW'}
                            </p>
                            <p className="text-gray-700 leading-relaxed">
                                {narrative}
                            </p>
                        </div>
                        <div className="hidden print:block md:block pl-6 border-l border-gray-100">
                            <div className="text-xs text-gray-500 mb-1 font-sans">LINGUISTIC RISK SCORE</div>
                            <div className="text-3xl font-bold font-sans">{Math.round(result.style_risk_score)}<span className="text-lg text-gray-400 font-normal">/100</span></div>
                        </div>
                    </div>
                </section>

                {/* 4. Linguistic Analysis (Print-Safe Heatmap) */}
                <section className="mb-10 page-break-inside-avoid">
                    <h2 className="text-sm font-sans font-bold uppercase tracking-wider border-b border-gray-200 pb-2 mb-4">Linguistic Analysis</h2>
                    <p className="text-xs text-gray-500 mb-4 italic">Underlined terms contributed to the risk score.</p>
                    <div className="leading-loose text-lg text-justify text-gray-800">
                        {result.heatmap?.map((token: any, i: number) => {
                            // Print logic handled by CSS classes
                            const isHigh = token.score > 0.45;
                            const style = isHigh ?
                                { textDecoration: 'underline', textDecorationColor: '#666', textUnderlineOffset: '3px' } : {};

                            return (
                                <span key={i} style={style} className={isHigh ? 'font-medium' : ''}>
                                    {token.token}{' '}
                                </span>
                            );
                        })}
                    </div>
                </section>

                {/* 5. Evidence Sections (Narrative Grouping) */}
                <section className="mb-8">
                    <h2 className="text-sm font-sans font-bold uppercase tracking-wider border-b border-black pb-2 mb-6">Verification Evidence</h2>

                    {/* Refuting Level */}
                    {refutes.length > 0 && (
                        <div className="mb-6">
                            <h3 className="text-xs font-sans font-bold uppercase text-red-700 mb-3 flex items-center gap-2">
                                ▸ Refuting Sources ({refutes.length})
                            </h3>
                            <ul className="list-none space-y-4">
                                {refutes.map((ev: any, i: number) => (
                                    <li key={i} className="pl-4 border-l-2 border-red-100">
                                        <div className="text-sm font-bold text-gray-900">{formatSource(ev.url)}</div>
                                        <div className="text-sm text-gray-700 mt-1">"{ev.text}"</div>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Supporting Level */}
                    {supports.length > 0 && (
                        <div className="mb-6">
                            <h3 className="text-xs font-sans font-bold uppercase text-green-700 mb-3 flex items-center gap-2">
                                ▸ Supporting Sources ({supports.length})
                            </h3>
                            <ul className="list-none space-y-4">
                                {supports.map((ev: any, i: number) => (
                                    <li key={i} className="pl-4 border-l-2 border-green-100">
                                        <div className="text-sm font-bold text-gray-900">{formatSource(ev.url)}</div>
                                        <div className="text-sm text-gray-700 mt-1">"{ev.text}"</div>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* Neutral Level */}
                    {neutral.length > 0 && (
                        <div className="mb-6">
                            <h3 className="text-xs font-sans font-bold uppercase text-gray-500 mb-3 flex items-center gap-2">
                                ▸ Contextual Sources ({neutral.length})
                            </h3>
                            <ul className="list-none space-y-3">
                                {neutral.slice(0, 5).map((ev: any, i: number) => (
                                    <li key={i} className="pl-4 border-l-2 border-gray-100 text-sm text-gray-600">
                                        <span className="font-semibold text-gray-800">{formatSource(ev.url)}</span>: {ev.text.substring(0, 120)}...
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </section>

                {/* 6. Conclusion */}
                <section className="mt-12 p-6 border-t-2 border-black">
                    <h3 className="text-xs font-sans font-bold uppercase text-gray-500 mb-2">CONCLUSION</h3>
                    <p className="text-lg font-serif font-medium text-gray-900">
                        {refutes.length > 0
                            ? "This claim is contradicted by available evidence from credible sources."
                            : supports.length > 0
                                ? "This claim is supported by multiple independent reports."
                                : "Insufficient definitive evidence found to verify this claim."}
                    </p>
                </section>

                {/* Footer */}
                <footer className="mt-16 pt-8 border-t border-gray-100 text-center text-[10px] text-gray-400 uppercase tracking-widest print:fixed print:bottom-8 print:w-full">
                    Generated by Prism Intelligence • Automated Analysis • {new Date().getFullYear()}
                </footer>
            </div>
        </div>
    );
}
