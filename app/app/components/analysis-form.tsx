'use client';

import { useState } from 'react';

interface AnalysisFormProps {
    onAnalyze: (text: string) => void;
    isLoading: boolean;
}

export function AnalysisForm({ onAnalyze, isLoading }: AnalysisFormProps) {
    const [text, setText] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (text.trim()) {
            onAnalyze(text);
        }
    };

    const examples = [
        "Russia attacked Ukraine",
        "Drinking bleach cures COVID",
        "Vaccines cause autism"
    ];

    return (
        <div className="w-full max-w-2xl mx-auto">
            <div className="mb-4 text-center">
                <h2 className="text-xl font-semibold tracking-tight text-gray-900">Analyze a Claim</h2>
                <p className="text-sm text-gray-500 mt-1">Paste a factual claim or news article snippet to investigate.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="relative">
                    <textarea
                        placeholder="e.g. 'The earth is flat' or paste a URL/Text..."
                        className="w-full min-h-[100px] p-4 text-lg rounded-lg border border-gray-200 bg-white shadow-sm focus:outline-none focus:ring-1 focus:ring-gray-400 focus:border-gray-400 disabled:bg-gray-50 disabled:text-gray-400 resize-none transition-all"
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        disabled={isLoading}
                    />
                </div>

                <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                    <div className="flex flex-wrap gap-2 text-sm text-gray-500">
                        <span className="mr-1">Try:</span>
                        {examples.map(ex => (
                            <button
                                key={ex}
                                type="button"
                                onClick={() => setText(ex)}
                                className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors text-xs"
                                disabled={isLoading}
                            >
                                {ex}
                            </button>
                        ))}
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading || !text.trim()}
                        className="w-full sm:w-auto py-2.5 px-6 bg-gray-900 hover:bg-black text-white font-medium rounded-lg shadow-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
                    >
                        {isLoading ? 'Investigating...' : 'Analyze'}
                    </button>
                </div>
            </form>
        </div>
    );
}
