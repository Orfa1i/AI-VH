import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'interactive' | 'subtle';
  children?: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', className = '', children, ...props }, ref) => {
    const classNames = [
      'ak-card',
      variant === 'interactive' ? 'ak-card--interactive' : '',
      variant === 'subtle' ? 'ak-card--subtle' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <div ref={ref} className={classNames} {...props}>
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export const CardHead: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <div className={`ak-card__head ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <h3 className={`ak-card__title ${className}`} {...props}>
    {children}
  </h3>
);

export const CardMeta: React.FC<React.HTMLAttributes<HTMLSpanElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <span className={`ak-card__meta ${className}`} {...props}>
    {children}
  </span>
);

export const CardFoot: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <div className={`ak-card__foot ${className}`} {...props}>
    {children}
  </div>
);
