import { useEffect, useState } from 'react';
import { useAuth } from './useAuth';

interface LimitData {
  can_generate: boolean;
  used: number;
  limit: number;
  period: 'week' | 'month' | 'unlimited';
}

export function useLimit() {
  const { isAuthenticated } = useAuth();
  const [limitData, setLimitData] = useState<LimitData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchLimit = async () => {
    if (!isAuthenticated) {
      setLimitData(null);
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('auth_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

      const response = await fetch(`${apiUrl}/api/auth/check-limit`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();

        // Определяем период based on limit
        let period: 'week' | 'month' | 'unlimited' = 'week';
        if (data.limit === -1) {
          period = 'unlimited';
        } else if (data.limit === 50) {
          period = 'month';
        } else if (data.limit === 3) {
          period = 'week';
        }

        setLimitData({
          can_generate: data.can_generate,
          used: data.used,
          limit: data.limit,
          period,
        });
      }
    } catch (error) {
      console.error('Error fetching limit:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLimit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  return {
    limitData,
    loading,
    refetch: fetchLimit,
  };
}
