'use client';

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
  tip?: string;
}

export default function LoadingOverlay({
  isVisible,
  message = 'Загрузка...',
  tip,
}: LoadingOverlayProps) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="glass rounded-4xl p-8 max-w-md mx-4 text-center">
        {/* Spinner */}
        <div className="flex justify-center mb-6">
          <div className="relative w-16 h-16">
            <div className="absolute inset-0 border-4 border-primary/20 rounded-full" />
            <div className="absolute inset-0 border-4 border-transparent border-t-primary rounded-full animate-spin" />
          </div>
        </div>

        {/* Message */}
        <h3
          className="text-xl font-semibold mb-2"
          dangerouslySetInnerHTML={{ __html: message }}
        />

        {/* Tip */}
        {tip && (
          <p className="text-sm text-gray-600 mt-4">{tip}</p>
        )}

        {/* Progress hint */}
        <p className="text-xs text-gray-500 mt-6">
          Это может занять 10-30 секунд. Пожалуйста, не закрывайте страницу.
        </p>
      </div>
    </div>
  );
}
