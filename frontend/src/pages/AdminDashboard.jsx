import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/api';
import {
  Shield,
  Layers,
  HelpCircle,
  PackageSearch,
  CheckCircle2,
  Clock,
  AlertCircle,
  Search,
  Sparkles,
  ArrowRight,
  ExternalLink,
  RefreshCw,
  Eye,
  CheckCheck,
  XCircle,
  HelpCircle as QuestionIcon,
  ChevronRight
} from 'lucide-react';

export const AdminDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total_lost: 0,
    total_found: 0,
    potential_matches: 0,
    pending_reviews: 0,
    resolved_cases: 0,
  });
  const [matches, setMatches] = useState([]);
  const [activeFilter, setActiveFilter] = useState('all'); // 'all', 'admin_review', 'in_progress', 'approved', 'rejected'
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);

  // Security Check: Normal users cannot access
  useEffect(() => {
    if (user && user.role !== 'admin') {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, matchesData] = await Promise.all([
        adminService.getStats(),
        adminService.getPendingMatches(),
      ]);
      setStats(statsData);
      setMatches(matchesData);
    } catch (err) {
      console.error('Failed to load admin dashboard data:', err);
      setError(err.response?.data?.detail || 'Failed to load administrator dashboard.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin') {
      loadDashboardData();
    }
  }, [user]);

  const filteredMatches = matches.filter((m) => {
    if (activeFilter === 'admin_review' && m.status !== 'admin_review') return false;
    if (activeFilter === 'in_progress' && !['in_progress', 'verification_pending', 'submitted', 'evaluated'].includes(m.status)) return false;
    if (activeFilter === 'approved' && m.status !== 'approved') return false;
    if (activeFilter === 'rejected' && m.status !== 'rejected') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const lostTitle = m.lost_item?.title?.toLowerCase() || '';
      const foundTitle = m.found_item?.title?.toLowerCase() || '';
      const category = m.lost_item?.category?.toLowerCase() || '';
      return lostTitle.includes(q) || foundTitle.includes(q) || category.includes(q);
    }

    return true;
  });

  if (user?.role !== 'admin') {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <div className="glass-panel max-w-md p-8 rounded-2xl border border-rose-500/30 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center mx-auto text-rose-400">
            <XCircle className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-white">403 — Unauthorized Access</h2>
          <p className="text-sm text-slate-400">
            This section is strictly restricted to authorized administrators.
          </p>
          <Link
            to="/dashboard"
            className="inline-block px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl"
          >
            Return to User Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-teal-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-300 text-xs font-semibold mb-3">
              <Shield className="w-3.5 h-3.5" />
              <span>Admin Decision & Review Hub</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">
              Smart Lost & Found Administrator Command Center
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Review AI-powered match recommendations, evaluate claimant ownership verifications, and approve handovers.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadDashboardData}
              disabled={loading}
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 flex items-center space-x-2 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Queue</span>
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Cards Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 sm:gap-6">
        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Lost Items</span>
            <HelpCircle className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-white">{stats.total_lost}</p>
          <p className="text-xs text-slate-500 mt-1">Reported by users</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Found Items</span>
            <PackageSearch className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-white">{stats.total_found}</p>
          <p className="text-xs text-slate-500 mt-1">In institutional custody</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Potential Matches</span>
            <Sparkles className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-emerald-400">{stats.potential_matches}</p>
          <p className="text-xs text-slate-500 mt-1">AI engine detections</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-teal-500/30 bg-teal-950/20">
          <div className="flex items-center justify-between text-teal-300 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Pending Reviews</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-amber-300">{stats.pending_reviews}</p>
          <p className="text-xs text-teal-400/80 mt-1">Action required</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Resolved Cases</span>
            <CheckCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-emerald-400">{stats.resolved_cases}</p>
          <p className="text-xs text-slate-500 mt-1">Successfully claimed</p>
        </div>
      </div>

      {/* Main Review Section */}
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              <span>AI Match Reviews</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Review and authorize ownership claims identified by the Multi-Agent matching pipeline.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search matches by title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 pr-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 w-48 sm:w-60"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center space-x-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/80 text-xs">
              <button
                onClick={() => setActiveFilter('all')}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  activeFilter === 'all'
                    ? 'bg-teal-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                All ({matches.length})
              </button>
              <button
                onClick={() => setActiveFilter('admin_review')}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  activeFilter === 'admin_review'
                    ? 'bg-amber-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Admin Review
              </button>
              <button
                onClick={() => setActiveFilter('in_progress')}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  activeFilter === 'in_progress'
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Verification
              </button>
              <button
                onClick={() => setActiveFilter('approved')}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  activeFilter === 'approved'
                    ? 'bg-emerald-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Approved
              </button>
            </div>
          </div>
        </div>

        {/* Matches Table / Grid */}
        {loading ? (
          <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-teal-400 animate-spin" />
            <p className="text-sm text-slate-400">Loading AI match reviews...</p>
          </div>
        ) : filteredMatches.length === 0 ? (
          <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center space-y-3">
            <Shield className="w-12 h-12 text-slate-600 mx-auto" />
            <h3 className="text-base font-bold text-white">No matches found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              No matching records found matching the active filter criteria.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredMatches.map((m) => {
              const isAdminReview = m.status === 'admin_review';
              const isApproved = m.status === 'approved';
              const isRejected = m.status === 'rejected';

              return (
                <div
                  key={m.match_id}
                  className={`glass-panel p-5 rounded-2xl border transition-all hover:border-slate-700 flex flex-col lg:flex-row lg:items-center justify-between gap-6 ${
                    isAdminReview
                      ? 'border-amber-500/40 bg-amber-950/10'
                      : isApproved
                      ? 'border-emerald-500/30'
                      : 'border-slate-800'
                  }`}
                >
                  {/* Match Overview & Items */}
                  <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Lost Item */}
                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-md border border-rose-500/20">
                          Lost Item #{m.lost_item?.id}
                        </span>
                        <span className="text-xs text-slate-400">{m.lost_item?.category}</span>
                      </div>
                      <h4 className="text-sm font-bold text-white truncate">{m.lost_item?.title || 'Unknown Item'}</h4>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-1">{m.lost_item?.description}</p>
                      <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
                        <span>Lost by: <strong className="text-slate-300">{m.lost_item?.user_name || 'Claimant'}</strong></span>
                        <span>{m.lost_item?.date_lost}</span>
                      </div>
                    </div>

                    {/* Found Item */}
                    <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                          Found Item #{m.found_item?.id}
                        </span>
                        <span className="text-xs text-slate-400">{m.found_item?.category}</span>
                      </div>
                      <h4 className="text-sm font-bold text-white truncate">{m.found_item?.title || 'Found Item'}</h4>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-1">{m.found_item?.description}</p>
                      <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
                        <span>Found at: <strong className="text-slate-300">{m.found_item?.location}</strong></span>
                        <span>{m.found_item?.date_found}</span>
                      </div>
                    </div>
                  </div>

                  {/* AI Scores & Status */}
                  <div className="flex flex-wrap lg:flex-nowrap items-center gap-6 lg:border-l lg:border-slate-800 lg:pl-6">
                    {/* Match Score */}
                    <div className="text-center min-w-[80px]">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">AI Match</span>
                      <span className="text-xl font-bold text-emerald-400">{m.match_score}%</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold block mt-0.5 ${
                        m.confidence_level === 'high' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                      }`}>
                        {m.confidence_level.toUpperCase()}
                      </span>
                    </div>

                    {/* Verification Score */}
                    <div className="text-center min-w-[90px]">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Verification</span>
                      {m.verification_score !== null && m.verification_score !== undefined ? (
                        <>
                          <span className="text-xl font-bold text-teal-300">{m.verification_score}%</span>
                          <span className="text-[10px] text-slate-400 block mt-0.5">Verified</span>
                        </>
                      ) : (
                        <>
                          <span className="text-sm font-medium text-slate-500 block mt-1">Pending</span>
                          <span className="text-[10px] text-slate-500 block">No answers</span>
                        </>
                      )}
                    </div>

                    {/* Status Badge */}
                    <div className="min-w-[120px]">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block mb-1">Review Status</span>
                      <span
                        className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold border ${
                          isAdminReview
                            ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 animate-pulse'
                            : isApproved
                            ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                            : isRejected
                            ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                            : 'bg-teal-500/20 border-teal-500/40 text-teal-300'
                        }`}
                      >
                        {m.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>

                    {/* Action Button */}
                    <Link
                      to={`/admin/match/${m.match_id}`}
                      className={`px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-md ${
                        isAdminReview
                          ? 'bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-white shadow-amber-600/30'
                          : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-600/20'
                      }`}
                    >
                      <span>View Details</span>
                      <ChevronRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
