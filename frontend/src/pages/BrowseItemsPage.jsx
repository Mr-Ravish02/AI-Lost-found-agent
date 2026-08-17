import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  Tag, 
  MapPin, 
  Calendar, 
  HelpCircle, 
  PackageSearch, 
  X, 
  RotateCcw, 
  Loader2, 
  Info, 
  Sparkles,
  PlusCircle,
  User as UserIcon
} from 'lucide-react';
import { itemService } from '../services/api';

const CATEGORIES = [
  "All Categories",
  "Electronics",
  "Wallets & Bags",
  "Keys & Badges",
  "Documents & Cards",
  "Accessories & Jewelry",
  "Clothing & Apparel",
  "Books & Stationery",
  "Sports & Equipment",
  "Other"
];

export const BrowseItemsPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Filters state
  const [itemType, setItemType] = useState(searchParams.get('type') || 'all'); // 'all', 'lost', 'found'
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [category, setCategory] = useState(searchParams.get('category') || 'All Categories');
  const [locationFilter, setLocationFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('active'); // 'active', 'all', 'returned'

  // Items state
  const [lostItems, setLostItems] = useState([]);
  const [foundItems, setFoundItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState(null);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const categoryParam = category === 'All Categories' ? undefined : category;
      const statusParam = statusFilter === 'all' ? undefined : statusFilter;
      const searchParam = searchTerm.trim() || undefined;
      const locParam = locationFilter.trim() || undefined;

      const params = {
        category: categoryParam,
        status: statusParam,
        search: searchParam,
        location: locParam,
      };

      const [lostRes, foundRes] = await Promise.all([
        itemService.getLostItems(params),
        itemService.getFoundItems(params),
      ]);

      setLostItems(lostRes || []);
      setFoundItems(foundRes || []);
    } catch (err) {
      console.error("Error fetching items:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [category, statusFilter, itemType]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchItems();
  };

  const handleResetFilters = () => {
    setItemType('all');
    setSearchTerm('');
    setCategory('All Categories');
    setLocationFilter('');
    setStatusFilter('active');
  };

  // Combine and filter items based on itemType
  const allItems = [
    ...(itemType !== 'found' ? lostItems.map((i) => ({ ...i, type: 'lost' })) : []),
    ...(itemType !== 'lost' ? foundItems.map((i) => ({ ...i, type: 'found' })) : []),
  ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header & Hero */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Public Directory & Search</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">
              Explore Lost & Found Items
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Search by title, keywords, category, brand, and location to find items.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link
              to="/report"
              className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-emerald-600/30 flex items-center space-x-2 transition-all hover:scale-[1.02]"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Report an Item</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Search & Filter Controls */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
        {/* Search Bar Form */}
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by keyword, item title, brand, serial, description..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          <button
            type="submit"
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow-md transition-all flex items-center justify-center space-x-2"
          >
            <Search className="w-4 h-4" />
            <span>Search</span>
          </button>
        </form>

        {/* Filter Badges and Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-2">
          {/* Type Switcher */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Item Type</label>
            <select
              value={itemType}
              onChange={(e) => setItemType(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-800/90 border border-slate-700 text-white text-xs font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="all">All Items (Lost + Found)</option>
              <option value="lost">Lost Items Only</option>
              <option value="found">Found Items Only</option>
            </select>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-800/90 border border-slate-700 text-white text-xs font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          {/* Location Query */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Location / Building</label>
            <input
              type="text"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') fetchItems(); }}
              placeholder="e.g. Library, Cafeteria"
              className="w-full px-3 py-2 rounded-xl bg-slate-800/90 border border-slate-700 text-white text-xs font-medium placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1 uppercase tracking-wider">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-800/90 border border-slate-700 text-white text-xs font-medium focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="active">Active Only</option>
              <option value="all">All Statuses</option>
              <option value="returned">Returned / Claimed</option>
            </select>
          </div>
        </div>

        {/* Reset button */}
        {(searchTerm || category !== 'All Categories' || locationFilter || statusFilter !== 'active' || itemType !== 'all') && (
          <div className="flex justify-end pt-1">
            <button
              onClick={handleResetFilters}
              className="text-xs text-emerald-400 hover:text-emerald-300 font-medium flex items-center space-x-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset all filters</span>
            </button>
          </div>
        )}
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between text-xs text-slate-400 px-1">
        <div>
          Showing <span className="font-semibold text-white">{allItems.length}</span> items matching criteria
        </div>
      </div>

      {/* Results Grid */}
      {loading ? (
        <div className="min-h-[300px] flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
          <p className="text-sm text-slate-400">Searching items...</p>
        </div>
      ) : allItems.length === 0 ? (
        <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center space-y-4">
          <div className="w-16 h-16 rounded-full bg-slate-800/80 flex items-center justify-center mx-auto text-emerald-400">
            <Search className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-white">No items found</h3>
          <p className="text-slate-400 text-sm max-w-md mx-auto">
            Try adjusting your search keywords, category selection, or filters to find what you're looking for.
          </p>
          <button
            onClick={handleResetFilters}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {allItems.map((item) => {
            const isLost = item.type === 'lost';
            const dateVal = isLost ? item.date_lost : item.date_found;

            return (
              <div
                key={`${item.type}-${item.id}`}
                onClick={() => setSelectedItem(item)}
                className="glass-panel rounded-2xl border border-slate-800 overflow-hidden hover:border-emerald-500/40 hover:scale-[1.01] transition-all flex flex-col cursor-pointer group"
              >
                {/* Image Banner */}
                <div className="h-48 bg-slate-950 relative overflow-hidden flex items-center justify-center border-b border-slate-800">
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
                      <span className="text-xs font-medium text-slate-500">No Photo</span>
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
                          : item.status === 'returned'
                          ? 'bg-teal-500/20 border-teal-500/40 text-teal-300'
                          : 'bg-slate-700 border-slate-600 text-slate-300'
                      }`}
                    >
                      {item.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                {/* Content */}
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

                    {/* Metadata pills */}
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {item.brand && (
                        <span className="px-2 py-0.5 rounded-md bg-slate-800 text-[11px] text-slate-300 border border-slate-700">
                          {item.brand}
                        </span>
                      )}
                      {item.color && (
                        <span className="px-2 py-0.5 rounded-md bg-slate-800 text-[11px] text-slate-300 border border-slate-700">
                          {item.color}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Footer details */}
                  <div className="space-y-1.5 text-xs text-slate-400 border-t border-slate-800 pt-3">
                    <div className="flex items-center space-x-2">
                      <MapPin className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                      <span className="truncate">{item.location}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Calendar className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                        <span>{isLost ? 'Lost: ' : 'Found: '}{dateVal}</span>
                      </div>
                      {item.user_name && (
                        <span className="text-[11px] text-slate-500 flex items-center space-x-1">
                          <UserIcon className="w-3 h-3" />
                          <span>{item.user_name}</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-2xl rounded-2xl border border-slate-800 overflow-hidden shadow-2xl animate-fade-in max-h-[90vh] flex flex-col">
            {/* Header */}
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

            {/* Content */}
            <div className="p-6 space-y-6 overflow-y-auto flex-1">
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
                  <span className="text-slate-400 block">Reported By:</span>
                  <span className="text-white font-medium">{selectedItem.user_name || 'Community Member'}</span>
                </div>
              </div>

              {/* Distinctive features */}
              {selectedItem.distinctive_features && (
                <div>
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                    Distinctive Identifiers
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

            {/* Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-900/40 flex items-center justify-end">
              <button
                onClick={() => setSelectedItem(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
