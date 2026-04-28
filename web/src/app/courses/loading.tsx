export default function Loading() {
  return (
    <div className="flex flex-col gap-8 py-8 animate-pulse">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b pb-6">
        <div className="h-8 w-48 bg-gray-200 dark:bg-gray-800 rounded"></div>
        <div className="h-10 w-full md:w-64 bg-gray-200 dark:bg-gray-800 rounded"></div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="flex flex-col gap-4 p-4 border rounded-lg h-64 bg-gray-50 dark:bg-gray-900/50">
            <div className="h-6 w-3/4 bg-gray-200 dark:bg-gray-800 rounded"></div>
            <div className="h-4 w-1/2 bg-gray-200 dark:bg-gray-800 rounded"></div>
            <div className="mt-auto flex justify-between">
              <div className="h-8 w-24 bg-gray-200 dark:bg-gray-800 rounded"></div>
              <div className="h-8 w-24 bg-gray-200 dark:bg-gray-800 rounded"></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
