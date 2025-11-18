import { create } from 'zustand';

interface TryonState {
  personImage: File | null;
  garmentImage: File | null;
  personImagePreview: string | null;
  garmentImagePreview: string | null;
  isGenerating: boolean;
  resultImage: string | null;

  // Actions
  setPersonImage: (file: File | null, preview: string | null) => void;
  setGarmentImage: (file: File | null, preview: string | null) => void;
  setIsGenerating: (generating: boolean) => void;
  setResultImage: (url: string | null) => void;
  reset: () => void;
}

export const useTryonStore = create<TryonState>((set) => ({
  personImage: null,
  garmentImage: null,
  personImagePreview: null,
  garmentImagePreview: null,
  isGenerating: false,
  resultImage: null,

  setPersonImage: (file, preview) =>
    set({ personImage: file, personImagePreview: preview }),

  setGarmentImage: (file, preview) =>
    set({ garmentImage: file, garmentImagePreview: preview }),

  setIsGenerating: (generating) =>
    set({ isGenerating: generating }),

  setResultImage: (url) =>
    set({ resultImage: url }),

  reset: () =>
    set({
      personImage: null,
      garmentImage: null,
      personImagePreview: null,
      garmentImagePreview: null,
      isGenerating: false,
      resultImage: null,
    }),
}));
