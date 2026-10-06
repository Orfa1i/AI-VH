import React from 'react';
import { AlertCircle } from 'lucide-react';

export interface TextFieldProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helpText?: string;
  error?: string;
  leadingIcon?: React.ReactNode;
}

export const TextField = React.forwardRef<HTMLInputElement, TextFieldProps>(
  (
    {
      label,
      helpText,
      error,
      leadingIcon,
      id,
      className = '',
      required,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || React.useId();
    const hasError = Boolean(error);

    return (
      <div className="ak-field">
        {label && (
          <label htmlFor={inputId} className="ak-label">
            {label}
            {required && <span aria-hidden="true"> *</span>}
          </label>
        )}
        <div className={leadingIcon ? 'ak-input-group' : undefined}>
          {leadingIcon}
          <input
            ref={ref}
            id={inputId}
            className={`ak-input ${className}`}
            required={required}
            disabled={disabled}
            aria-invalid={hasError ? 'true' : undefined}
            {...props}
          />
        </div>
        {hasError ? (
          <span className="ak-help ak-help--error" role="alert">
            <AlertCircle aria-hidden="true" />
            {error}
          </span>
        ) : helpText ? (
          <span className="ak-help">{helpText}</span>
        ) : null}
      </div>
    );
  }
);

TextField.displayName = 'TextField';

export interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  helpText?: string;
  error?: string;
}

export const TextArea = React.forwardRef<HTMLTextAreaElement, TextAreaProps>(
  (
    {
      label,
      helpText,
      error,
      id,
      className = '',
      required,
      disabled,
      ...props
    },
    ref
  ) => {
    const inputId = id || React.useId();
    const hasError = Boolean(error);

    return (
      <div className="ak-field">
        {label && (
          <label htmlFor={inputId} className="ak-label">
            {label}
            {required && <span aria-hidden="true"> *</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={`ak-textarea ${className}`}
          required={required}
          disabled={disabled}
          aria-invalid={hasError ? 'true' : undefined}
          {...props}
        />
        {hasError ? (
          <span className="ak-help ak-help--error" role="alert">
            <AlertCircle aria-hidden="true" />
            {error}
          </span>
        ) : helpText ? (
          <span className="ak-help">{helpText}</span>
        ) : null}
      </div>
    );
  }
);

TextArea.displayName = 'TextArea';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  helpText?: string;
  error?: string;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      helpText,
      error,
      id,
      className = '',
      required,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const selectId = id || React.useId();
    const hasError = Boolean(error);

    return (
      <div className="ak-field">
        {label && (
          <label htmlFor={selectId} className="ak-label">
            {label}
            {required && <span aria-hidden="true"> *</span>}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={`ak-select ${className}`}
          required={required}
          disabled={disabled}
          aria-invalid={hasError ? 'true' : undefined}
          {...props}
        >
          {children}
        </select>
        {hasError ? (
          <span className="ak-help ak-help--error" role="alert">
            <AlertCircle aria-hidden="true" />
            {error}
          </span>
        ) : helpText ? (
          <span className="ak-help">{helpText}</span>
        ) : null}
      </div>
    );
  }
);

Select.displayName = 'Select';

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  helpText?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, hint, helpText, id, className = '', ...props }, ref) => {
    const inputId = id || React.useId();
    const effectiveHint = hint || helpText;

    return (
      <label htmlFor={inputId} className="ak-choice">
        <input
          ref={ref}
          id={inputId}
          type="checkbox"
          className={`ak-check ${className}`}
          {...props}
        />
        {(label || effectiveHint) && (
          <div>
            {label && <span>{label}</span>}
            {effectiveHint && <span className="ak-choice__hint">{effectiveHint}</span>}
          </div>
        )}
      </label>
    );
  }
);


Checkbox.displayName = 'Checkbox';
