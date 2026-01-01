'use client';

// Color/Style scale function
function getTokenStyle(score: number): React.CSSProperties {
    // Score is 0.0 to 1.0 (saliency)

    // Low importance: Ignore
    if (score < 0.15) return {};

    // Medium importance: Underline
    if (score < 0.45) {
        return {
            textDecoration: 'underline',
            textDecorationColor: `rgba(220, 38, 38, ${(score + 0.2).toFixed(2)})`, // red-600
            textDecorationThickness: '2px',
            textUnderlineOffset: '2px'
        };
    }

    // High importance: Background Highlight
    return {
        backgroundColor: `rgba(254, 226, 226, 0.5)`, // red-100/50
        borderBottom: `2px solid rgba(220, 38, 38, ${(score).toFixed(2)})`,
        borderRadius: '2px'
    };
}

interface Token {
    token: string;
    score: number;
}

export function HeatmapText({ tokens }: { tokens: Token[] }) {
    if (!tokens || tokens.length === 0) return null;

    return (
        <div className="leading-loose text-lg text-gray-800 font-serif">
            {tokens.map((t, i) => (
                <span
                    key={i}
                    className="mr-1 inline-block transition-colors cursor-help hover:bg-red-50"
                    style={getTokenStyle(t.score)}
                    title={`Linguistic Risk Contribution: ${(t.score * 100).toFixed(0)}%`}
                >
                    {t.token}
                </span>
            ))}
        </div>
    );
}
