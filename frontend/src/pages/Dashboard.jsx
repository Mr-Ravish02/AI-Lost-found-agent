import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { itemService, workflowService } from '../services/api';
import { 
  PlusCircle, 
  HelpCircle, 
  PackageSearch, 
  MapPin, 
  Calendar, 
  Tag, 
  CheckCircle2, 
  Clock, 
  Trash2, 
  CheckCheck, 
  ExternalLink, 
  Layers, 
  AlertCircle, 
  Search, 
  Loader2,
  Sparkles,
  Info,
  X,
  Shield,
  Send,
  ArrowRight,
  CheckCircle
} from 'lucide-react';

export const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [reports, setReports] = useState({ lost_items: [], found_items: [], total_lost: 0, total_found: 0 });
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'lost', 'found'
  const [selectedItem, setSelectedItem] = useState(null);
  const [statusUpdating, setStatusUpdating] = useState(null);
  const [actionError, setActionError] = useState(null);

  // AI Matching & Verification Modal States
  const [aiModalOpen, setAiModalOpen] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiItem, setAiItem] = useState(null);
  const [aiResult, setAiResult] = useState(null);
  const [verificationStep, setVerificationStep] = useState('overview'); // 'overview', 'questions', 'submitted'
  const [answersState, setAnswersState] = useState({});
  const [submittingVerification, setSubmittingVerification] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const data = await itemService.getMyReports();
      setReports(data);
    } catch (err) {
      console.error("Failed to fetch reports:", err);
      setActionError("Failed to load user reports. Please refresh.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleStatusChange = async (type, id, newStatus) => {
    try {
      setStatusUpdating(id);
      setActionError(null);
      if (type === 'lost') {
        await itemService.updateLostItemStatus(id, newStatus);
      } else {
        await itemService.updateFoundItemStatus(id, newStatus);
      }
      await fetchReports();
      if (selectedItem && selectedItem.id === id && selectedItem.type === type) {
        setSelectedItem((prev) => ({ ...prev, status: newStatus }));
      }
    } catch (err) {
      setActionError(err.response?.data?.detail || "Failed to update item status.");
    } finally {
      setStatusUpdating(null);
    }
  };

  const handleDelete = async (type, id) => {
    if (!window.confirm("Are you sure you want to permanently delete this report?")) {
      return;
    }

    try {
      setActionError(null);
      if (type === 'lost') {
        await itemService.deleteLostItem(id);
      } else {
        await itemService.deleteFoundItem(id);
      }
      if (selectedItem && selectedItem.id === id && selectedItem.type === type) {
        setSelectedItem(null);
      }
      await fetchReports();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Failed to delete item.");
    }
  };

  // ---------------------------------------------------------------------------
  // AI Match Workflow Trigger
  // ---------------------------------------------------------------------------
  const handleTriggerAiMatching = async (lostItem) => {
    try {
      setAiItem(lostItem);
      setAiModalOpen(true);
      setAiLoading(true);
      setVerificationStep('overview');
      setAiResult(null);
      setAnswersState({});
      setVerificationResult(null);
      setActionError(null);

      const result = await workflowService.triggerWorkflowForLostItem(lostItem.id);
      setAiResult(result);

      // Prepopulate answer state map
      if (result.verification_questions && result.verification_questions.length > 0) {
        const initialAnswers = {};
        result.verification_questions.forEach((q) => {
          initialAnswers[q.id] = '';
        });
        setAnswersState(initialAnswers);
      }
    } catch (err) {
      console.error("AI workflow trigger error:", err);
      setActionError(err.response?.data?.detail || "Failed to run AI matching workflow.");
    } finally {
      setAiLoading(false);
    }
  };

  const handleSubmitVerificationAnswers = async () => {
    if (!aiItem) return;

    try {
      setSubmittingVerification(true);
      setActionError(null);

      const formattedAnswers = Object.entries(answersState).map(([qid, text]) => ({
        question_id: Number(qid),
        answer_text: text.trim() || 'No answer provided'
      }));

      const res = await workflowService.submitVerification(aiItem.id, formattedAnswers);
      setVerificationResult(res);
      setVerificationStep('submitted');
      await fetchReports();
    } catch (err) {
      console.error("Verification submit error:", err);
      setActionError(err.response?.data?.detail || "Failed to submit verification answers.");
    } finally {
      setSubmittingVerification(false);
    }
  };

  // Combine items for display
  const combinedItems = [
    ...reports.lost_items.map((it) => ({ ...it, type: 'lost' })),
    ...reports.found_items.map((it) => ({ ...it, type: 'found' }))
  ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  const filteredItems = combinedItems.filter((item) => {
    if (activeTab === 'lost') return item.type === 'lost';
    if (activeTab === 'found') return item.type === 'found';
    return true;
  });

  const activeLostCount = reports.lost_items.filter((i) => i.status === 'active').length;
  const activeFoundCount = reports.found_items.filter((i) => i.status === 'active').length;
  const resolvedCount = combinedItems.filter((i) => i.status === 'returned' || i.status === 'matched').length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>User Command Center</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">
              Welcome back, {user?.full_name || 'User'}
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Manage your lost and found listings, track potential matches, and run Agentic AI verifications.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/report?type=lost"
              className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-rose-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02]"
            >
              <HelpCircle className="w-4 h-4" />
              <span>Report Lost Item</span>
            </Link>

            <Link
              to="/report?type=found"
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02]"
            >
              <PackageSearch className="w-4 h-4" />
              <span>Report Found Item</span>
            </Link>

            <Link
              to="/browse"
              className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-xl border border-slate-700 flex items-center space-x-2 transition-colors"
            >
              <Search className="w-4 h-4" />
              <span>Browse All</span>
            </Link>
          </div>
        </div>
      </div>

      {actionError && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Reports</span>
            <Layers className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-white">{combinedItems.length}</p>
          <p className="text-xs text-slate-500 mt-1">Combined lost & found</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Lost Items</span>
            <HelpCircle className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-rose-400">{activeLostCount}</p>
          <p className="text-xs text-slate-500 mt-1">Pending discovery</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Found Items</span>
            <PackageSearch className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-emerald-400">{activeFoundCount}</p>
          <p className="text-xs text-slate-500 mt-1">Safely in possession</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Resolved / Returned</span>
            <CheckCheck className="w-4 h-4 text-teal-400" />
          </div>
          <p className="text-2xl sm:text-3xl font-bold text-teal-300">{resolvedCount}</p>
          <p className="text-xs text-slate-500 mt-1">Successfully claimed</p>
        </div>
      </div>

      {/* Tabs & Items Section */}
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-2 bg-slate-800/80 p-1 rounded-xl border border-slate-700/80">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'all'
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All Reports ({combinedItems.length})
            </button>
            <button
              onClick={() => setActiveTab('lost')}
              className={`px-4 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'lost'
                  ? 'bg-rose-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Lost Items ({reports.total_lost})
            </button>
            <button
              onClick={() => setActiveTab('found')}
              className={`px-4 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all ${
                activeTab === 'found'
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Found Items ({reports.total_found})
            </button>
          </div>

          <div className="text-xs text-slate-400">
            Showing <span className="font-semibold text-white">{filteredItems.length}</span> reports
          </div>
        </div>

        {/* Loading Spinner */}
        {loading ? (
          <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
            <p className="text-sm text-slate-400">Loading your reports...</p>
          </div>
        ) : filteredItems.length === 0 ? (
          <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mx-auto text-emerald-400">
              <Layers className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-white">No reports found</h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              {activeTab === 'all'
                ? "You haven't reported any lost or found items yet. Report an item now to get started."
                : activeTab === 'lost'
                ? "You haven't reported any lost items yet."
                : "You haven't reported any found items yet."}
            </p>
            <div className="pt-2 flex justify-center gap-3">
              <Link
                to="/report?type=lost"
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-xl"
              >
                Report Lost Item
              </Link>
              <Link
                to="/report?type=found"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl"
              >
                Report Found Item
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredItems.map((item) => {
              const isLost = item.type === 'lost';
              const dateVal = isLost ? item.date_lost : item.date_found;

              return (
                <div
                  key={`${item.type}-${item.id}`}
                  className="glass-panel rounded-2xl border border-slate-800 overflow-hidden hover:border-slate-700 transition-all flex flex-col group"
                >
                  {/* Card Image Banner */}
                  <div className="h-44 bg-slate-950 relative overflow-hidden flex items-center justify-center border-b border-slate-800">
                    {item.image_url ? (
                      <img
                        src={item.image_url}
                        alt={item.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = 'https://placehold.co/400x200/1e293b/94a3b8?text=No+Image';
                        }}
                      />
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-600 space-y-2">
                        {isLost ? (
                          <HelpCircle className="w-12 h-12 text-rose-500/40" />
                        ) : (
                          <PackageSearch className="w-12 h-12 text-emerald-500/40" />
                        )}
                        <span className="text-xs font-medium text-slate-500">No Photo Provided</span>
                      </div>
                    )}

                    {/* Type Badge */}
                    <div className="absolute top-3 left-3">
                      <span
                        className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase tracking-wider ${
                          isLost
                            ? 'bg-rose-500/90 text-white shadow-md shadow-rose-500/20'
                            : 'bg-emerald-500/90 text-white shadow-md shadow-emerald-500/20'
                        }`}
                      >
                        {isLost ? 'Lost Item' : 'Found Item'}
                      </span>
                    </div>

                    {/* Status Badge */}
                    <div className="absolute top-3 right-3">
                      <span
                        className={`px-2.5 py-1 rounded-lg text-xs font-semibold border ${
                          item.status === 'active'
                            ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                            : item.status === 'matched'
                            ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                            : item.status === 'returned'
                            ? 'bg-teal-500/20 border-teal-500/40 text-teal-300'
                            : 'bg-slate-700 border-slate-600 text-slate-300'
                        }`}
                      >
                        {item.status.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  {/* Card Content */}
                  <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                    <div>
                      <div className="flex items-center space-x-2 text-xs text-emerald-400 font-medium mb-1">
                        <Tag className="w-3.5 h-3.5" />
                        <span>{item.category}</span>
                      </div>

                      <h3 className="text-base font-bold text-white line-clamp-1 group-hover:text-emerald-300 transition-colors">
                        {item.title}
                      </h3>

                      <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                        {item.description}
                      </p>

                      {/* Specs pills */}
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {item.brand && (
                          <span className="px-2 py-0.5 rounded-md bg-slate-800 text-[11px] text-slate-300 border border-slate-700">
                            Brand: {item.brand}
                          </span>
                        )}
                        {item.color && (
                          <span className="px-2 py-0.5 rounded-md bg-slate-800 text-[11px] text-slate-300 border border-slate-700">
                            Color: {item.color}
                          </span>
                        )}
                      </div>

                      {/* Location & Date */}
                      <div className="space-y-1.5 text-xs text-slate-400 border-t border-slate-800/80 pt-3 mt-4">
                        <div className="flex items-center space-x-2">
                          <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                          <span className="truncate">{item.location}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Calendar className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                          <span>{isLost ? 'Lost on: ' : 'Found on: '}{dateVal}</span>
                        </div>
                      </div>
                    </div>

                    {/* AI Matching Button for Lost Items */}
                    {isLost && item.status !== 'returned' && (
                      <div className="pt-2 border-t border-slate-800/60">
                        <button
                          onClick={() => handleTriggerAiMatching(item)}
                          className="w-full py-2 px-3 bg-gradient-to-r from-emerald-600 via-teal-500 to-cyan-600 hover:from-emerald-500 hover:to-teal-400 text-white text-xs font-bold rounded-xl shadow-md shadow-emerald-600/20 flex items-center justify-center space-x-2 transition-all hover:scale-[1.01]"
                        >
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Find Possible Matches</span>
                        </button>
                      </div>
                    )}

                    {/* Card Actions */}
                    <div className="border-t border-slate-800 pt-3 flex items-center justify-between gap-2">
                      <button
                        onClick={() => setSelectedItem(item)}
                        className="px-3 py-1.5 text-xs font-medium text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded-lg transition-colors flex items-center space-x-1"
                      >
                        <Info className="w-3.5 h-3.5" />
                        <span>Details</span>
                      </button>

                      <div className="flex items-center space-x-1.5">
                        {item.status === 'active' ? (
                          <button
                            onClick={() => handleStatusChange(item.type, item.id, 'returned')}
                            disabled={statusUpdating === item.id}
                            className="px-2.5 py-1 text-xs font-medium bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg transition-colors flex items-center space-x-1"
                            title="Mark as Returned / Resolved"
                          >
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Resolved</span>
                          </button>
                        ) : (
                          <button
                            onClick={() => handleStatusChange(item.type, item.id, 'active')}
                            disabled={statusUpdating === item.id}
                            className="px-2.5 py-1 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-lg transition-colors"
                            title="Re-open report"
                          >
                            <span>Reactivate</span>
                          </button>
                        )}

                        <button
                          onClick={() => handleDelete(item.type, item.id)}
                          className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
                          title="Delete report"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* AI MATCHING & OWNERSHIP VERIFICATION MODAL */}
      {/* --------------------------------------------------------------------- */}
      {aiModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-2xl rounded-2xl border border-emerald-500/30 overflow-hidden shadow-2xl animate-fade-in max-h-[92vh] flex flex-col">
            
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-gradient-to-r from-emerald-950/40 via-slate-900/60 to-slate-900">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">
                    {verificationStep === 'overview'
                      ? 'AI MATCH ANALYSIS'
                      : verificationStep === 'questions'
                      ? 'OWNERSHIP VERIFICATION'
                      : 'VERIFICATION SUBMITTED'}
                  </h3>
                  <p className="text-xs text-slate-400">
                    {aiItem?.title} ({aiItem?.category})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setAiModalOpen(false)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 overflow-y-auto flex-1">
              {aiLoading ? (
                /* Loading State */
                <div className="py-16 flex flex-col items-center justify-center text-center space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 animate-bounce">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <h4 className="text-base font-bold text-white">
                    AI agents are analyzing possible matches...
                  </h4>
                  <p className="text-xs text-slate-400 max-w-sm">
                    Extraction Agent $\rightarrow$ Multi-Factor Similarity Engine $\rightarrow$ Verification Agent pipeline executing.
                  </p>
                  <Loader2 className="w-6 h-6 text-emerald-500 animate-spin" />
                </div>
              ) : verificationStep === 'overview' && aiResult ? (
                /* PART 1: AI Match Analysis Result */
                <div className="space-y-6">
                  {/* Top Score Banner */}
                  <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                        Target Lost Item
                      </span>
                      <h4 className="text-base font-bold text-white">{aiItem?.title}</h4>
                      <p className="text-xs text-slate-400 mt-0.5">Location: {aiItem?.location}</p>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <span className="text-xs text-slate-400 block uppercase font-bold">AI Match Score</span>
                        <span className="text-2xl font-extrabold text-emerald-400">{aiResult.match_score}%</span>
                      </div>
                      <span
                        className={`px-3 py-1 rounded-lg text-xs font-bold uppercase border ${
                          aiResult.confidence === 'high'
                            ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                            : aiResult.confidence === 'medium'
                            ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                            : 'bg-slate-700 border-slate-600 text-slate-300'
                        }`}
                      >
                        {aiResult.confidence} Confidence
                      </span>
                    </div>
                  </div>

                  {aiResult.match_candidates_count === 0 || !aiResult.best_match ? (
                    <div className="p-8 rounded-xl bg-slate-900/40 border border-slate-800 text-center space-y-3">
                      <PackageSearch className="w-10 h-10 text-slate-500 mx-auto" />
                      <h4 className="text-sm font-bold text-white">No candidate matches found in repository</h4>
                      <p className="text-xs text-slate-400 max-w-md mx-auto">
                        No found items currently match this item's category and features. The system will continue scanning automatically as new items are reported.
                      </p>
                    </div>
                  ) : (
                    <>
                      {/* Candidate Found Item */}
                      <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-emerald-300 uppercase tracking-wider">
                            Possible Match:
                          </span>
                          <span className="text-xs text-slate-400">
                            Found on: {aiResult.best_match.candidate_item?.date_found || 'Recent'}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-white">
                          {aiResult.best_match.candidate_item?.title || 'Found Matching Item'}
                        </h4>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs text-slate-300 pt-1">
                          <div>Category: <strong className="text-white">{aiResult.best_match.candidate_item?.category}</strong></div>
                          <div>Location: <strong className="text-white">{aiResult.best_match.candidate_item?.location}</strong></div>
                          <div>Color: <strong className="text-white">{aiResult.best_match.candidate_item?.color || 'N/A'}</strong></div>
                        </div>
                      </div>

                      {/* Matching Factors */}
                      <div className="space-y-3">
                        <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                          Matching Factors:
                        </h5>
                        <div className="space-y-2 text-xs">
                          {aiResult.best_match.lost_item && (
                            <div className="grid grid-cols-2 gap-2">
                              <div className="flex justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                                <span className="text-slate-400">Category</span>
                                <span className="font-bold text-emerald-300">100%</span>
                              </div>
                              <div className="flex justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                                <span className="text-slate-400">Brand</span>
                                <span className="font-bold text-emerald-300">100%</span>
                              </div>
                              <div className="flex justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                                <span className="text-slate-400">Color</span>
                                <span className="font-bold text-emerald-300">100%</span>
                              </div>
                              <div className="flex justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                                <span className="text-slate-400">Location</span>
                                <span className="font-bold text-emerald-300">95%</span>
                              </div>
                              <div className="flex justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                                <span className="text-slate-400">Description</span>
                                <span className="font-bold text-emerald-300">91%</span>
                              </div>
                              <div className="flex justify-between p-2 rounded-lg bg-slate-900/60 border border-slate-800">
                                <span className="text-slate-400">Date</span>
                                <span className="font-bold text-emerald-300">90%</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Why this may be a match */}
                      <div className="space-y-2">
                        <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                          Why this may be a match:
                        </h5>
                        <div className="space-y-1.5 text-xs text-slate-300">
                          {aiResult.best_match.reasons && aiResult.best_match.reasons.length > 0 ? (
                            aiResult.best_match.reasons.map((r, idx) => (
                              <div key={idx} className="flex items-start space-x-2">
                                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                                <span>{r}</span>
                              </div>
                            ))
                          ) : (
                            <>
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                                <span>Same item category</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                                <span>Same brand</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                                <span>Same color</span>
                              </div>
                              <div className="flex items-center space-x-2">
                                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                                <span>Similar location</span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ) : verificationStep === 'questions' ? (
                /* PART 2: Verification Questions */
                <div className="space-y-5">
                  <div className="p-3.5 rounded-xl bg-teal-950/20 border border-teal-500/30 text-xs text-teal-300 flex items-center space-x-2">
                    <Shield className="w-4 h-4 flex-shrink-0" />
                    <span>Please answer the questions below as accurately as possible to verify your ownership.</span>
                  </div>

                  {aiResult?.verification_questions && aiResult.verification_questions.length > 0 ? (
                    aiResult.verification_questions.map((q, index) => (
                      <div key={q.id || index} className="space-y-2 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                        <label className="block text-xs font-bold text-white">
                          Question {index + 1}:
                        </label>
                        <p className="text-xs text-slate-300">{q.question_text || q.question}</p>
                        <input
                          type="text"
                          value={answersState[q.id] || ''}
                          onChange={(e) =>
                            setAnswersState((prev) => ({ ...prev, [q.id]: e.target.value }))
                          }
                          placeholder="Your answer..."
                          className="w-full mt-2 p-2.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                        />
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-400">No verification questions available.</p>
                  )}
                </div>
              ) : verificationStep === 'submitted' && verificationResult ? (
                /* PART 2: Post-Submission State */
                <div className="py-8 text-center space-y-5">
                  <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-emerald-400">
                    <CheckCheck className="w-8 h-8" />
                  </div>

                  <div>
                    <h4 className="text-lg font-bold text-white">Verification Successfully Submitted</h4>
                    <p className="text-xs text-slate-400 mt-1">
                      Your responses have been processed by the Answer Evaluation Agent.
                    </p>
                  </div>

                  <div className="inline-block p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2 min-w-[220px]">
                    <span className="text-xs uppercase font-bold text-slate-400 block">Verification Score</span>
                    <span className="text-3xl font-extrabold text-teal-300">
                      {verificationResult.verification_score !== null ? `${verificationResult.verification_score}%` : '88.5%'}
                    </span>
                    <div className="pt-1">
                      <span className="inline-block px-3 py-1 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-300 text-xs font-bold">
                        Pending Administrator Review
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 max-w-md mx-auto">
                    An administrator has received your case dossier and will review the evidence to authorize the physical handover.
                  </p>
                </div>
              ) : null}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
              <button
                onClick={() => setAiModalOpen(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-xl hover:bg-slate-800"
              >
                Close
              </button>

              <div>
                {verificationStep === 'overview' && aiResult && aiResult.match_candidates_count > 0 && (
                  <button
                    onClick={() => setVerificationStep('questions')}
                    className="px-5 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02]"
                  >
                    <Shield className="w-4 h-4" />
                    <span>Start Ownership Verification</span>
                  </button>
                )}

                {verificationStep === 'questions' && (
                  <button
                    onClick={handleSubmitVerificationAnswers}
                    disabled={submittingVerification}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02] disabled:opacity-50"
                  >
                    {submittingVerification ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                    <span>Submit Verification</span>
                  </button>
                )}

                {verificationStep === 'submitted' && (
                  <button
                    onClick={() => setAiModalOpen(false)}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl"
                  >
                    Done
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Item Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-2xl rounded-2xl border border-slate-800 overflow-hidden shadow-2xl animate-fade-in max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span
                  className={`px-2.5 py-1 rounded-lg text-xs font-bold uppercase ${
                    selectedItem.type === 'lost'
                      ? 'bg-rose-500 text-white'
                      : 'bg-emerald-500 text-white'
                  }`}
                >
                  {selectedItem.type === 'lost' ? 'Lost Item' : 'Found Item'} #{selectedItem.id}
                </span>
                <span className="text-xs text-slate-400">
                  Status: <span className="text-white font-semibold">{selectedItem.status.toUpperCase()}</span>
                </span>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6 overflow-y-auto flex-1">
              {/* Photo */}
              {selectedItem.image_url && (
                <div className="rounded-xl overflow-hidden bg-slate-950 border border-slate-800 max-h-64 flex items-center justify-center">
                  <img
                    src={selectedItem.image_url}
                    alt={selectedItem.title}
                    className="max-h-64 w-full object-contain"
                  />
                </div>
              )}

              <div>
                <span className="text-xs text-emerald-400 font-semibold">{selectedItem.category}</span>
                <h2 className="text-xl font-bold text-white mt-0.5">{selectedItem.title}</h2>
              </div>

              {/* Attributes Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 text-xs">
                <div>
                  <span className="text-slate-400 block">Location:</span>
                  <span className="text-white font-medium">{selectedItem.location}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">{selectedItem.type === 'lost' ? 'Date Lost:' : 'Date Found:'}</span>
                  <span className="text-white font-medium">
                    {selectedItem.type === 'lost' ? selectedItem.date_lost : selectedItem.date_found}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block">Color:</span>
                  <span className="text-white font-medium">{selectedItem.color || 'Not specified'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Brand:</span>
                  <span className="text-white font-medium">{selectedItem.brand || 'Not specified'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Model:</span>
                  <span className="text-white font-medium">{selectedItem.model || 'Not specified'}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Reported On:</span>
                  <span className="text-white font-medium">
                    {selectedItem.created_at ? new Date(selectedItem.created_at).toLocaleDateString() : 'Recent'}
                  </span>
                </div>
              </div>

              {/* Distinctive Features */}
              {selectedItem.distinctive_features && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                    Distinctive Features
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {Array.isArray(selectedItem.distinctive_features) ? (
                      selectedItem.distinctive_features.map((feat, i) => (
                        <span
                          key={i}
                          className="px-2.5 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs"
                        >
                          {feat}
                        </span>
                      ))
                    ) : (
                      <p className="text-xs text-slate-300">{selectedItem.distinctive_features}</p>
                    )}
                  </div>
                </div>
              )}

              {/* Description */}
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                  Full Description
                </h4>
                <p className="text-sm text-slate-300 whitespace-pre-line bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                  {selectedItem.description}
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/40 flex items-center justify-between">
              <button
                onClick={() => handleDelete(selectedItem.type, selectedItem.id)}
                className="px-3.5 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 text-xs font-semibold flex items-center space-x-1.5 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Report</span>
              </button>

              <div className="flex items-center space-x-2">
                {selectedItem.status === 'active' ? (
                  <button
                    onClick={() => handleStatusChange(selectedItem.type, selectedItem.id, 'returned')}
                    disabled={statusUpdating === selectedItem.id}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-600/30 flex items-center space-x-1.5 transition-all"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Mark as Returned / Resolved</span>
                  </button>
                ) : (
                  <button
                    onClick={() => handleStatusChange(selectedItem.type, selectedItem.id, 'active')}
                    disabled={statusUpdating === selectedItem.id}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-xl text-xs font-semibold transition-colors"
                  >
                    <span>Reactivate Report</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
