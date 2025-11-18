'use client';

import { useState, useEffect } from 'react';
import DashboardSection from './DashboardSection';
import { useTryons } from '@/hooks/useTryons';

interface Recommendation {
  id: string;
  title: string;
  description: string;
  icon: string;
  category: 'trend' | 'personal' | 'season' | 'occasion';
}

export default function Recommendations() {
  const { tryons } = useTryons();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  useEffect(() => {
    // 5=5@8@C5< AI-@5:><5=40F88 =0 >A=>25 8AB>@88 ?>;L7>20B5;O
    const generateRecommendations = () => {
      const recs: Recommendation[] = [];

      // 07>2K5 @5:><5=40F88
      const baseRecommendations: Recommendation[] = [
        {
          id: '1',
          title: '>4=K9 B@5=4: 25@A097',
          description: '!2>1>4=K9 :@>9 2 <>45! >?@>1C9B5 >25@A097-?8460: 8;8 EC48',
          icon: '=%',
          category: 'trend',
        },
        {
          id: '2',
          title: '8<=OO :>;;5:F8O',
          description: '>102LB5 B5?;>BK 2 30@45@>1: ?0;LB>, A28B5@0 8 CNB=K5 :0@4830=K',
          icon: 'D',
          category: 'season',
        },
        {
          id: '3',
          title: '5;>2>9 AB8;L',
          description: '>B>2LB5AL : 206=K< 2AB@5G0<: :;0AA8G5A:85 :>ABN<K 8 @C10H:8',
          icon: '=�',
          category: 'occasion',
        },
        {
          id: '4',
          title: 'Casual >1@07K',
          description: ';O ?>2A54=52=>9 687=8: 468=AK, DCB1>;:8 8 comfortable >1C2L',
          icon: '=U',
          category: 'personal',
        },
        {
          id: '5',
          title: '5G5@=89 AB8;L',
          description: '-;530=B=K5 ?;0BLO 8 :>ABN<K 4;O >A>1KE A;CG052',
          icon: '(',
          category: 'occasion',
        },
        {
          id: '6',
          title: '!?>@B82=K9 H8:',
          description: 'Athleisure B@5=4: A>G5B09B5 :><D>@B 8 AB8;L',
          icon: '<�',
          category: 'trend',
        },
      ];

      // A;8 C ?>;L7>20B5;O 5ABL ?@8<5@:8, ?5@A>=0;878@C5< @5:><5=40F88
      if (tryons && tryons.length > 0) {
        recs.push({
          id: 'personal-1',
          title: 'AE>4O 87 20H53> AB8;O',
          description: `# 20A ${tryons.length} ?@8<5@>:! >?@>1C9B5 ?>E>685 >1@07K 2 4@C38E F25B0E`,
          icon: '<�',
          category: 'personal',
        });

        // A;8 5ABL 871@0==K5
        const favorites = tryons.filter((t) => t.is_favorite);
        if (favorites.length > 0) {
          recs.push({
            id: 'personal-2',
            title: '>?>;=8B5 ;N18<K5 >1@07K',
            description: '0948B5 0:A5AAC0@K 8 >1C2L : 20H8< 871@0==K< =0@O40<',
            icon: 'P',
            category: 'personal',
          });
        }
      }

      // >102;O5< 107>2K5 @5:><5=40F88
      recs.push(...baseRecommendations.slice(0, 4 - recs.length));

      setRecommendations(recs);
    };

    generateRecommendations();
  }, [tryons]);

  const categoryColors = {
    trend: 'bg-gradient-to-br from-pink-50 to-purple-50 border-pink-200',
    personal: 'bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200',
    season: 'bg-gradient-to-br from-cyan-50 to-blue-50 border-cyan-200',
    occasion: 'bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200',
  };

  return (
    <DashboardSection title=" 5:><5=40F88 4;O 20A">
      <div className="space-y-3">
        {recommendations.map((rec) => (
          <div
            key={rec.id}
            className={`p-4 rounded-xl border-2 ${categoryColors[rec.category]} hover:scale-102 transition-transform cursor-pointer`}
          >
            <div className="flex items-start gap-3">
              <div className="text-2xl flex-shrink-0">{rec.icon}</div>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-sm mb-1">{rec.title}</h4>
                <p className="text-xs text-gray-600 line-clamp-2">{rec.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 text-center">
        <p className="text-xs text-gray-500">
          💡 Рекомендации обновляются на основе ваших примерок
        </p>
      </div>
    </DashboardSection>
  );
}
