import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminService } from '../services/api';
import {
  Shield,
  ArrowLeft,
  Sparkles,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  HelpCircle,
  PackageSearch,
  MapPin,
  Calendar,
  Tag,
  CheckCheck,
  User,
  MessageSquare,
  FileText,
  Loader2
} from 'lucide-react';

export const AdminMatchReview = () => {
  const { matchId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [matchData, setMatchData] = useState(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(null);
  const [error, setError] = useState(null);

  // Security Check: Normal users cannot access
  useEffect(() => {
    if (user && user.role !== 'admin') {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const loadMatchDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminService.getMatchDetail(matchId);
      setMatchData(data);
      if (data.admin_notes) {
        setAdminNotes(data.admin_notes);
      }
    } catch (err) {
      console.error('Failed to load match detail:', err);
      setError(err.response?.data?.detail || 'Failed to load match details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin' && matchId) {
      loadMatchDetails();
    }
  }, [user, matchId]);

  const handleDecision = async (actionType) => {
    if (!window.confirm(`Are you sure you want to execute action '${actionType.toUpperCase()}' for this match?`)) {
      return;
    }

    try {
      setActionLoading(true);
      setError(null);
      setActionSuccess(null);

      const payload = { notes: adminNotes.trim() || undefined, reason: adminNotes.trim() || undefined };
      let res;

      if (actionType === 'approve') {
        res = await adminService.approveMatch(matchId, payload);
        setActionSuccess('Match has been APPROVED successfully. Lost & Found items are now resolved/returned.');
      } else if (actionType === 'reject') {
        res = await adminService.rejectMatch(matchId, payload);
        setActionSuccess('Match has been REJECTED. Claimant has been notified.');
      } else if (actionType === 'request_info') {
        res = await adminService.requestMoreInfo(matchId, payload);
        setActionSuccess('Additional verification details have been requested from the claimant.');
      }

      await loadMatchDetails();
    } catch (err) {
      console.error(`Decision error (${actionType}):`, err);
      setError(err.response?.data?.detail || `Failed to execute ${actionType}.`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-10 h-10 text-teal-400 animate-spin" />
        <p className="text-sm text-slate-400">Loading AI match dossier and verification data...</p>
      </div>
    );
  }

  if (error && !matchData) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12 text-center space-y-4">
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
          {error}
        </div>
        <Link
          to="/admin"
          className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-800 text-slate-300 hover:text-white rounded-xl text-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Admin Dashboard</span>
        </Link>
      </div>
    );
  }

  const lost = matchData.lost_item || {};
  const found = matchData.found_item || {};
  const breakdown = matchData.factor_breakdown || {};
  const reasons = matchData.reasons || [];
  const questions = matchData.questions || [];
  const answers = matchData.answers || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <Link
          to="/admin"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-teal-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Admin Queue</span>
        </Link>

        <div className="flex items-center space-x-3">
          <span className="text-xs text-slate-400">Status:</span>
          <span
            className={`px-3 py-1 rounded-lg text-xs font-bold uppercase border ${
              matchData.status === 'admin_review'
                ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                : matchData.status === 'approved'
                ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                : matchData.status === 'rejected'
                ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                : 'bg-teal-500/20 border-teal-500/40 text-teal-300'
            }`}
          >
            {matchData.status.replace('_', ' ')}
          </span>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-sm flex items-center space-x-3 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Top Banner: Score Overview */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-teal-500/30 bg-gradient-to-r from-teal-950/20 via-slate-900/40 to-slate-900/60">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {/* AI Match Score */}
          <div className="flex items-center space-x-4 border-b md:border-b-0 md:border-r border-slate-800 pb-4 md:pb-0 md:pr-4">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <Sparkles className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">AI Match Score</span>
              <div className="text-3xl font-extrabold text-white mt-0.5">{matchData.match_score}%</div>
              <span className="text-xs text-emerald-300 font-semibold uppercase">{matchData.confidence_level} Confidence</span>
            </div>
          </div>

          {/* Verification Score */}
          <div className="flex items-center space-x-4 border-b md:border-b-0 md:border-r border-slate-800 pb-4 md:pb-0 md:pr-4">
            <div className="w-16 h-16 rounded-2xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-300">
              <Shield className="w-8 h-8" />
            </div>
            <div>
              <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">Verification Score</span>
              <div className="text-3xl font-extrabold text-white mt-0.5">
                {matchData.verification_score !== null && matchData.verification_score !== undefined
                  ? `${matchData.verification_score}%`
                  : 'N/A'}
              </div>
              <span className="text-xs text-teal-300 font-medium">
                {answers.length > 0 ? `${answers.length} Answers Evaluated` : 'No Answers Submitted'}
              </span>
            </div>
          </div>

          {/* Items Summary */}
          <div>
            <span className="text-xs uppercase font-bold text-slate-400 tracking-wider">Case Reference</span>
            <h3 className="text-sm font-bold text-white mt-1">Match #{matchData.match_id}</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Lost: <strong className="text-rose-300">{lost.title}</strong>
              <br />
              Found: <strong className="text-emerald-300">{found.title}</strong>
            </p>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison Dossier */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lost Item Dossier */}
        <div className="glass-panel p-6 rounded-2xl border border-rose-500/30 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <HelpCircle className="w-5 h-5 text-rose-400" />
              <h3 className="text-base font-bold text-white">Claimant's Lost Report</h3>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-300 border border-rose-500/30">
              Item #{lost.id}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-xs text-rose-400 font-semibold">{lost.category}</span>
              <h4 className="text-lg font-bold text-white">{lost.title}</h4>
            </div>

            <p className="text-xs text-slate-300 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800 whitespace-pre-line">
              {lost.description}
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Brand:</span>
                <span className="text-white font-medium">{lost.brand || 'N/A'}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Color:</span>
                <span className="text-white font-medium">{lost.color || 'N/A'}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Location Lost:</span>
                <span className="text-white font-medium">{lost.location || 'N/A'}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Date Lost:</span>
                <span className="text-white font-medium">{lost.date_lost || 'N/A'}</span>
              </div>
            </div>

            {lost.distinctive_features && (
              <div>
                <span className="text-xs font-semibold text-slate-400 block mb-1">Distinctive Features:</span>
                <div className="flex flex-wrap gap-1.5">
                  {Array.isArray(lost.distinctive_features) ? (
                    lost.distinctive_features.map((f, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 text-xs border border-rose-500/20">
                        {f}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-300">{lost.distinctive_features}</span>
                  )}
                </div>
              </div>
            )}

            <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-xs text-slate-400">
              <span>Claimant: <strong className="text-slate-200">{lost.user_name || 'Claimant'}</strong></span>
              <span>Email: <strong className="text-slate-200">{lost.user_email || 'N/A'}</strong></span>
            </div>
          </div>
        </div>

        {/* Found Item Dossier */}
        <div className="glass-panel p-6 rounded-2xl border border-emerald-500/30 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <PackageSearch className="w-5 h-5 text-emerald-400" />
              <h3 className="text-base font-bold text-white">Finder's Item Report (Custody)</h3>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
              Item #{found.id}
            </span>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-xs text-emerald-400 font-semibold">{found.category}</span>
              <h4 className="text-lg font-bold text-white">{found.title}</h4>
            </div>

            <p className="text-xs text-slate-300 bg-slate-900/60 p-3.5 rounded-xl border border-slate-800 whitespace-pre-line">
              {found.description}
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Brand:</span>
                <span className="text-white font-medium">{found.brand || 'N/A'}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Color:</span>
                <span className="text-white font-medium">{found.color || 'N/A'}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Location Found:</span>
                <span className="text-white font-medium">{found.location || 'N/A'}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-800/60 border border-slate-700/60">
                <span className="text-slate-400 block">Date Found:</span>
                <span className="text-white font-medium">{found.date_found || 'N/A'}</span>
              </div>
            </div>

            {found.distinctive_features && (
              <div>
                <span className="text-xs font-semibold text-slate-400 block mb-1">Found Distinctive Features:</span>
                <div className="flex flex-wrap gap-1.5">
                  {Array.isArray(found.distinctive_features) ? (
                    found.distinctive_features.map((f, i) => (
                      <span key={i} className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 text-xs border border-emerald-500/20">
                        {f}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-300">{found.distinctive_features}</span>
                  )}
                </div>
              </div>
            )}

            <div className="border-t border-slate-800 pt-3 flex items-center justify-between text-xs text-slate-400">
              <span>Finder: <strong className="text-slate-200">{found.user_name || 'Staff / Finder'}</strong></span>
              <span>Email: <strong className="text-slate-200">{found.user_email || 'N/A'}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Similarity Factors & AI Reasons */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Factor Breakdown */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>Matching Factor Breakdown</span>
          </h3>

          <div className="space-y-3 pt-2">
            {Object.keys(breakdown).length > 0 ? (
              Object.entries(breakdown).map(([factor, val]) => (
                <div key={factor} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-slate-400 capitalize">{factor}</span>
                    <span className="text-emerald-300 font-bold">{val}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        val >= 80 ? 'bg-emerald-500' : val >= 50 ? 'bg-teal-500' : 'bg-amber-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, val))}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500">No factor breakdown available.</p>
            )}
          </div>
        </div>

        {/* AI Reasons & Explanation */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>AI Match Verification Reasons</span>
          </h3>

          <div className="space-y-2 pt-2">
            {reasons.length > 0 ? (
              reasons.map((r, i) => (
                <div key={i} className="flex items-start space-x-2.5 text-xs text-slate-300">
                  <CheckCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span>{r}</span>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-500">No matching reasons logged.</p>
            )}
          </div>

          {matchData.verification_evaluation && (
            <div className="mt-4 p-3.5 rounded-xl bg-teal-950/30 border border-teal-500/30">
              <span className="text-xs font-bold text-teal-300 uppercase tracking-wider block mb-1">
                Verification Agent Assessment:
              </span>
              <p className="text-xs text-slate-300">{matchData.verification_evaluation}</p>
            </div>
          )}
        </div>
      </div>

      {/* Ownership Verification Answers */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center space-x-2">
          <Shield className="w-4 h-4 text-teal-400" />
          <span>Claimant Verification Submission Details</span>
        </h3>

        {questions.length === 0 ? (
          <p className="text-xs text-slate-500">No verification questions were generated yet.</p>
        ) : answers.length === 0 ? (
          <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs">
            Questions have been generated, but the claimant has not submitted their answers yet.
          </div>
        ) : (
          <div className="space-y-4">
            {answers.map((ans, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-emerald-400">
                    Question #{idx + 1} ({ans.question_id ? `QID: ${ans.question_id}` : 'General'})
                  </span>
                  {ans.evaluation_score !== null && (
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                      ans.evaluation_score >= 80 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                    }`}>
                      Score: {ans.evaluation_score}%
                    </span>
                  )}
                </div>

                <div className="p-3 rounded-lg bg-slate-800/70 border border-slate-700/60 text-xs text-white">
                  <span className="text-slate-400 block mb-1">Claimant's Answer:</span>
                  <p className="font-medium">{ans.answer_text}</p>
                </div>

                {ans.evaluation_feedback && (
                  <p className="text-[11px] text-teal-300 flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5 flex-shrink-0" />
                    <span>AI Evaluation: {ans.evaluation_feedback}</span>
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Administrator Action Panel */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-teal-500/40 bg-slate-900/80 space-y-6">
        <div>
          <h3 className="text-base font-bold text-white flex items-center space-x-2">
            <Shield className="w-5 h-5 text-teal-400" />
            <span>Administrator Decision & Action</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Carefully review all evidence above. Approval will mark the case as resolved/returned.
          </p>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
            Administrative Decision Notes / Justification:
          </label>
          <textarea
            rows={3}
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            placeholder="Add notes for claimant and audit logs (e.g. 'Serial number verified at helpdesk, items released to owner')..."
            className="w-full p-3.5 rounded-xl bg-slate-800/80 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-slate-800 pt-5">
          <button
            onClick={() => handleDecision('request_info')}
            disabled={actionLoading}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/30 text-xs font-semibold rounded-xl flex items-center space-x-2 transition-colors disabled:opacity-50"
          >
            <HelpCircle className="w-4 h-4" />
            <span>REQUEST MORE INFORMATION</span>
          </button>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => handleDecision('reject')}
              disabled={actionLoading}
              className="px-5 py-2.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 text-xs font-bold rounded-xl flex items-center space-x-2 transition-colors disabled:opacity-50"
            >
              <XCircle className="w-4 h-4" />
              <span>REJECT MATCH</span>
            </button>

            <button
              onClick={() => handleDecision('approve')}
              disabled={actionLoading}
              className="px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02] disabled:opacity-50"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>APPROVE MATCH</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
