import React from 'react';

interface TimelineAnimationProps extends React.HTMLAttributes<HTMLElement> {
  timelineRef?: React.RefObject<HTMLDivElement | null>;
  animationNum?: number;
  as?: any;
  children?: React.ReactNode;
  className?: string;
  src?: string;
  alt?: string;
}

export const TimelineAnimation: React.FC<TimelineAnimationProps> = ({
  timelineRef,
  animationNum = 1,
  as: Component = 'div',
  children,
  className = '',
  ...props
}) => {
  const delay = (animationNum - 1) * 120;
  return (
    <Component
      className={`transition-all duration-700 ease-out transform ${className}`}
      style={{
        animationDelay: `${delay}ms`,
        ...props.style,
      }}
      {...props}
    >
      {children}
    </Component>
  );
};

export default TimelineAnimation;
