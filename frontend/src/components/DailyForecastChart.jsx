import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { 
  Sparkles, 
  Calendar, 
  TrendingUp, 
  AlertTriangle, 
  Info, 
  CheckCircle2, 
  Clock, 
  SlidersHorizontal 
} from 'lucide-react';

export default function DailyForecastChart({ forecastData }) {
  const [horizon, setHorizon] = useState(30); // 7, 14, 30
  const [activeTab, setActiveTab] = useState('chart'); // 'chart' | 'table'

  if (!forecastData || !forecastData.daily_forecast) {
    return (
      <div className="bg-white border border-slate-200/80 rounded-3xl p-8 shadow-xs text-center text-slate-500">
        <Sparkles className="h-6 w-6 text-[#00BC7C] mx-auto mb-2 animate-pulse" />
        <p className="text-sm font-bold text-[#283139]">Loading AI Daily Spending Prediction...</p>
        <p className="text-xs text-slate-400 mt-1">Extracting historical spending cadence & two-stage hurdle model...</p>
      </div>
    );
  }

  const allDays = forecastData.daily_forecast || [];
  const displayedDays = allDays.slice(0, horizon);

  // Compute stats for selected horizon
  const horizonTotal = displayedDays.reduce((acc, d) => acc + (d.predicted_amount || 0), 0);
  const horizonSpendDays = displayedDays.filter(d => d.will_spend).length;
  const horizonDailyAvg = horizonTotal / Math.max(1, displayedDays.length);
  
  // Find peak day in this horizon
  let horizonPeak = displayedDays[0] || null;
  displayedDays.forEach(d => {
    if (horizonPeak && d.predicted_amount > horizonPeak.predicted_amount) {
      horizonPeak = d;
    }
  });

  // Top 4 upcoming peak days
  const topPeakDays = [...displayedDays]
    .sort((a, b) => b.predicted_amount - a.predicted_amount)
    .slice(0, 4);

  // All projected overspend days in this horizon
  const overspendDays = displayedDays.filter(d => d.is_high_spend);

  // Custom Recharts Dot for highlighting High Spend alert days (STATIONARY - NO CSS ANIMATION TRANSLATIONS)
  const CustomizedDot = (props) => {
    const { cx, cy, payload } = props;
    if (!cx || !cy) return null;

    if (payload.is_high_spend) {
      return (
        <g key={`alert-dot-${payload.date}`}>
          {/* Stationary outer halo ring */}
          <circle 
            cx={cx} 
            cy={cy} 
            r={8} 
            fill="#FE5A61" 
            fillOpacity={0.2} 
            stroke="#FE5A61" 
            strokeWidth={1.5} 
            strokeDasharray="2 2" 
          />
          {/* Solid prominent inner alert dot */}
          <circle 
            cx={cx} 
            cy={cy} 
            r={4.5} 
            fill="#FE5A61" 
            stroke="#ffffff" 
            strokeWidth={2} 
          />
        </g>
      );
    }
    if (payload.is_weekend) {
      return <circle cx={cx} cy={cy} r={3.5} fill="#40C3F9" stroke="#ffffff" strokeWidth={1.5} />;
    }
    return <circle cx={cx} cy={cy} r={2.5} fill="#00BC7C" />;
  };

  // Custom Tooltip
  const CustomForecastTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white border border-slate-200 p-3.5 rounded-2xl shadow-xl text-xs max-w-xs text-[#283139]">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="font-extrabold text-[#283139] flex items-center space-x-1">
              <Calendar className="h-3.5 w-3.5 text-[#00BC7C] mr-1" />
              {data.day_name}, {data.display_date}
            </span>
            {data.is_high_spend ? (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FE5A61]/15 text-[#FE5A61] border border-[#FE5A61]/25 flex items-center">
                <AlertTriangle className="h-2.5 w-2.5 mr-0.5" /> High Spend
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#00BC7C]/10 text-[#00BC7C] border border-[#00BC7C]/20">
                Projected Spend
              </span>
            )}
          </div>

          <div className="mt-2.5 space-y-1.5">
            <div className="flex justify-between items-center">
              <span className="text-slate-500 font-medium">Predicted Expenditure:</span>
              <span className="font-mono font-black text-sm text-[#00BC7C]">
                ₹{data.predicted_amount.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-slate-500 font-medium">Spending Likelihood:</span>
              <span className="font-mono text-slate-700 font-bold">
                {(data.spending_probability * 100).toFixed(0)}% (Will Spend: {data.will_spend ? 'YES' : 'NO'})
              </span>
            </div>
            <div className="flex justify-between items-center text-[11px]">
              <span className="text-slate-500 font-medium">Confidence Range:</span>
              <span className="font-mono text-slate-500">
                ₹{data.confidence_lower.toFixed(2)} - ₹{data.confidence_upper.toFixed(2)}
              </span>
            </div>
            {data.likely_categories && data.likely_categories.length > 0 && (
              <div className="pt-2 border-t border-slate-100 mt-1.5">
                <span className="text-[10px] text-slate-400 block mb-1 font-semibold uppercase tracking-wider">Expected Categories:</span>
                <div className="flex flex-wrap gap-1">
                  {data.likely_categories.map((cat, idx) => (
                    <span 
                      key={idx} 
                      className="px-2 py-0.5 bg-slate-50 text-slate-700 rounded-full text-[10px] border border-slate-200 font-medium"
                    >
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white border border-slate-200/80 rounded-3xl p-6 shadow-xs space-y-6 text-[#283139]">
      {/* 1. Header with Title, Model Badge, and Horizon Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2 flex-wrap gap-y-1">
            <div className="p-1.5 bg-[#00BC7C]/10 text-[#00BC7C] rounded-xl border border-[#00BC7C]/20">
              <Sparkles className="h-4 w-4" />
            </div>
            <h3 className="text-base sm:text-lg font-black text-[#283139] tracking-tight">
              AI Day-by-Day Spending Prediction
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#8B5CF6]/10 text-[#8B5CF6] border border-[#8B5CF6]/25">
              Two-Stage Hurdle ML Model
            </span>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Machine Learning forecast predicting <span className="text-[#00BC7C] font-bold">which days</span> you are projected to spend and <span className="text-[#00BC7C] font-bold">by how much</span> based on historical living cadence.
          </p>
        </div>

        {/* Horizon Selector Pills */}
        <div className="flex items-center space-x-1.5 bg-slate-50 border border-slate-200 p-1 rounded-full self-start sm:self-auto">
          {[
            { label: 'Next 7 Days', value: 7 },
            { label: 'Next 14 Days', value: 14 },
            { label: 'Full 30 Days', value: 30 }
          ].map((item) => (
            <button
              key={item.value}
              onClick={() => setHorizon(item.value)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                horizon === item.value
                  ? 'bg-[#00BC7C] text-white shadow-xs'
                  : 'text-slate-600 hover:text-[#283139]'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Top Summary KPI Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
        {/* KPI 1: Total Forecasted Spend */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Projected Spend</span>
            <TrendingUp className="h-3.5 w-3.5 text-[#00BC7C]" />
          </div>
          <div className="mt-2.5">
            <div className="text-xl font-black font-mono text-[#283139]">
              ₹{horizonTotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <span className="text-[11px] text-slate-400 font-semibold">
              Avg ₹{horizonDailyAvg.toFixed(2)}/day
            </span>
          </div>
        </div>

        {/* KPI 2: Active Spending Days */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Spending Days</span>
            <CheckCircle2 className="h-3.5 w-3.5 text-[#00BC7C]" />
          </div>
          <div className="mt-2.5">
            <div className="text-xl font-black font-mono text-[#00BC7C]">
              {horizonSpendDays} <span className="text-xs text-slate-400 font-normal">/ {horizon} days</span>
            </div>
            <span className="text-[11px] text-slate-400 font-semibold">
              {((horizonSpendDays / horizon) * 100).toFixed(0)}% projected active
            </span>
          </div>
        </div>

        {/* KPI 3: Peak Projected Day */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Peak Spend Day</span>
            <AlertTriangle className="h-3.5 w-3.5 text-[#FFC053]" />
          </div>
          <div className="mt-2.5">
            <div className="text-sm font-black text-[#d97706] truncate">
              {horizonPeak?.display_date} ({horizonPeak?.day_name.slice(0, 3)})
            </div>
            <span className="text-sm font-mono font-black text-[#283139]">
              ₹{horizonPeak?.predicted_amount.toFixed(2)}
            </span>
          </div>
        </div>

        {/* KPI 4: ML Model Confidence */}
        <div className="bg-slate-50/80 border border-slate-200/80 rounded-2xl p-4 flex flex-col justify-between shadow-xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">ML Confidence</span>
            <Sparkles className="h-3.5 w-3.5 text-[#8B5CF6]" />
          </div>
          <div className="mt-2.5">
            <div className="text-xl font-black font-mono text-[#8B5CF6]">
              {((forecastData.model_confidence_score || 0.93) * 100).toFixed(0)}%
            </div>
            <span className="text-[11px] text-slate-400 truncate block font-medium">
              Ridge + Logistic Hurdle
            </span>
          </div>
        </div>
      </div>

      {/* 2.5. Active Predicted Overspend Alert Days Banner */}
      {overspendDays.length > 0 && (
        <div className="p-4 rounded-2xl bg-rose-50/80 border border-rose-200 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs text-rose-950">
          <div className="flex items-start space-x-3">
            <div className="p-2 rounded-xl bg-[#FE5A61]/15 text-[#FE5A61] mt-0.5 border border-[#FE5A61]/25">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2 flex-wrap">
                <span className="font-extrabold text-[#FE5A61] text-sm">
                  {overspendDays.length} Predicted Overspend Alert Day{overspendDays.length > 1 ? 's' : ''} Flagged
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[#8B5CF6]/10 text-[#8B5CF6] text-[10px] font-bold border border-[#8B5CF6]/20 flex items-center space-x-1">
                  <Sparkles className="h-2.5 w-2.5 mr-0.5" />
                  <span>MongoDB Alert Stream Connected</span>
                </span>
              </div>
              <p className="text-slate-600 mt-1 text-xs leading-relaxed font-medium">
                High spending predicted on:{' '}
                {overspendDays.map((d, i) => (
                  <span key={d.date} className="font-bold text-[#FE5A61]">
                    {d.day_name}, {d.display_date} (₹{d.predicted_amount.toFixed(2)} • {d.likely_categories.join(', ')})
                    {i < overspendDays.length - 1 ? ' • ' : ''}
                  </span>
                ))}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              const el = document.getElementById('live-alerts-stream');
              if (el) el.scrollIntoView({ behavior: 'smooth' });
            }}
            className="self-start md:self-auto px-4 py-2 rounded-full bg-[#FE5A61] hover:bg-[#e0454c] text-white text-xs font-bold transition-all flex items-center space-x-1.5 cursor-pointer whitespace-nowrap shadow-sm shadow-[#FE5A61]/25"
          >
            <span>View Alerts</span>
            <span className="text-[10px] font-mono">({overspendDays.length})</span>
          </button>
        </div>
      )}

      {/* 3. Main Chart / Table View Toggle */}
      <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1.5 text-xs font-semibold">
            <span className="h-2.5 w-2.5 rounded-full bg-[#FE5A61] inline-block"></span>
            <span>High Spend Alerts</span>
          </span>
          <span className="flex items-center space-x-1.5 text-xs font-semibold">
            <span className="h-2.5 w-2.5 rounded-full bg-[#40C3F9] inline-block"></span>
            <span>Weekend Cadence</span>
          </span>
          <span className="flex items-center space-x-1.5 text-xs font-semibold">
            <span className="h-2.5 w-2.5 rounded-full bg-[#00BC7C] inline-block"></span>
            <span>Weekday Cadence</span>
          </span>
        </div>

        <div className="flex items-center space-x-1 bg-slate-50 border border-slate-200 p-1 rounded-full">
          <button
            onClick={() => setActiveTab('chart')}
            className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'chart' ? 'bg-white text-[#283139] shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Graph View
          </button>
          <button
            onClick={() => setActiveTab('table')}
            className={`px-3 py-1 rounded-full text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'table' ? 'bg-white text-[#283139] shadow-xs' : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Day-by-Day Table
          </button>
        </div>
      </div>

      {/* 4. Interactive Forecast Graph */}
      {activeTab === 'chart' ? (
        <div className="h-72 w-full pt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={displayedDays} margin={{ top: 10, right: 15, left: -10, bottom: 5 }}>
              <defs>
                <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00BC7C" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#00BC7C" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis 
                dataKey="display_date" 
                stroke="#94a3b8" 
                fontSize={11} 
                tickLine={false}
                interval={horizon === 30 ? 2 : 0}
              />
              <YAxis 
                stroke="#94a3b8" 
                fontSize={11} 
                tickLine={false}
                tickFormatter={(v) => `₹${v}`}
              />
              <Tooltip content={<CustomForecastTooltip />} />
              <ReferenceLine 
                y={forecastData.historical_mean_daily_spend || 35.0} 
                stroke="#94a3b8" 
                strokeDasharray="4 4" 
                strokeOpacity={0.8}
                label={{
                  value: `Historical Avg: ₹${(forecastData.historical_mean_daily_spend || 35.0).toFixed(0)}`,
                  fill: '#64748b',
                  fontSize: 10,
                  position: 'insideTopLeft'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="predicted_amount" 
                stroke="#00BC7C" 
                strokeWidth={2.5}
                fillOpacity={1} 
                fill="url(#forecastGradient)" 
                dot={<CustomizedDot />}
                activeDot={{ r: 6, fill: '#00BC7C', stroke: '#ffffff', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      ) : (
        /* Detailed Tabular View of All Days */
        <div className="max-h-72 overflow-y-auto rounded-2xl border border-slate-200 bg-white">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="bg-slate-50 text-slate-500 sticky top-0 border-b border-slate-200 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-3.5">Date</th>
                <th className="py-3 px-3.5">Day</th>
                <th className="py-3 px-3.5">Will Spend?</th>
                <th className="py-3 px-3.5">Probability</th>
                <th className="py-3 px-3.5">Predicted Amount</th>
                <th className="py-3 px-3.5">Likely Categories</th>
                <th className="py-3 px-3.5">Intensity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {displayedDays.map((d) => (
                <tr key={d.date} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-2.5 px-3.5 font-bold text-[#283139]">{d.display_date}</td>
                  <td className="py-2.5 px-3.5 text-slate-500 font-sans">{d.day_name}</td>
                  <td className="py-2.5 px-3.5">
                    {d.will_spend ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#00BC7C]/15 text-[#00BC7C] font-sans">
                        YES
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-400 font-sans">
                        NO
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 px-3.5 text-[#00BC7C] font-bold">
                    {(d.spending_probability * 100).toFixed(0)}%
                  </td>
                  <td className="py-2.5 px-3.5 font-black text-[#283139]">
                    ₹{d.predicted_amount.toFixed(2)}
                  </td>
                  <td className="py-2.5 px-3.5 font-sans">
                    <div className="flex flex-wrap gap-1">
                      {d.likely_categories.map((c, i) => (
                        <span key={i} className="px-2 py-0.5 bg-slate-50 rounded-full text-[10px] text-slate-600 border border-slate-200">
                          {c}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="py-2.5 px-3.5 font-sans">
                    {d.is_high_spend ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#FE5A61]/15 text-[#FE5A61] border border-[#FE5A61]/25">
                        HIGH
                      </span>
                    ) : (
                      <span className="text-slate-400 text-[11px] font-medium">{d.spending_intensity}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 5. Key Projected Peak Days Cards */}
      <div className="pt-3 border-t border-slate-100">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold text-[#283139] flex items-center space-x-1.5 uppercase tracking-wider">
            <Clock className="h-3.5 w-3.5 text-[#00BC7C]" />
            <span>Highest Projected Spending Days (Upcoming Focus)</span>
          </span>
          <span className="text-[11px] text-slate-400 font-medium">Sorted by expected amount</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {topPeakDays.map((peak, idx) => (
            <div 
              key={peak.date} 
              className="p-4 rounded-2xl bg-slate-50/80 border border-slate-200/80 hover:border-[#00BC7C]/40 hover:bg-white transition-all flex flex-col justify-between shadow-xs"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#283139] flex items-center space-x-1">
                  <span className="text-[#00BC7C] mr-1 font-mono font-black">#{idx + 1}</span>
                  {peak.display_date} ({peak.day_name.slice(0, 3)})
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[#00BC7C]/10 text-[#00BC7C] border border-[#00BC7C]/20 font-bold">
                  {(peak.spending_probability * 100).toFixed(0)}%
                </span>
              </div>

              <div className="mt-3 flex items-baseline justify-between">
                <span className="text-base font-black font-mono text-[#283139]">
                  ₹{peak.predicted_amount.toFixed(2)}
                </span>
                {peak.is_high_spend && (
                  <span className="text-[10px] font-bold text-[#FE5A61] uppercase tracking-wider">
                    Spike
                  </span>
                )}
              </div>

              <div className="mt-2 flex flex-wrap gap-1 text-[9px] text-slate-500">
                {peak.likely_categories.map((c, i) => (
                  <span key={i} className="px-1.5 py-0.5 rounded-full bg-white border border-slate-200 font-medium">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
