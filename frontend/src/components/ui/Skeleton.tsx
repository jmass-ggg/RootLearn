/**
 * Skeleton loading component
 * Provides consistent loading placeholders throughout the application
 * Requirements: 15.1
 */

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rect' | 'circle';
  width?: string;
  height?: string;
}

export function Skeleton({
  className = '',
  variant = 'rect',
  width,
  height,
}: SkeletonProps) {
  const baseStyles = 'animate-pulse bg-gray-200';
  
  const variantStyles = {
    text: 'h-4 rounded',
    rect: 'rounded-lg',
    circle: 'rounded-full',
  };

  const style: React.CSSProperties = {
    width: width || undefined,
    height: height || undefined,
  };

  return (
    <div 
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
}

/**
 * Card skeleton for loading card-based content
 */
export function CardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <Skeleton variant="text" className="w-3/4 mb-4" height="24px" />
      <Skeleton variant="text" className="w-full mb-2" />
      <Skeleton variant="text" className="w-5/6 mb-2" />
      <Skeleton variant="text" className="w-4/6" />
    </div>
  );
}

/**
 * List skeleton for loading list items
 */
export function ListSkeleton({ count = 3, className = '' }: { count?: number; className?: string }) {
  return (
    <div className={`space-y-4 ${className}`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          <Skeleton variant="circle" width="48px" height="48px" />
          <div className="flex-1">
            <Skeleton variant="text" className="w-3/4 mb-2" />
            <Skeleton variant="text" className="w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}
