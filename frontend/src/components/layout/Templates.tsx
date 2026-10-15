import React from 'react';

/* ---------- Layout Containers ---------- */
export interface ContainerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'default' | 'narrow' | 'wide' | 'full';
  children: React.ReactNode;
}

export const Container: React.FC<ContainerProps> = ({
  size = 'default',
  className = '',
  style,
  children,
  ...props
}) => {
  const maxMap = {
    narrow: 640,
    default: 1200, // --content-max
    wide: 1440,
    full: '100%',
  };

  return (
    <div
      className={className}
      style={{
        maxWidth: maxMap[size],
        width: '100%',
        margin: '0 auto',
        paddingLeft: 'var(--space-6)',
        paddingRight: 'var(--space-6)',
        boxSizing: 'border-box',
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};

/* ---------- Page Header Pattern ---------- */
export interface PageHeaderProps {
  title: string;
  description?: string;
  breadcrumbs?: Array<{ label: string; href?: string; isCurrent?: boolean }>;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  breadcrumbs,
  actions,
}) => {
  return (
    <div style={{ marginBottom: 'var(--space-6)' }}>
      {breadcrumbs && breadcrumbs.length > 0 && (
        <nav aria-label="Breadcrumb" style={{ marginBottom: 'var(--space-2)' }}>
          <ol className="ak-crumbs">
            {breadcrumbs.map((crumb, idx) => (
              <li key={idx} aria-current={crumb.isCurrent ? 'page' : undefined}>
                {crumb.isCurrent ? (
                  <span>{crumb.label}</span>
                ) : (
                  <a href={crumb.href || '#'}>{crumb.label}</a>
                )}
              </li>
            ))}
          </ol>
        </nav>
      )}

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: 'var(--space-4)',
        }}
      >
        <div>
          <h1 className="heading-1">{title}</h1>
          {description && (
            <p className="body" style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
              {description}
            </p>
          )}
        </div>

        {actions && <div style={{ display: 'flex', gap: 'var(--space-3)' }}>{actions}</div>}
      </div>
    </div>
  );
};

/* ---------- AppPage Template ---------- */
export interface AppPageProps {
  title?: string;
  description?: string;
  breadcrumbs?: Array<{ label: string; href?: string; isCurrent?: boolean }>;
  actions?: React.ReactNode;
  children: React.ReactNode;
}

export const AppPage: React.FC<AppPageProps> = ({
  title,
  description,
  breadcrumbs,
  actions,
  children,
}) => {
  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        padding: 'var(--space-8)',
        maxWidth: '100%',
        overflowY: 'auto',
      }}
    >
      {title && (
        <PageHeader
          title={title}
          description={description}
          breadcrumbs={breadcrumbs}
          actions={actions}
        />
      )}
      {children}
    </main>
  );
};

/* ---------- DetailPage Template (8 / 4 two-column rail) ---------- */
export interface DetailPageProps {
  title?: string;
  description?: string;
  breadcrumbs?: Array<{ label: string; href?: string; isCurrent?: boolean }>;
  actions?: React.ReactNode;
  children: React.ReactNode;
  rail: React.ReactNode;
}

export const DetailPage: React.FC<DetailPageProps> = ({
  title,
  description,
  breadcrumbs,
  actions,
  children,
  rail,
}) => {
  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        padding: 'var(--space-8)',
        overflowY: 'auto',
      }}
    >
      {title && (
        <PageHeader
          title={title}
          description={description}
          breadcrumbs={breadcrumbs}
          actions={actions}
        />
      )}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 8fr) minmax(320px, 4fr)',
          gap: 'var(--space-6)',
          alignItems: 'start',
        }}
      >
        <div style={{ minWidth: 0 }}>{children}</div>
        <aside style={{ minWidth: 0 }}>{rail}</aside>
      </div>
    </main>
  );
};

/* ---------- FlowPage Template (Single focused 640px column) ---------- */
export interface FlowPageProps {
  title?: string;
  description?: string;
  steps?: React.ReactNode;
  children: React.ReactNode;
}

export const FlowPage: React.FC<FlowPageProps> = ({
  title,
  description,
  steps,
  children,
}) => {
  return (
    <main
      id="main-content"
      style={{
        flex: 1,
        padding: 'var(--space-8)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        overflowY: 'auto',
      }}
    >
      <div style={{ width: '100%', maxWidth: 640 }}>
        {steps && <div style={{ marginBottom: 'var(--space-8)' }}>{steps}</div>}
        {title && (
          <div style={{ marginBottom: 'var(--space-6)', textAlign: 'center' }}>
            <h1 className="heading-1">{title}</h1>
            {description && (
              <p className="body" style={{ color: 'var(--text-secondary)', marginTop: 4 }}>
                {description}
              </p>
            )}
          </div>
        )}
        {children}
      </div>
    </main>
  );
};

/* ---------- AuthPage Template (440px centred card) ---------- */
export interface AuthPageProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}

export const AuthPage: React.FC<AuthPageProps> = ({
  title,
  subtitle,
  children,
}) => {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'var(--bg-page)',
        padding: 'var(--space-4)',
      }}
    >
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <img
          src="./logos/vh-logo-horizontal.svg"
          alt="Virtual Hospital by Asklevia"
          style={{ height: 36, width: 'auto' }}
        />
      </div>
      <div
        className="ak-card"
        style={{
          width: '100%',
          maxWidth: 440,
          boxShadow: 'var(--shadow-md)',
        }}
      >
        <h2 className="heading-2" style={{ textAlign: 'center' }}>{title}</h2>
        {subtitle && (
          <p className="body" style={{ color: 'var(--text-secondary)', textAlign: 'center', marginTop: 4 }}>
            {subtitle}
          </p>
        )}
        <div style={{ marginTop: 'var(--space-6)' }}>{children}</div>
      </div>
    </div>
  );
};
