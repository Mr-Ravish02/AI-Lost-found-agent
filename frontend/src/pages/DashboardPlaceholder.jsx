import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { healthService } from '../services/api';
import { CheckCircle2, Shield, Activity, Sparkles, PlusCircle, Search, Clock } from 'lucide-react';

export const DashboardPlaceholder = () => {
  const { user } = useAuth();
  const [healthStatus, setHealthStatus] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await healthService.checkHealth();
        setHealthStatus(data);
      } catch (err) {
        setHealthStatus({ status: 'error', detail: 'Could not connect to FastAPI server' });
      } finally {
        setLoadingHealth(false);
      }
    };
    fetchHealth();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold mb-3">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Phase 1 Authentication Active</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">
              Welcome, {user?.full_name || 'User'}!
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Logged in as <span className="text-emerald-300 font-semibold">{user?.email}</span> ({user?.role?.toUpperCase()} role).
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center space-x-2">
              <PlusCircle className="w-4 h-4" />
              <span>Report Item (Phase 2)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Backend & DB Health Indicator */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">FastAPI Backend Status</span>
            <Activity className="w-4 h-4 text-emerald-400" />
          </div>
          {loadingHealth ? (
            <p className="text-sm text-slate-500">Checking API...</p>
          ) : (
            <div className="flex items-center space-x-2 mt-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-lg font-bold text-white">
                {healthStatus?.status === 'ok' ? 'Online & Healthy' : 'Disconnected'}
              </span>
            </div>
          )}
          <p className="text-xs text-slate-500 mt-2">Running on http://127.0.0.1:8000</p>
        </div>

        <div className="glass-card p-6 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Database Engine</span>
            <Shield className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-lg font-bold text-white mt-1">SQLite3 (SQLAlchemy 2.0)</p>
          <p className="text-xs text-slate-500 mt-2">Tables created: users, lost_items, found_items, matches</p>
        </div>

        <div className="glass-card p-6 rounded-xl border border-slate-800">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Next Implementation</span>
            <Sparkles className="w-4 h-4 text-teal-400" />
          </div>
          <p className="text-lg font-bold text-teal-300 mt-1">Phase 2: Lost/Found System</p>
          <p className="text-xs text-slate-500 mt-2">Form submission, image upload, search & user reports feed</p>
        </div>
      </div>

      {/* Empty State / Phase 1 Status */}
      <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center space-y-4">
        <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center mx-auto text-emerald-400">
          <Clock className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-white">Foundation Ready for Item Reporting & AI Agents</h3>
        <p className="text-slate-400 text-sm max-w-xl mx-auto">
          Phase 1 user authentication, JWT security tokens, database schemas, and FastAPI endpoints are successfully operating. Phase 2 will enable Lost/Found report submission and search.
        </p>
      </div>
    </div>
  );
};
