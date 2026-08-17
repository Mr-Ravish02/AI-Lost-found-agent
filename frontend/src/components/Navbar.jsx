import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { notificationService } from '../services/api';
import { 
  Sparkles, 
  Shield, 
  LogOut, 
  User as UserIcon, 
  PlusCircle, 
  Search, 
  LayoutDashboard,
  Bell,
  CheckCheck,
  ExternalLink,
  X
} from 'lucide-react';

export const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const notifRef = useRef(null);

  const fetchNotifications = async () => {
    if (!user) return;
    try {
      const data = await notificationService.getNotifications();
      setNotifications(data);
    } catch (err) {
      // Silently fail for background notification fetch
    }
  };

  useEffect(() => {
    if (user) {
      fetchNotifications();
      const interval = setInterval(fetchNotifications, 15000);
      return () => clearInterval(interval);
    }
  }, [user]);

  // Close dropdown when clicked outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (notifRef.current && !notifRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkAsRead = async (notif) => {
    if (!notif.is_read) {
      try {
        await notificationService.markAsRead(notif.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
      } catch (err) {
        console.error(err);
      }
    }
    if (notif.link) {
      setShowNotifications(false);
      navigate(notif.link);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <nav className="sticky top-0 z-50 glass-panel border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Branding */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 via-teal-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/25 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold bg-gradient-to-r from-white via-slate-100 to-emerald-200 bg-clip-text text-transparent">
                AI Lost & Found
              </span>
              <span className="hidden sm:block text-[10px] uppercase tracking-wider font-semibold text-emerald-400">
                Smart Agentic System
              </span>
            </div>
          </Link>

          {/* Nav Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            <Link
              to="/"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive('/') ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              Home
            </Link>

            <Link
              to="/browse"
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                isActive('/browse') ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Search className="w-4 h-4" />
              <span>Browse Items</span>
            </Link>

            {user && (
              <>
                <Link
                  to="/dashboard"
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                    isActive('/dashboard') ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>

                <Link
                  to="/report"
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                    isActive('/report') ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <PlusCircle className="w-4 h-4" />
                  <span>Report Item</span>
                </Link>

                {user.role === 'admin' && (
                  <Link
                    to="/admin"
                    className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                      isActive('/admin') ? 'bg-teal-500/20 text-teal-300 border border-teal-500/30' : 'text-teal-400 hover:bg-teal-900/30'
                    }`}
                  >
                    <Shield className="w-4 h-4" />
                    <span>Admin Review</span>
                  </Link>
                )}
              </>
            )}
          </div>

          {/* Right Actions */}
          <div className="flex items-center space-x-3">
            {user ? (
              <div className="flex items-center space-x-3">
                {/* Notifications Bell */}
                <div className="relative" ref={notifRef}>
                  <button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors relative"
                    title="Notifications"
                  >
                    <Bell className="w-5 h-5" />
                    {unreadCount > 0 && (
                      <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white rounded-full text-[10px] font-bold flex items-center justify-center animate-pulse">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </span>
                    )}
                  </button>

                  {/* Dropdown Menu */}
                  {showNotifications && (
                    <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl glass-panel border border-slate-700 shadow-2xl p-4 space-y-3 z-50 animate-fade-in">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                        <div className="flex items-center space-x-2">
                          <Bell className="w-4 h-4 text-emerald-400" />
                          <span className="text-xs font-bold text-white uppercase tracking-wider">
                            Notifications
                          </span>
                          {unreadCount > 0 && (
                            <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">
                              {unreadCount} new
                            </span>
                          )}
                        </div>
                        {unreadCount > 0 && (
                          <button
                            onClick={handleMarkAllRead}
                            className="text-[11px] text-slate-400 hover:text-emerald-300 flex items-center space-x-1"
                          >
                            <CheckCheck className="w-3 h-3" />
                            <span>Mark all read</span>
                          </button>
                        )}
                      </div>

                      <div className="max-h-72 overflow-y-auto space-y-2">
                        {notifications.length === 0 ? (
                          <p className="text-xs text-slate-400 text-center py-6">No notifications yet.</p>
                        ) : (
                          notifications.map((notif) => (
                            <div
                              key={notif.id}
                              onClick={() => handleMarkAsRead(notif)}
                              className={`p-3 rounded-xl cursor-pointer transition-all border ${
                                !notif.is_read
                                  ? 'bg-emerald-950/40 border-emerald-500/30 text-white'
                                  : 'bg-slate-900/40 border-slate-800 text-slate-300 hover:bg-slate-800/60'
                              }`}
                            >
                              <div className="flex items-start justify-between gap-2">
                                <h5 className="text-xs font-bold text-white">{notif.title}</h5>
                                {!notif.is_read && (
                                  <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0 mt-1" />
                                )}
                              </div>
                              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">
                                {notif.message}
                              </p>
                              <span className="text-[9px] text-slate-500 block mt-1.5">
                                {notif.created_at ? new Date(notif.created_at).toLocaleString() : 'Just now'}
                              </span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  )}
                </div>

                <Link
                  to="/report"
                  className="hidden sm:flex items-center space-x-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg shadow-md shadow-emerald-600/25 transition-all hover:scale-[1.02]"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>Report Item</span>
                </Link>

                <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700">
                  <UserIcon className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-medium text-slate-200">{user.full_name}</span>
                  {user.role === 'admin' && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-teal-500/20 text-teal-300 font-semibold border border-teal-500/30">
                      Admin
                    </span>
                  )}
                </div>

                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
                >
                  Log In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg shadow-lg shadow-emerald-600/25 transition-all hover:scale-[1.02]"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

        </div>
      </div>
    </nav>
  );
};
