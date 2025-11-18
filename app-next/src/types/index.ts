// Пользователь
export interface User {
  id: string;
  email: string;
  name?: string;
  createdAt: string;
}

// Виртуальная примерка
export interface Tryon {
  id: string;
  userId: string;
  r2Url: string;
  r2Key: string;
  title?: string;
  isFavorite: boolean;
  createdAt: string;
}

// Статистика пользователя
export interface UserStats {
  totalTryons: number;
  favoriteCount: number;
  recentCount: number;
}

// Look (AI фильтр)
export interface Look {
  id: string;
  name: string;
  description: string;
  imageUrl: string;
  category: 'casual' | 'business' | 'party' | 'sport' | 'beach';
}

// Brand Constructor
export interface BrandStyle {
  brand: 'zara' | 'hm' | 'mango';
  name: string;
  description: string;
  colors: string[];
  patterns: string[];
}

// Style Plan
export interface StylePlan {
  id: string;
  userId: string;
  occasion: string;
  season: 'spring' | 'summer' | 'autumn' | 'winter';
  style: string;
  recommendations: string[];
  createdAt: string;
}

// Service Update
export interface ServiceUpdate {
  id: string;
  title: string;
  description: string;
  type: 'feature' | 'improvement' | 'bugfix';
  date: string;
  imageUrl?: string;
}

// API Response
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Формы
export interface LoginForm {
  email: string;
  password: string;
}

export interface RegisterForm {
  email: string;
  password: string;
  name?: string;
}

// UI состояния
export interface ModalState {
  isOpen: boolean;
  type?: 'auth' | 'tryon' | 'looks' | 'brand' | 'style';
  data?: unknown;
}
