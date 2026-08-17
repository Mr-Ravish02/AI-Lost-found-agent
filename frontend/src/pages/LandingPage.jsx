import React from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, Brain, Cpu, ShieldCheck, ArrowRight, Search, FileText, CheckCircle2, MessageSquare, Award } from 'lucide-react';

export const LandingPage = () => {
  return (
    <div className="space-y-24 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-12 lg:pt-20">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/3 right-10 w-[300px] h-[300px] bg-teal-500/15 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold uppercase tracking-wider mb-6">
            <Sparkles className="w-4 h-4 text-emerald-400" />
            <span>Agentic AI Powered CSE Final Year Project</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight max-w-4xl mx-auto">
            AI-Powered Smart <br />
            <span className="bg-gradient-to-r from-emerald-400 via-teal-200 to-cyan-400 bg-clip-text text-transparent glow-text">
              Lost & Found Management System
            </span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed font-normal">
            Reconnecting lost items with their rightful owners using multi-agentic AI intelligence: natural language extraction, semantic vector matching, verification agent prompts, and admin-in-the-loop review.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/register"
              className="w-full sm:w-auto px-8 py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-xl shadow-xl shadow-emerald-600/30 transition-all hover:scale-105 flex items-center justify-center space-x-2"
            >
              <span>Get Started Now</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/login"
              className="w-full sm:w-auto px-8 py-3.5 glass-card text-slate-200 hover:text-white font-semibold rounded-xl border border-slate-700 hover:border-slate-600 transition-all flex items-center justify-center"
            >
              Log In to Dashboard
            </Link>
          </div>

          {/* Quick Stats Banner */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            {[
              { label: 'Information Extraction', val: 'Groq / WatsonX LLM' },
              { label: 'Semantic Matching', val: 'Vector Cosine AI' },
              { label: 'Human-in-the-Loop', val: 'Admin Verification' },
              { label: 'Agentic Framework', val: 'LangGraph & LangChain' },
            ].map((stat, idx) => (
              <div key={idx} className="p-4 rounded-xl glass-card border border-slate-800 text-center">
                <p className="text-xs text-emerald-400 uppercase tracking-wider font-semibold">{stat.label}</p>
                <p className="text-sm font-bold text-slate-100 mt-1">{stat.val}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Multi-Agent Architecture */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-4xl font-bold text-white">
            Powered by Autonomous Agentic AI
          </h2>
          <p className="text-slate-400 mt-2">
            Five specialized agents work together to ensure maximum accuracy and zero false claims.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              icon: Brain,
              color: 'from-emerald-600 to-teal-500',
              title: '1. Extraction Agent',
              desc: 'Parses unstructured text descriptions to auto-extract structured tags like category, color, brand, model, location, and distinctive features.',
            },
            {
              icon: Cpu,
              color: 'from-teal-600 to-cyan-500',
              title: '2. Matching Agent',
              desc: 'Generates text embeddings and evaluates multi-factor cosine similarity across category, color, brand, location, and date to calculate match score (0-100%).',
            },
            {
              icon: ShieldCheck,
              color: 'from-emerald-500 to-teal-700',
              title: '3. Verification Agent',
              desc: 'Generates non-revealing ownership verification questions about private details and evaluates user answers to recommend approval.',
            },
          ].map((agent, idx) => (
            <div key={idx} className="glass-card p-6 rounded-2xl border border-slate-800 flex flex-col justify-between">
              <div>
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${agent.color} flex items-center justify-center mb-4 shadow-lg shadow-teal-500/20`}>
                  <agent.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-2">{agent.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{agent.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* System Workflow */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 bg-slate-800/40 rounded-3xl p-8 sm:p-12 border border-slate-800">
        <div className="text-center mb-10">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">How the System Works</h2>
          <p className="text-slate-400 text-sm mt-1">End-to-end workflow from report submission to item handover</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { step: '01', title: 'Submit Report', text: 'Report lost or found item with text description and image.' },
            { step: '02', title: 'AI Matching', text: 'Agents extract tags and calculate semantic match scores.' },
            { step: '03', title: 'Verification', text: 'Claimant answers AI questions about private features.' },
            { step: '04', title: 'Admin Approval', text: 'Admin reviews evidence score & approves item return.' },
          ].map((s, idx) => (
            <div key={idx} className="relative p-5 glass-panel rounded-xl border border-slate-700/50">
              <span className="text-3xl font-extrabold text-emerald-400/30">{s.step}</span>
              <h4 className="text-lg font-bold text-white mt-2">{s.title}</h4>
              <p className="text-xs text-slate-400 mt-1 leading-relaxed">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
};
