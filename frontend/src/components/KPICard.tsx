import React from 'react';
import '../styles/KPICard.css';

interface KPICardProps {
  title: string;
  value: number | string;
  unit?: string;
  trend?: 'up' | 'down' | 'stable';
  severity?: 'normal' | 'warning' | 'critical';
}

export const KPICard: React.FC<KPICardProps> = ({ 
  title, 
  value, 
  unit = '', 
  trend = 'stable',
  severity = 'normal'
}) => {
  return (
    <div className={`kpi-card ${severity}`}>
      <div className="kpi-header">{title}</div>
      <div className="kpi-value">
        {value}{unit}
        {trend !== 'stable' && (
          <span className={`trend ${trend}`}>
            {trend === 'up' ? '↑' : '↓'}
          </span>
        )}
      </div>
    </div>
  );
};
