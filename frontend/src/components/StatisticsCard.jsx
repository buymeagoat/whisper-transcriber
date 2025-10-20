import React from 'react'

const StatisticsCard = ({ 
  title, 
  value, 
  icon: Icon, 
  color = 'blue', 
  subtitle,
  loading = false 
}) => {
  const colorClasses = {
    blue: 'text-blue-600',
    green: 'text-green-600',
    yellow: 'text-yellow-600',
    red: 'text-red-600',
    purple: 'text-purple-600',
    indigo: 'text-indigo-600'
  }

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-6">
      <div className="flex items-center">
        {Icon && <Icon className={`w-8 h-8 ${colorClasses[color]}`} />}
        <div className="ml-4 flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {title}
          </h3>
          {loading ? (
            <div className="animate-pulse">
              <div className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded mt-1"></div>
            </div>
          ) : (
            <p className={`text-3xl font-bold ${colorClasses[color]}`}>
              {value}
            </p>
          )}
          {subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default StatisticsCard
