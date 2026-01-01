import { ExternalLink } from 'lucide-react';

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

export function EvidenceCard({ evidence }: { evidence: Evidence }) {
    // Simplified Stance Colors (Text only or very subtle bg)
    const stanceStyle =
        evidence.stance?.label === 'supports' ? 'text-green-700 bg-green-50 border-green-100' :
            evidence.stance?.label === 'refutes' ? 'text-red-700 bg-red-50 border-red-100' :
                'text-gray-600 bg-gray-50 border-gray-100';

    const hostname = evidence.url ? new URL(evidence.url).hostname.replace('www.', '') : 'Unknown Source';

    return (
        <a
            href={evidence.url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="block group p-4 -mx-4 rounded-lg hover:bg-gray-50 transition-colors border border-transparent hover:border-gray-100"
        >
            <div className="flex justify-between items-baseline mb-1">
                <div className="flex items-center gap-2">
                    <span className={`text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded border ${stanceStyle}`}>
                        {evidence.stance?.label || 'Neutral'}
                    </span>
                    <span className="text-xs font-medium text-gray-900 flex items-center gap-1">
                        {/* Favicon placeholder could go here */}
                        {hostname}
                    </span>
                </div>
                {evidence.score && <span className="text-[10px] text-gray-300 font-mono">Sim: {(evidence.score).toFixed(2)}</span>}
            </div>

            <p className="text-sm text-gray-600 leading-relaxed group-hover:text-gray-900 transition-colors line-clamp-2">
                {evidence.text}
            </p>
        </a>
    );
}
