import React, { useState } from 'react';
import SpendeeLogo from './SpendeeLogo';
import { 
  Bell, 
  ShieldCheck, 
  Database, 
  Cpu, 
  CheckCircle2, 
  AlertTriangle, 
  AlertOctagon, 
  Sparkles,
  User,
  LogOut,
  X,
  ExternalLink
} from 'lucide-react';

export default function Navbar({ 
  health, 
  unreadAlertsCount, 
  alerts, 
  currentUser,
  onLogout,
  onMarkAllRead, 
  onMarkAlertRead,
  onRefresh,
  onGoToLanding
}) {
  const [showAlertsDrawer, setShowAlertsDrawer] = useState(false);

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-slate-200/80 sticky top-0 z-40 text-[#283139] shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={onGoToLanding}>
          <SpendeeLogo className="h-8" showText={true} textColor="text-[#283139]" />
          <span className="hidden lg:inline-block px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-[#00BC7C]/10 text-[#00BC7C] border border-[#00BC7C]/20 rounded-full">
            Postgres ACID + Mongo + Scikit-Learn
          </span>
        </div>

        {/* System Health Indicators & Controls */}
        <div className="flex items-center space-x-2.5 sm:space-x-3">
          {/* Health Status Pills */}
          <div className="hidden md:flex items-center space-x-2 bg-slate-50 border border-slate-200/80 px-3 py-1.5 rounded-full text-xs">
            <div className="flex items-center space-x-1.5 text-slate-700">
              <Database className="h-3.5 w-3.5 text-[#40C3F9]" />
              <span className="font-medium">PostgreSQL</span>
              <span className="h-2 w-2 rounded-full bg-[#00BC7C] animate-pulse"></span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="flex items-center space-x-1.5 text-slate-700">
              <Database className="h-3.5 w-3.5 text-[#00BC7C]" />
              <span className="font-medium">MongoDB</span>
              <span className="h-2 w-2 rounded-full bg-[#00BC7C] animate-pulse"></span>
            </div>
            <span className="text-slate-300">|</span>
            <div className="flex items-center space-x-1.5 text-slate-700">
              <Cpu className="h-3.5 w-3.5 text-[#8B5CF6]" />
              <span className="font-medium">AI Engine</span>
              <span className="h-2 w-2 rounded-full bg-[#8B5CF6]"></span>
            </div>
          </div>

          {/* Spendee Home Showcase Navigation */}
          {onGoToLanding && (
            <button
              onClick={onGoToLanding}
              className="hidden sm:flex items-center space-x-1.5 px-3.5 py-1.5 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-700 hover:text-[#283139] border border-slate-200 text-xs font-semibold transition-all cursor-pointer shadow-xs"
              title="Return to Spendee Landing Showcase"
            >
              <ExternalLink className="h-3.5 w-3.5 text-[#00BC7C]" />
              <span>Spendee Home</span>
            </button>
          )}

          {/* Active User Chip & Logout */}
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200/80 px-3 py-1.5 rounded-full text-xs text-slate-700">
              <div className="h-5 w-5 rounded-full bg-[#00BC7C]/15 flex items-center justify-center text-[#00BC7C] font-bold">
                <User className="h-3 w-3" />
              </div>
              <span className="font-bold hidden sm:inline text-[#283139]">
                {currentUser?.name || currentUser?.username || 'User'}
              </span>
              <span className="text-[#00BC7C] font-mono text-[11px] font-bold">
                (ID: {currentUser?.user_id || 1})
              </span>
            </div>

            {onLogout && (
              <button
                onClick={onLogout}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-slate-50 hover:bg-rose-50 hover:border-rose-200 hover:text-rose-600 text-slate-600 transition-all border border-slate-200 text-xs font-semibold cursor-pointer shadow-xs"
                title="Log Out"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            )}
          </div>

          {/* Dynamic Notification Bell Badge */}
          <div className="relative">
            <button
              onClick={() => setShowAlertsDrawer(!showAlertsDrawer)}
              className="relative p-2 rounded-full bg-slate-50 hover:bg-slate-100 text-slate-600 hover:text-[#283139] transition-all border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#00BC7C] cursor-pointer shadow-xs"
              title="View Real-Time Alerts"
            >
              <Bell className="h-5 w-5" />
              {unreadAlertsCount > 0 && (
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-[#FE5A61] text-[10px] font-bold text-white shadow-md animate-bounce">
                  {unreadAlertsCount > 9 ? '9+' : unreadAlertsCount}
                </span>
              )}
            </button>

            {/* Notification Dropdown Drawer */}
            {showAlertsDrawer && (
              <div className="absolute right-0 mt-3 w-80 sm:w-96 bg-white border border-slate-200 rounded-3xl shadow-2xl z-50 overflow-hidden text-[#283139] animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/80">
                  <div className="flex items-center space-x-2">
                    <Bell className="h-4 w-4 text-[#00BC7C]" />
                    <h3 className="font-bold text-sm text-[#283139]">MongoDB Alert Stream</h3>
                    {unreadAlertsCount > 0 && (
                      <span className="px-2 py-0.5 rounded-full bg-[#00BC7C]/15 text-[#00BC7C] text-xs font-semibold">
                        {unreadAlertsCount} new
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-2">
                    {unreadAlertsCount > 0 && (
                      <button
                        onClick={onMarkAllRead}
                        className="text-xs text-[#00BC7C] hover:text-[#0ea573] font-semibold underline cursor-pointer"
                      >
                        Mark all read
                      </button>
                    )}
                    <button
                      onClick={() => setShowAlertsDrawer(false)}
                      className="text-slate-400 hover:text-slate-600 p-1 rounded-full hover:bg-slate-200 transition-colors cursor-pointer"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                <div className="max-h-80 overflow-y-auto divide-y divide-slate-100">
                  {alerts && alerts.length > 0 ? (
                    alerts.slice(0, 10).map((a) => {
                      const isBreach = a.severity === 'breach';
                      const isAnomaly = a.severity === 'anomaly';
                      return (
                        <div
                          key={a._id}
                          className={`p-3.5 text-xs transition-colors hover:bg-slate-50 ${
                            !a.is_read ? 'bg-[#00BC7C]/5' : ''
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex items-center space-x-1.5">
                              {isBreach ? (
                                <AlertOctagon className="h-3.5 w-3.5 text-[#FE5A61] flex-shrink-0" />
                              ) : isAnomaly ? (
                                <Cpu className="h-3.5 w-3.5 text-[#8B5CF6] flex-shrink-0" />
                              ) : (
                                <AlertTriangle className="h-3.5 w-3.5 text-[#FFC053] flex-shrink-0" />
                              )}
                              <span
                                className={`font-bold uppercase tracking-wider text-[10px] ${
                                  isBreach
                                    ? 'text-[#FE5A61]'
                                    : isAnomaly
                                    ? 'text-[#8B5CF6]'
                                    : 'text-[#d97706]'
                                }`}
                              >
                                {a.severity}
                              </span>
                              <span className="text-slate-300">•</span>
                              <span className="text-slate-700 font-semibold">{a.category}</span>
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">
                              {new Date(a.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className="mt-1 text-slate-600 text-xs leading-relaxed">
                            {typeof a.message === 'string' ? a.message.replace(/\$/g, '₹') : a.message}
                          </p>
                          {!a.is_read && (
                            <div className="mt-2 flex justify-end">
                              <button
                                onClick={() => onMarkAlertRead(a._id)}
                                className="text-[11px] text-[#00BC7C] hover:text-[#0ea573] font-bold flex items-center space-x-1 cursor-pointer"
                              >
                                <CheckCircle2 className="h-3 w-3" />
                                <span>Mark read</span>
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })
                  ) : (
                    <div className="p-6 text-center text-slate-400 text-xs">
                      No active alerts in MongoDB.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}