import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserPlus, Sparkles, AlertCircle } from 'lucide-react';

export const RegisterPage = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      await register({
        full_name: fullName,
        email,
        password,
        role,
      });
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register account.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-8 glass-panel p-8 rounded-2xl border border-slate-800 shadow-2xl">
        <div className="text-center">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-6 h-6 text-emerald-400" />
          </div>
          <h2 className="text-2xl font-bold text-white">Create Account</h2>
          <p className="mt-1 text-sm text-slate-400">Join the AI Lost & Found Management System</p>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Full Name
            </label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Doe"
              className="w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
              className="w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Password
            </label>
            <input
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              className="w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Account Role
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 text-sm"
            >
              <option value="user">Regular User (Report Lost/Found Items)</option>
              <option value="admin">System Administrator (Review Matches & Verification)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-3.5 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center space-x-2 text-sm mt-6"
          >
            {submitting ? (
              <span>Creating Account...</span>
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Register Account</span>
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-slate-800 text-center">
          <p className="text-xs text-slate-400">Already registered?</p>
          <Link to="/login" className="text-xs font-semibold text-emerald-400 hover:underline">
            Sign in to existing account
          </Link>
        </div>
      </div>
    </div>
  );
};
