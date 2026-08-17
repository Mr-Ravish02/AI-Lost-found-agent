import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Sparkles, 
  MapPin, 
  Calendar, 
  Tag, 
  Palette, 
  FileText, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ArrowLeft,
  HelpCircle,
  PackageSearch,
  Check
} from 'lucide-react';
import { ImageUpload } from '../components/ImageUpload';
import { itemService } from '../services/api';

const CATEGORIES = [
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

export const ReportItemPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  // Type: 'lost' or 'found'
  const initialType = searchParams.get('type') === 'found' ? 'found' : 'lost';
  const [itemType, setItemType] = useState(initialType);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    category: 'Electronics',
    description: '',
    location: '',
    date: new Date().toISOString().split('T')[0],
    color: '',
    brand: '',
    model: '',
    distinctiveFeaturesInput: '',
    imageUrl: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [createdItemId, setCreatedItemId] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    // Split features by comma or newline
    const features = formData.distinctiveFeaturesInput
      .split(/[,\n]/)
      .map((f) => f.trim())
      .filter(Boolean);

    try {
      let result;
      if (itemType === 'lost') {
        const payload = {
          title: formData.title.trim(),
          category: formData.category,
          description: formData.description.trim(),
          location: formData.location.trim(),
          date_lost: formData.date,
          color: formData.color.trim() || null,
          brand: formData.brand.trim() || null,
          model: formData.model.trim() || null,
          distinctive_features: features.length > 0 ? features : null,
          image_url: formData.imageUrl || null,
        };
        result = await itemService.reportLostItem(payload);
      } else {
        const payload = {
          title: formData.title.trim(),
          category: formData.category,
          description: formData.description.trim(),
          location: formData.location.trim(),
          date_found: formData.date,
          color: formData.color.trim() || null,
          brand: formData.brand.trim() || null,
          model: formData.model.trim() || null,
          distinctive_features: features.length > 0 ? features : null,
          image_url: formData.imageUrl || null,
        };
        result = await itemService.reportFoundItem(payload);
      }

      setCreatedItemId(result.id);
      setSuccess(true);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Failed to submit report. Please check required fields.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16">
        <div className="glass-panel p-8 rounded-2xl border border-slate-800 text-center space-y-6 animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center mx-auto text-emerald-400">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">
              {itemType === 'lost' ? 'Lost Item Reported Successfully!' : 'Found Item Reported Successfully!'}
            </h2>
            <p className="text-slate-400 text-sm max-w-md mx-auto">
              Your report is now live in the system (Report #{createdItemId}). Our automated matching engine will analyze potential matches.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="w-full sm:w-auto px-6 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold rounded-xl shadow-lg shadow-emerald-600/30 transition-all"
            >
              Go to My Dashboard
            </button>
            <button
              onClick={() => navigate('/browse')}
              className="w-full sm:w-auto px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium rounded-xl border border-slate-700 transition-all"
            >
              Browse All Items
            </button>
            <button
              onClick={() => {
                setSuccess(false);
                setFormData({
                  title: '',
                  category: 'Electronics',
                  description: '',
                  location: '',
                  date: new Date().toISOString().split('T')[0],
                  color: '',
                  brand: '',
                  model: '',
                  distinctiveFeaturesInput: '',
                  imageUrl: '',
                });
              }}
              className="w-full sm:w-auto px-4 py-2.5 text-slate-400 hover:text-slate-200 text-sm font-medium transition-colors"
            >
              Submit Another Report
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center space-x-2 text-sm text-slate-400 hover:text-slate-200 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back</span>
      </button>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">
          Report an Item
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Provide accurate details to help our smart system identify and match items effectively.
        </p>
      </div>

      {/* Item Type Switcher Tabs */}
      <div className="grid grid-cols-2 gap-3 p-1.5 rounded-2xl bg-slate-800/80 border border-slate-700/80 mb-8">
        <button
          type="button"
          onClick={() => setItemType('lost')}
          className={`py-3 px-4 rounded-xl text-sm font-semibold flex items-center justify-center space-x-2 transition-all ${
            itemType === 'lost'
              ? 'bg-gradient-to-r from-rose-600 to-rose-500 text-white shadow-lg shadow-rose-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
          }`}
        >
          <HelpCircle className="w-4 h-4" />
          <span>I Lost Something</span>
        </button>

        <button
          type="button"
          onClick={() => setItemType('found')}
          className={`py-3 px-4 rounded-xl text-sm font-semibold flex items-center justify-center space-x-2 transition-all ${
            itemType === 'found'
              ? 'bg-gradient-to-r from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-600/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'
          }`}
        >
          <PackageSearch className="w-4 h-4" />
          <span>I Found Something</span>
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Report Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>Basic Information</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">Core details identifying the item</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Title */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Item Title <span className="text-rose-400">*</span>
              </label>
              <input
                type="text"
                name="title"
                required
                value={formData.title}
                onChange={handleChange}
                placeholder={itemType === 'lost' ? "e.g., Apple iPhone 14 Pro in Black Case" : "e.g., Found Silver Dell Laptop"}
                className="w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
              />
            </div>

            {/* Category */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Category <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Date Lost / Found */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                {itemType === 'lost' ? 'Date Lost' : 'Date Found'} <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <input
                  type="date"
                  name="date"
                  required
                  value={formData.date}
                  onChange={handleChange}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
                />
              </div>
            </div>

            {/* Location */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-slate-300 mb-1">
                {itemType === 'lost' ? 'Last Known Location' : 'Location Found'} <span className="text-rose-400">*</span>
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <MapPin className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  name="location"
                  required
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="e.g., Computer Lab 304, Desk #12 or Cafeteria Near Vending Machine"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all text-sm"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Item Specifications & Attributes */}
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800 space-y-6">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-teal-500" />
              <span>Attributes & Distinctive Features</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">Specific characteristics used for AI and similarity scoring</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Color */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Color</label>
              <input
                type="text"
                name="color"
                value={formData.color}
                onChange={handleChange}
                placeholder="e.g., Emerald Green, Space Gray"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Brand */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Brand / Maker</label>
              <input
                type="text"
                name="brand"
                value={formData.brand}
                onChange={handleChange}
                placeholder="e.g., Sony, Apple, Nike"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>

            {/* Model */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Model / Serial</label>
              <input
                type="text"
                name="model"
                value={formData.model}
                onChange={handleChange}
                placeholder="e.g., WH-1000XM4"
                className="w-full px-3.5 py-2 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Distinctive Features */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Distinctive Features / Identifiers
            </label>
            <textarea
              name="distinctiveFeaturesInput"
              rows={2}
              value={formData.distinctiveFeaturesInput}
              onChange={handleChange}
              placeholder="e.g., Yellow anime sticker on top lid, scratch near USB-C port, blue keychain ring"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">Separate features by commas or new lines.</p>
          </div>

          {/* Detailed Description */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Detailed Description <span className="text-rose-400">*</span>
            </label>
            <textarea
              name="description"
              required
              rows={4}
              value={formData.description}
              onChange={handleChange}
              placeholder="Provide as much detail as possible: circumstances, contents if bag/wallet, stickers, engraving, or condition..."
              className="w-full px-4 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Photo Upload */}
        <div className="glass-panel p-6 sm:p-8 rounded-2xl border border-slate-800">
          <div className="border-b border-slate-800 pb-4 mb-6">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
              <span>Photo Upload</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">Upload a clear photo of the item if available</p>
          </div>

          <ImageUpload
            value={formData.imageUrl}
            onChange={(url) => setFormData((prev) => ({ ...prev, imageUrl: url }))}
            label={itemType === 'lost' ? "Photo of Lost Item (or similar reference)" : "Photo of Found Item"}
          />
        </div>

        {/* Submit Actions */}
        <div className="flex items-center justify-end space-x-4 pt-2">
          <button
            type="button"
            onClick={() => navigate(-1)}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-slate-800 text-sm font-medium transition-colors"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={loading}
            className={`px-6 py-2.5 rounded-xl text-sm font-semibold text-white shadow-lg transition-all flex items-center space-x-2 ${
              itemType === 'lost'
                ? 'bg-rose-600 hover:bg-rose-500 shadow-rose-600/30'
                : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/30'
            } ${loading ? 'opacity-70 cursor-not-allowed' : 'hover:scale-[1.02]'}`}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Submitting Report...</span>
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                <span>Submit {itemType === 'lost' ? 'Lost Item Report' : 'Found Item Report'}</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
