import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isIconOnly?: boolean;
  isBlock?: boolean;
  isLoading?: boolean;
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
  children?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isIconOnly = false,
      isBlock = false,
      isLoading = false,
      leadingIcon,
      trailingIcon,
      disabled,
      className = '',
      children,
      ...props
    },
    ref
  ) => {
    const classNames = [
      'ak-btn',
      `ak-btn--${variant}`,
      size !== 'md' ? `ak-btn--${size}` : '',
      isIconOnly ? 'ak-btn--icon' : '',
      isBlock ? 'ak-btn--block' : '',
      isLoading ? 'is-loading' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        type={props.type || 'button'}
        className={classNames}
        disabled={disabled || isLoading}
        aria-busy={isLoading ? 'true' : undefined}
        {...props}
      >
        {isLoading ? (
          <span className="ak-spinner ak-spinner--sm" aria-hidden="true" />
        ) : leadingIcon ? (
          <span style={{ display: 'inline-flex', alignItems: 'center', marginRight: children ? 6 : 0 }}>
            {leadingIcon}
          </span>
        ) : null}
        {children}
        {trailingIcon && !isLoading && (
          <span style={{ display: 'inline-flex', alignItems: 'center', marginLeft: children ? 6 : 0 }}>
            {trailingIcon}
          </span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

