'use client'

interface ChartData {
  houses?: Record<string, string[]>
  planets?: Record<string, string>
  ascendant?: string
  [key: string]: unknown
}

interface SimpleKundliCanvasProps {
  chartData: ChartData
}

export default function SimpleKundliCanvas({ chartData }: SimpleKundliCanvasProps) {
  return (
    <div className="bg-gradient-to-br from-indigo-900 to-purple-900 rounded-xl p-6 text-white">
      <h3 className="text-xl font-bold mb-4">Birth Chart</h3>
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((house) => (
          <div
            key={house}
            className="aspect-square border-2 border-white/20 rounded-lg flex items-center justify-center text-sm"
          >
            House {house}
          </div>
        ))}
      </div>
      <div className="mt-4 text-sm text-gray-300">
        <p>Chart visualization placeholder</p>
      </div>
    </div>
  )
}
