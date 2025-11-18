'use client';

import { useState } from 'react';
import { useTryons } from '@/hooks/useTryons';
import DashboardSection from './DashboardSection';
import Image from 'next/image';
import { formatDistanceToNow } from 'date-fns';
import { ru } from 'date-fns/locale';
import type { UserTryon } from '@/lib/api';

export default function MyPhotos() {
  const { tryons, isLoading, toggleFavorite, updateTitle } = useTryons();
  const [selectedPhoto, setSelectedPhoto] = useState<UserTryon | null>(null);
  const [editingTitle, setEditingTitle] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [filterFavorites, setFilterFavorites] = useState(false);

  const filteredTryons = filterFavorites
    ? tryons?.filter((t) => t.is_favorite)
    : tryons;

  const handleToggleFavorite = async (tryonId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await toggleFavorite(tryonId);
    } catch (error) {
      console.error('Toggle favorite failed:', error);
    }
  };

  const handleStartEditTitle = (tryon: UserTryon, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingTitle(tryon.id);
    setNewTitle(tryon.title || '');
  };

  const handleSaveTitle = async (tryonId: string) => {
    try {
      await updateTitle(tryonId, newTitle);
      setEditingTitle(null);
    } catch (error) {
      console.error('Update title failed:', error);
    }
  };

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename || 'tryon-result.jpg';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(downloadUrl);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <>
      <DashboardSection
        title=">8 D>B>"
        action={
          <button
            onClick={() => setFilterFavorites(!filterFavorites)}
            className={`text-sm px-3 py-1 rounded-full transition-colors ${
              filterFavorites
                ? 'bg-primary text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {filterFavorites ? 'P 71@0==>5' : 'A5 D>B>'}
          </button>
        }
      >
        {isLoading ? (
          <div className="text-sm text-gray-500">03@C7:0...</div>
        ) : filteredTryons && filteredTryons.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {filteredTryons.map((tryon) => (
              <div
                key={tryon.id}
                className="group cursor-pointer"
                onClick={() => setSelectedPhoto(tryon)}
              >
                <div className="relative aspect-[3/4] rounded-xl overflow-hidden mb-2 bg-gray-100">
                  <Image
                    src={tryon.r2_url}
                    alt={tryon.title || '@8<5@:0'}
                    fill
                    className="object-cover group-hover:scale-105 transition-transform duration-200"
                    sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
                  />

                  {/* Favorite button */}
                  <button
                    onClick={(e) => handleToggleFavorite(tryon.id, e)}
                    className="absolute top-2 right-2 w-8 h-8 rounded-full bg-white/80 backdrop-blur-sm flex items-center justify-center hover:bg-white transition-colors"
                  >
                    <span className={tryon.is_favorite ? 'text-yellow-500' : 'text-gray-400'}>
                      {tryon.is_favorite ? 'P' : ''}
                    </span>
                  </button>
                </div>

                {/* Title */}
                {editingTitle === tryon.id ? (
                  <input
                    type="text"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    onBlur={() => handleSaveTitle(tryon.id)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSaveTitle(tryon.id);
                      if (e.key === 'Escape') setEditingTitle(null);
                    }}
                    onClick={(e) => e.stopPropagation()}
                    className="w-full text-xs px-2 py-1 border border-primary rounded"
                    autoFocus
                  />
                ) : (
                  <p
                    className="text-xs text-gray-600 truncate flex items-center gap-1"
                    onClick={(e) => handleStartEditTitle(tryon, e)}
                  >
                    {tryon.title || '57 =0720=8O'}
                    <span className="opacity-0 group-hover:opacity-100 transition-opacity"></span>
                  </p>
                )}

                <p className="text-xs text-gray-400">
                  {formatDistanceToNow(new Date(tryon.created_at), {
                    addSuffix: true,
                    locale: ru,
                  })}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">
            {filterFavorites
              ? '5B 871@0==KE D>B>3@0D89'
              : '!>7409B5 A2>N ?5@2CN 28@BC0;L=CN ?@8<5@:C!'}
          </p>
        )}
      </DashboardSection>

      {/* Photo Detail Modal */}
      {selectedPhoto && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in"
          onClick={() => setSelectedPhoto(null)}
        >
          <div
            className="glass rounded-4xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold">
                {selectedPhoto.title || '57 =0720=8O'}
              </h3>
              <button
                onClick={() => setSelectedPhoto(null)}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Image */}
            <div className="relative aspect-[3/4] rounded-2xl overflow-hidden bg-gray-100 mb-6 max-w-md mx-auto">
              <Image
                src={selectedPhoto.r2_url}
                alt={selectedPhoto.title || '@8<5@:0'}
                fill
                className="object-contain"
                priority
                sizes="(max-width: 768px) 100vw, 50vw"
              />
            </div>

            {/* Info */}
            <div className="mb-6 text-sm text-gray-600">
              <p>
                Создано:{' '}
                {formatDistanceToNow(new Date(selectedPhoto.created_at), {
                  addSuffix: true,
                  locale: ru,
                })}
              </p>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => handleDownload(selectedPhoto.r2_url, selectedPhoto.r2_key)}
                className="flex-1 btn-primary"
              >
                =� !:0G0BL
              </button>
              <button
                onClick={(e) => handleToggleFavorite(selectedPhoto.id, e)}
                className={`flex-1 ${
                  selectedPhoto.is_favorite ? 'btn-secondary' : 'btn-primary'
                }`}
              >
                {selectedPhoto.is_favorite ? 'P #1@0BL 87 871@0==>3>' : '  871@0==>5'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
