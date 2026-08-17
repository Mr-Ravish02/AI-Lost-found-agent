import axios from 'axios';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach Auth JWT Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor to handle global errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

export const itemService = {
  // Image Upload
  uploadImage: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/items/upload-image', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Lost Items
  reportLostItem: async (data) => {
    const response = await api.post('/items/lost', data);
    return response.data;
  },
  getLostItems: async (params = {}) => {
    const response = await api.get('/items/lost', { params });
    return response.data;
  },
  getLostItemById: async (id) => {
    const response = await api.get(`/items/lost/${id}`);
    return response.data;
  },
  updateLostItemStatus: async (id, status) => {
    const response = await api.patch(`/items/lost/${id}/status`, { status });
    return response.data;
  },
  deleteLostItem: async (id) => {
    const response = await api.delete(`/items/lost/${id}`);
    return response.data;
  },

  // Found Items
  reportFoundItem: async (data) => {
    const response = await api.post('/items/found', data);
    return response.data;
  },
  getFoundItems: async (params = {}) => {
    const response = await api.get('/items/found', { params });
    return response.data;
  },
  getFoundItemById: async (id) => {
    const response = await api.get(`/items/found/${id}`);
    return response.data;
  },
  updateFoundItemStatus: async (id, status) => {
    const response = await api.patch(`/items/found/${id}/status`, { status });
    return response.data;
  },
  deleteFoundItem: async (id) => {
    const response = await api.delete(`/items/found/${id}`);
    return response.data;
  },

  // User Reports & Stats
  getMyReports: async () => {
    const response = await api.get('/items/my-reports');
    return response.data;
  },
  getStats: async () => {
    const response = await api.get('/items/stats');
    return response.data;
  },
};

export const workflowService = {
  triggerWorkflowForLostItem: async (lostItemId) => {
    const response = await api.post(`/ai/workflow/lost/${lostItemId}`);
    return response.data;
  },
  submitVerification: async (lostItemId, answers) => {
    const response = await api.post(`/ai/workflow/lost/${lostItemId}/verify`, { answers });
    return response.data;
  },
};

export const verificationService = {
  getMatchVerification: async (matchId) => {
    const response = await api.get(`/ai/verification/${matchId}`);
    return response.data;
  },
  generateQuestions: async (matchId) => {
    const response = await api.post(`/ai/verification/${matchId}/generate`);
    return response.data;
  },
  submitAnswers: async (matchId, answers) => {
    const response = await api.post(`/ai/verification/${matchId}/answers`, { answers });
    return response.data;
  },
};

export const adminService = {
  getStats: async () => {
    const response = await api.get('/admin/dashboard/stats');
    return response.data;
  },
  getPendingMatches: async () => {
    const response = await api.get('/admin/matches/pending');
    return response.data;
  },
  getMatchDetail: async (matchId) => {
    const response = await api.get(`/admin/matches/${matchId}`);
    return response.data;
  },
  approveMatch: async (matchId, payload = {}) => {
    const response = await api.post(`/admin/matches/${matchId}/approve`, payload);
    return response.data;
  },
  rejectMatch: async (matchId, payload = {}) => {
    const response = await api.post(`/admin/matches/${matchId}/reject`, payload);
    return response.data;
  },
  requestMoreInfo: async (matchId, payload = {}) => {
    const response = await api.post(`/admin/matches/${matchId}/request-info`, payload);
    return response.data;
  },
};

export const notificationService = {
  getNotifications: async () => {
    const response = await api.get('/notifications');
    return response.data;
  },
  markAsRead: async (id) => {
    const response = await api.patch(`/notifications/${id}/read`);
    return response.data;
  },
  markAllAsRead: async () => {
    const response = await api.post('/notifications/mark-all-read');
    return response.data;
  },
};

export const healthService = {
  checkHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
