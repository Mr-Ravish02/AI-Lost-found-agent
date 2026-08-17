import React, { useState, useRef } from 'react';
import { UploadCloud, X, Image as ImageIcon, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { itemService } from '../services/api';

export const ImageUpload = ({ value, onChange, label = "Upload Item Photo" }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;

    // Validate type
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'];
    if (!validTypes.includes(file.type.toLowerCase())) {
      setError('Please upload a valid image file (JPG, PNG, WEBP, GIF).');
      return;
    }

    // Validate size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image size must be less than 10MB.');
      return;
    }

    setError(null);
    setUploading(true);

    try {
      const data = await itemService.uploadImage(file);
      onChange(data.image_url);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to upload image. Please try again.';
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleRemove = (e) => {
    e.stopPropagation();
    onChange('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-300">
        {label} <span className="text-xs text-slate-500 font-normal">(Optional, helps AI identification)</span>
      </label>

      {value ? (
        <div className="relative group rounded-xl border border-slate-700 bg-slate-800/60 overflow-hidden p-3 flex items-center space-x-4">
          <div className="w-20 h-20 rounded-lg overflow-hidden bg-slate-900 border border-slate-700 flex-shrink-0 flex items-center justify-center">
            <img
              src={value}
              alt="Uploaded item"
              className="w-full h-full object-cover"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://placehold.co/100x100/1e293b/94a3b8?text=Image';
              }}
            />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-1.5 text-emerald-400 text-xs font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
              <span>Image uploaded successfully</span>
            </div>
            <p className="text-xs text-slate-400 truncate mt-1">{value}</p>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="text-xs text-emerald-400 hover:text-emerald-300 font-medium mt-1 inline-block"
            >
              Replace image
            </button>
          </div>
          <button
            type="button"
            onClick={handleRemove}
            className="p-2 rounded-lg bg-slate-800 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
            title="Remove photo"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
            dragOver
              ? 'border-emerald-500 bg-emerald-500/10'
              : 'border-slate-700 hover:border-emerald-500/50 bg-slate-800/40 hover:bg-slate-800/60'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png, image/jpeg, image/jpg, image/webp, image/gif"
            className="hidden"
            onChange={handleFileChange}
            disabled={uploading}
          />
          {uploading ? (
            <div className="flex flex-col items-center justify-center space-y-2 py-2">
              <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
              <p className="text-sm font-medium text-slate-300">Uploading and processing image...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-2">
              <div className="w-10 h-10 rounded-full bg-slate-700/60 flex items-center justify-center text-emerald-400">
                <UploadCloud className="w-5 h-5" />
              </div>
              <div className="text-sm">
                <span className="text-emerald-400 font-semibold hover:underline">Click to browse</span> or drag and drop photo here
              </div>
              <p className="text-xs text-slate-500">PNG, JPG, WEBP or GIF up to 10MB</p>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="flex items-center space-x-1.5 text-xs text-rose-400 mt-1">
          <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
