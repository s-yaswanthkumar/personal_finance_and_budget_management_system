import React from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Legend 
} from 'recharts';
import { PieChart as PieIcon, TrendingUp, Sparkles } from 'lucide-react';

const COLORS = [
  '#00BC7C', // Spendee Green
  '#FE5A61', // Spendee Coral Red
  '#40C3F9', // Spendee Sky Blue
  '#FFC053', // Spendee Amber Yellow
  '#FF6FAF', // Spendee Pink
  '#8B5CF6', // Spendee Purple
  '#14B8A6'  // Teal
];

export default function SpendingCharts({ 
  categoryData, 
  monthlyTrends, 
  burnRateData 
}) {
  // Format category spend for donut chart
  const pieData = (categoryData || []).map((c) => ({
    name: c.category_name,
    value: c.amount,
    count: c.transaction_count
  }));

  const totalSpent = pieData.reduce((acc, curr) => acc + curr.value, 0);

  // Format trend data for bar comparison
  const trendData = (monthlyTrends || []).map((t) => ({
    month: t.month,
    Income: t.income,
    Expense: t.expense,
    Savings: t.net_savings
  }));

  // Custom Pie Tooltip
  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const pct = totalSpent > 0 ? Math.round((data.value / totalSpent) * 100) : 0;
      return (
        <div className="bg-white border border-slate-200 p-3 rounded-2xl shadow-xl text-xs text-[#283139]">
          <p className="font-extrabold text-[#283139]">{data.name}</p>
          <p className="text-[#00BC7C] font-black font-mono mt-0.5">
            ₹{data.value.toLocaleString('en-IN', { minimumFractionDigits: 2 })} ({pct}%)
          </p>
          <p className="text-[10px] text-slate-400 mt-0.5 font-medium">{data.payload.count} transactions</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* 1. Category Spending Donut Chart */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <PieIcon className="h-4 w-4 text-[#00BC7C]" />
              <h3 className="text-sm font-extrabold text-[#283139] uppercase tracking-wider">
                Category Breakdown (vw_monthly_summary)
              </h3>
            </div>
            <span className="text-xs font-bold text-slate-500 font-mono">
              Total: ₹{totalSpent.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>

          <div className="mt-4 h-64 w-full flex items-center justify-center">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={92}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={COLORS[index % COLORS.length]} 
                        stroke="#ffffff"
                        strokeWidth={2}
                      />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-slate-400 text-xs">
                No expense records found for this month.
              </div>
            )}
          </div>
        </div>

        {/* Legend Pills */}
        <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap justify-center gap-2">
          {pieData.map((item, idx) => (
            <div key={item.name} className="flex items-center space-x-1.5 text-xs bg-slate-50 border border-slate-200/60 px-2.5 py-1 rounded-full">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: COLORS[idx % COLORS.length] }}
              ></span>
              <span className="text-slate-700 font-bold">{item.name}</span>
              <span className="text-slate-400 text-[11px] font-mono">
                (₹{item.value.toFixed(0)})
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* 2. Monthly Trend & Cash Flow */}
      <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-[#00BC7C]" />
              <h3 className="text-sm font-extrabold text-[#283139] uppercase tracking-wider">
                Monthly Trend & Cash Flow
              </h3>
            </div>
            <span className="px-3 py-1 rounded-full text-[11px] font-bold bg-[#00BC7C]/10 text-[#00BC7C] border border-[#00BC7C]/20 flex items-center space-x-1">
              <Sparkles className="h-3 w-3 mr-1" />
              <span>Burn Rate: ₹{burnRateData?.daily_burn_rate || 0}/day</span>
            </span>
          </div>

          <div className="mt-4 h-64 w-full">
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="month" stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#ffffff', 
                      borderColor: '#e2e8f0', 
                      borderRadius: '1rem',
                      fontSize: '12px',
                      boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)'
                    }} 
                    formatter={(value) => [`₹${Number(value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`]}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Bar dataKey="Income" fill="#00BC7C" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Expense" fill="#FE5A61" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                Historical monthly data loading...
              </div>
            )}
          </div>
        </div>

        {/* Burn Rate Forecast Footer */}
        <div className="mt-4 p-3 rounded-2xl bg-slate-50 border border-slate-200/80 flex items-center justify-between text-xs text-slate-700">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-4 w-4 text-[#00BC7C]" />
            <span className="font-bold text-slate-700">30-Day Spend Projection:</span>
            <span className="font-mono text-[#00BC7C] font-black">
              ₹{(burnRateData?.projected_30_day_spend || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
          <span className="text-[11px] text-slate-400 font-semibold hidden sm:inline">
            {burnRateData?.days_remaining || 0} days remaining
          </span>
        </div>
      </div>
    </div>
  );
}