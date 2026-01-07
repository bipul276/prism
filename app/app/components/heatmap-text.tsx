'use client';

// Color/Style scale function
// Now accepts overallRisk to conditionally suppress high styling for neutral claims
function getTokenStyle(score: number, overallRisk: number): React.CSSProperties {
    // Score is 0.0 to 1.0 (saliency)

    // Low importance: Ignore
    if (score < 0.15) return {};

    // If overall claim is neutral (< 30%), cap styling at subtle underline
    if (overallRisk < 30) {
        if (score >= 0.15) {
            return {
                textDecoration: 'underline',
                textDecorationColor: `rgba(156, 163, 175, 0.6)`, // gray-400
                textDecorationThickness: '1px',
                textUnderlineOffset: '3px'
            };
        }
        return {};
    }

    // Medium importance: Underline only
    if (score < 0.6) {
        return {
            textDecoration: 'underline',
            textDecorationColor: `rgba(220, 38, 38, 0.5)`, // red-600, semi-transparent
            textDecorationThickness: '2px',
            textUnderlineOffset: '3px'
        };
    }

    // High importance: Soft Background + Strong Underline
    return {
        backgroundColor: `rgba(254, 226, 226, 0.4)`, // red-100, very soft
        textDecoration: 'underline',
        textDecorationColor: `rgba(220, 38, 38, 1)`,
        textDecorationThickness: '2px',
        textUnderlineOffset: '3px',
        borderRadius: '2px'
    };
}

interface Token {
    token: string;
    score: number;
}

interface HeatmapTextProps {
    tokens: Token[];
    overallRisk?: number; // 0-100
}

export function HeatmapText({ tokens, overallRisk = 50 }: HeatmapTextProps) {
    if (!tokens || tokens.length === 0) return null;

    return (
        <div className="leading-loose text-lg text-gray-800 font-serif">
            {tokens.map((t, i) => (
                <span
                    key={i}
                    className="mr-1 inline-block transition-colors cursor-help hover:bg-gray-50"
                    style={getTokenStyle(t.score, overallRisk)}
                    title={`Linguistic Impact: ${(t.score * 100).toFixed(0)}%`}
                >
                    {t.token}
                </span>
            ))}
        </div>
    );
}

interface HeatmapLegendProps {
    overallRisk?: number;
}

interface HeatmapLegendProps {
    overallRisk?: number;
    detectedSignals?: string[]; // Signal names like "Causal Absolutes", "Emotional Loading"
}

export function HeatmapLegend({ overallRisk = 50, detectedSignals = [] }: HeatmapLegendProps) {
    // Don't show legend for neutral claims
    if (overallRisk < 30) {
        return null;
    }

    const hasCausal = detectedSignals.some(s => s.includes("Causal"));
    const hasEmotional = detectedSignals.some(s => s.includes("Emotional"));

    // For medium risk, make it collapsible
    if (overallRisk < 60) {
        return (
            <details className="mt-4 border-t border-gray-100 pt-3">
                <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600 select-none">
                    What do these highlights mean?
                </summary>
                <div className="flex items-center gap-6 text-xs text-gray-400 mt-2">
                    <div className={`flex items-center gap-2 ${hasCausal ? 'opacity-100' : 'opacity-40'}`}>
                        <span className="w-12 h-0.5 bg-red-400 opacity-50 block"></span>
                        <span>Causal framing {!hasCausal && <span className="text-gray-300">(not detected)</span>}</span>
                    </div>
                    <div className={`flex items-center gap-2 ${hasEmotional ? 'opacity-100' : 'opacity-40'}`}>
                        <span className="w-12 h-3 bg-red-100 block border-b border-red-400 opacity-50"></span>
                        <span>Emotional language {!hasEmotional && <span className="text-gray-300">(not detected)</span>}</span>
                    </div>
                </div>
            </details>
        );
    }

    // For high risk, show full legend
    return (
        <div className="flex items-center gap-6 text-xs text-gray-500 mt-4 border-t border-gray-100 pt-4 font-sans">
            <div className={`flex items-center gap-2 ${hasCausal ? '' : 'opacity-40'}`}>
                <span className="w-16 h-1 bg-transparent border-b-2 border-red-400 opacity-50 block"></span>
                <span>Causal framing {!hasCausal && <span className="text-gray-300">(not detected)</span>}</span>
            </div>
            <div className={`flex items-center gap-2 ${hasEmotional ? '' : 'opacity-40'}`}>
                <span className="w-16 h-4 bg-red-100 block border-b-2 border-red-600 opacity-50"></span>
                <span>Emotional language {!hasEmotional && <span className="text-gray-300">(not detected)</span>}</span>
            </div>
        </div>
    );
}


