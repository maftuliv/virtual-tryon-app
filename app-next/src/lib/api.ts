import ky from 'ky';

// Базовый клиент для API запросов
const api = ky.create({
  prefixUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
  timeout: 120000, // 2 минуты для генерации
  retry: {
    limit: 2,
    methods: ['get'],
    statusCodes: [408, 413, 429, 500, 502, 503, 504],
  },
  hooks: {
    beforeRequest: [
      (request) => {
        // Добавляем токен авторизации из localStorage
        if (typeof window !== 'undefined') {
          const authData = localStorage.getItem('auth-storage');
          if (authData) {
            try {
              const { state } = JSON.parse(authData);
              if (state?.token) {
                request.headers.set('Authorization', `Bearer ${state.token}`);
              }
            } catch (error) {
              console.error('Failed to parse auth token:', error);
            }
          }
        }
      },
    ],
    beforeError: [
      (error) => {
        const { response } = error;
        if (response) {
          error.name = 'APIError';
          error.message = `${response.status}: ${response.statusText}`;
        }
        return error;
      },
    ],
  },
});

export default api;

// Типы для API
export interface UploadRequest {
  personImages: File[];
  garmentImage: File;
}

export interface UploadResponse {
  success: boolean;
  person_images: string[];  // paths
  garment_image: string;     // path
  session_id: string;
}

export interface TryonRequest {
  person_images: string[];   // paths from upload
  garment_image: string;     // path from upload
  garment_category?: string;
  device_fingerprint?: string;
}

export interface TryonResult {
  original: string;
  result_path: string;
  result_image: string;  // base64
  result_url: string;
  result_filename: string;
}

export interface TryonResponse {
  success: boolean;
  results: TryonResult[];
  daily_limit?: {
    can_generate: boolean;
    used: number;
    remaining: number;
    limit: number;
  };
  anonymous_limit?: {
    used: number;
    remaining: number;
    limit: number;
  };
}

export interface UserTryon {
  id: string;
  user_id: string;
  r2_url: string;
  r2_key: string;
  title?: string;
  is_favorite: boolean;
  created_at: string;
}

export interface UserStats {
  total_tryons: number;
  favorite_count: number;
  recent_count: number;
}

// API функции
export const tryonApi = {
  // Шаг 1: Загрузка файлов
  async upload(data: UploadRequest): Promise<UploadResponse> {
    const formData = new FormData();

    // Добавляем person images (может быть несколько)
    data.personImages.forEach(file => {
      formData.append('person_images', file);
    });

    // Добавляем garment image
    formData.append('garment_image', data.garmentImage);

    return api.post('api/upload', { body: formData }).json();
  },

  // Шаг 2: Генерация виртуальной примерки
  async generate(data: TryonRequest): Promise<TryonResponse> {
    return api.post('api/tryon', {
      json: data,
    }).json();
  },

  // Получить историю примерок пользователя
  async getUserTryons(): Promise<UserTryon[]> {
    const response = await api.get('api/user/tryons').json<{
      success: boolean;
      tryons: UserTryon[];
      total: number;
      limit: number;
      offset: number;
      has_more: boolean;
    }>();
    return response.tryons || [];
  },

  // Получить статистику пользователя
  async getUserStats(): Promise<UserStats> {
    return api.get('api/user/tryons/stats').json();
  },

  // Переключить избранное
  async toggleFavorite(tryonId: string): Promise<void> {
    await api.post(`api/user/tryons/${tryonId}/favorite`);
  },

  // Обновить название
  async updateTitle(tryonId: string, title: string): Promise<void> {
    await api.put(`api/user/tryons/${tryonId}/title`, {
      json: { title },
    });
  },
};

export interface AuthResponse {
  user: {
    id: number;
    email: string;
    full_name?: string;
    avatar_url?: string;
    role: string;
    provider: string;
    is_premium: boolean;
    premium_until?: string | null;
    created_at: string;
  };
  token: string;
}

export const authApi = {
  // Регистрация
  async register(email: string, password: string, name?: string): Promise<AuthResponse> {
    return api.post('api/auth/register', {
      json: { email, password, name },
    }).json();
  },

  // Вход
  async login(email: string, password: string): Promise<AuthResponse> {
    return api.post('api/auth/login', {
      json: { email, password },
    }).json();
  },

  // Выход
  async logout() {
    return api.post('api/auth/logout').json();
  },

  // Получить текущего пользователя
  async getCurrentUser() {
    return api.get('api/auth/me').json();
  },

  // Получить данные пользователя по токену (для Google OAuth)
  async me(token: string) {
    return api.get('api/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).json();
  },
};
