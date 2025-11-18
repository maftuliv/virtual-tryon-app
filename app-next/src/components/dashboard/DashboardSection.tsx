'use client';

import { ReactNode } from 'react';

interface DashboardSectionProps {
  title: string;
  children: ReactNode;
  variant?: 'default' | 'strong';
  className?: string;
  action?: ReactNode;
}

export default function DashboardSection({
  title,
  children,
  variant = 'default',
  className = '',
  action,
}: DashboardSectionProps) {
  return (
    <div
      className={`
        ${variant === 'strong' ? 'glass-strong' : 'glass glass-hover'}
        p-6 rounded-4xl
        ${className}
      `}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">{title}</h3>
        {action && <div>{action}</div>}
      </div>
      {children}
    </div>
  );
}
