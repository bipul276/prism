export function RiskGauge({ score }: { score: number }) {
    // Score is 0 to 100 (integer)
    const percentage = Math.round(score);

    let color = "bg-green-500";
    let label = "Low Risk";

    if (score > 70) {
        color = "bg-red-500";
        label = "High Risk";
    } else if (score > 40) {
        color = "bg-yellow-500";
        label = "Medium Risk";
    }

    return (
        <div className="flex flex-col items-center p-4 border rounded-lg shadow-sm bg-white">
            <h3 className="text-lg font-semibold mb-2">Stylometric Risk</h3>
            <div className="relative w-32 h-32 rounded-full border-4 border-gray-100 flex items-center justify-center">
                <div className={`text-3xl font-bold ${color.replace('bg-', 'text-')}`}>
                    {percentage}%
                </div>
            </div>
            <div className={`mt-2 px-3 py-1 rounded-full text-white text-sm font-medium ${color}`}>
                {label}
            </div>
        </div>
    );
}
