import React, { useState, useEffect } from 'react';
import SpendeeLogo from './SpendeeLogo';
import { 
  Sparkles, 
  Lock, 
  User, 
  Mail, 
  Eye, 
  EyeOff, 
  ArrowRight, 
  ShieldCheck, 
  AlertCircle, 
  UserCheck, 
  Layers,
  ArrowLeft
} from 'lucide-react';

export default function LoginScreen({ onLoginSuccess, onBackToLanding }) {
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [demoUsers, setDemoUsers] = useState([]);

  useEffect(() => {
    // Fetch available demo users for quick demonstration
    fetch('/api/auth/users')
      .then(res => res.ok ? res.json() : [])
      .then(data => setDemoUsers(data))
      .catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!username.trim()) {
      setErrorMsg('Please enter your username.');
      return;
    }
    if (!password.trim()) {
      setErrorMsg('Please enter your password.');
      return;
    }

    setLoading(true);

    try {
      if (isRegisterMode) {
        // Register API call
        const res = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: username.trim(),
            password: password.trim(),
            name: fullName.trim() || username.trim(),
            email: email.trim() || `${username.trim().toLowerCase()}@example.com`
          })
        });

        const data = await res.json();
        if (!res.ok) {
          setErrorMsg(data.detail || 'Registration failed.');
        } else {
          if (data.access_token) {
            localStorage.setItem('jwt_token', data.access_token);
          }
          onLoginSuccess(data.user);
        }
      } else {
        // Login API call
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: username.trim(),
            password: password.trim()
          })
        });

        const data = await res.json();
        if (!res.ok) {
          setErrorMsg(data.detail || 'Invalid username or password.');
        } else {
          if (data.access_token) {
            localStorage.setItem('jwt_token', data.access_token);
          }
          onLoginSuccess(data.user);
        }
      }
    } catch (err) {
      setErrorMsg('Failed to connect to backend server. Make sure FastAPI is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (uname, pwd) => {
    setUsername(uname);
    setPassword(pwd);
    setErrorMsg(null);
    setIsRegisterMode(false);
  };

  return (
    <div className="min-h-screen bg-[#F8FAF9] text-[#283139] flex flex-col justify-center items-center p-4 relative overflow-hidden font-sans selection:bg-[#00BC7C] selection:text-white">
      {/* Spendee Soft Glow Background Elements */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-[#12C48B]/15 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-[#40C3F9]/10 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-md w-full relative z-10">
        {/* Back to Spendee Home Button */}
        {onBackToLanding && (
          <div className="mb-4">
            <button
              onClick={onBackToLanding}
              className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-500 hover:text-[#00BC7C] bg-white hover:bg-slate-50 px-3.5 py-1.5 rounded-full border border-slate-200 shadow-xs transition-all cursor-pointer"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Back to Spendee Home</span>
            </button>
          </div>
        )}

        {/* Spendee Brand Header */}
        <div className="text-center mb-6 space-y-2">
          <div className="flex justify-center">
            <SpendeeLogo className="h-10" showText={true} />
          </div>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Log in to manage your budgets, view AI forecasts, and track your ledger.
          </p>
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#00BC7C]/10 border border-[#00BC7C]/20 text-[11px] font-semibold text-[#00BC7C]">
            <ShieldCheck className="h-3.5 w-3.5" />
            <span>PostgreSQL ACID + MongoDB Cloud Cluster</span>
          </div>
        </div>

        {/* Main Auth Card (Spendee Crisp White & Subtle Shadow) */}
        <div className="bg-white border border-slate-200/90 rounded-3xl p-6 sm:p-8 shadow-xl">
          {/* Mode Switch Tabs */}
          <div className="flex bg-[#F4F7F6] p-1 rounded-2xl border border-slate-200/80 mb-6">
            <button
              type="button"
              onClick={() => { setIsRegisterMode(false); setErrorMsg(null); }}
              className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                !isRegisterMode 
                  ? 'bg-[#00BC7C] text-white shadow-md shadow-[#00BC7C]/25' 
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsRegisterMode(true); setErrorMsg(null); }}
              className={`flex-1 py-2.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                isRegisterMode 
                  ? 'bg-[#00BC7C] text-white shadow-md shadow-[#00BC7C]/25' 
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* Error Alert */}
          {errorMsg && (
            <div className="mb-5 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 text-xs flex items-start space-x-2.5">
              <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-rose-500" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegisterMode && (
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Sukhavasi Yaswanth"
                    className="w-full bg-[#F8FAF9] border border-slate-200 focus:border-[#00BC7C] focus:ring-1 focus:ring-[#00BC7C] rounded-xl pl-10 pr-4 py-2.5 text-xs text-[#283139] placeholder:text-slate-400 outline-none transition"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                {isRegisterMode ? 'Username' : 'Username or Email'}
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={isRegisterMode ? "Choose a unique username" : "Enter username (e.g. yaswanth)"}
                  className="w-full bg-[#F8FAF9] border border-slate-200 focus:border-[#00BC7C] focus:ring-1 focus:ring-[#00BC7C] rounded-xl pl-10 pr-4 py-2.5 text-xs text-[#283139] placeholder:text-slate-400 outline-none transition"
                />
              </div>
            </div>

            {isRegisterMode && (
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Email (Optional)</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. user@example.com"
                    className="w-full bg-[#F8FAF9] border border-slate-200 focus:border-[#00BC7C] focus:ring-1 focus:ring-[#00BC7C] rounded-xl pl-10 pr-4 py-2.5 text-xs text-[#283139] placeholder:text-slate-400 outline-none transition"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password (e.g. password123)"
                  className="w-full bg-[#F8FAF9] border border-slate-200 focus:border-[#00BC7C] focus:ring-1 focus:ring-[#00BC7C] rounded-xl pl-10 pr-10 py-2.5 text-xs text-[#283139] placeholder:text-slate-400 outline-none transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {isRegisterMode && (
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800 flex items-center space-x-2">
                <Layers className="h-4 w-4 flex-shrink-0 text-[#00BC7C]" />
                <span>New accounts automatically get Checking, Savings, and Indian category budgets.</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 rounded-xl bg-[#00BC7C] hover:bg-[#0ea573] text-white font-bold text-xs shadow-lg shadow-[#00BC7C]/25 transition-all flex items-center justify-center space-x-2 disabled:opacity-50 cursor-pointer active:scale-98"
            >
              {loading ? (
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <span>{isRegisterMode ? 'Create Account & Open Dashboard' : 'Sign In'}</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Login Helper */}
          <div className="mt-6 pt-5 border-t border-slate-100">
            <div className="text-[11px] font-bold text-slate-500 mb-2.5 flex items-center space-x-1.5">
              <UserCheck className="h-3.5 w-3.5 text-[#00BC7C]" />
              <span>Quick Login (Demo Accounts):</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {demoUsers && demoUsers.length > 0 ? (
                demoUsers.slice(0, 4).map((u) => {
                  const defaultPwd = u.user_id === 1 ? 'password123' : (u.username === 'demouser' ? 'demo123' : 'password123');
                  const isPrimary = u.user_id === 1;
                  return (
                    <button
                      key={u.user_id}
                      type="button"
                      onClick={() => handleQuickLogin(u.username, defaultPwd)}
                      className="p-2.5 rounded-xl bg-[#F8FAF9] hover:bg-emerald-50/50 border border-slate-200 hover:border-[#00BC7C]/50 text-left transition-all group cursor-pointer"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-700 group-hover:text-[#00BC7C] truncate max-w-[120px]">
                          {u.name || u.username}
                        </span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-bold ${isPrimary ? 'bg-[#00BC7C]/15 text-[#00BC7C]' : 'bg-[#40C3F9]/15 text-[#0284c7]'}`}>
                          ID: {u.user_id}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {isPrimary ? '60-day Indian history' : 'Isolated ledger'}
                      </p>
                    </button>
                  );
                })
              ) : (
                <>
                  <button
                    type="button"
                    onClick={() => handleQuickLogin('yaswanth', 'password123')}
                    className="p-2.5 rounded-xl bg-[#F8FAF9] hover:bg-emerald-50/50 border border-slate-200 hover:border-[#00BC7C]/50 text-left transition-all group cursor-pointer"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-700 group-hover:text-[#00BC7C]">
                        Yaswanth
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#00BC7C]/15 text-[#00BC7C] font-mono font-bold">
                        ID: 1
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      60-day Indian history
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={() => handleQuickLogin('demouser', 'demo123')}
                    className="p-2.5 rounded-xl bg-[#F8FAF9] hover:bg-emerald-50/50 border border-slate-200 hover:border-[#00BC7C]/50 text-left transition-all group cursor-pointer"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-700 group-hover:text-[#00BC7C]">
                        Demo User
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#40C3F9]/15 text-[#0284c7] font-mono font-bold">
                        ID: 2
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      Isolated ledger
                    </p>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Footer info */}
        <p className="text-center text-[11px] text-slate-400 mt-5">
          Spendee AI • PostgreSQL 18 ACID Engine • MongoDB Atlas Cloud • Scikit-Learn
        </p>
      </div>
    </div>
  );
}
