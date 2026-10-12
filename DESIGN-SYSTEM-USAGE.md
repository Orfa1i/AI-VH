# Asklevia Design System Usage & Developer Guide

## 1. Introduction
The Asklevia Design System provides a clinical-grade, high-contrast, accessible UI toolkit purpose-built for the AI Virtual Hospital. It is engineered to comply with WCAG 2.2 AA accessibility standards, eliminate arbitrary CSS bloat, and maintain an uncompromising clinical visual standard.

---

## 2. Core Brand Tokens & Principles

### A. Surface Architecture
- **Application Canvas**: `var(--ak-color-bg-app)` (`#F7F8FB`) — crisp light background.
- **Card & Component Surfaces**: `var(--ak-color-bg-surface)` (`#FFFFFF`) — pure white cards with 16px radius (`var(--ak-radius-lg)`).
- **Subtle Containers**: `var(--ak-color-bg-subtle)` (`#F1F5F9`) — secondary utility boxes and table headers.
- **Hairline Borders**: `var(--ak-color-border-subtle)` (`#E2E8F0`) — 1px subtle borders.
- **Brand Action Accent**: `var(--ak-color-primary)` (`#4F46E5`) with soft tint `var(--ak-color-primary-soft)` (`#EEF2FF`).

### B. Typography
- **Headings & Display**: `Funnel Display` (`font-headline`, `font-headline-sm`).
- **Body & Clinical Interface**: `Host Grotesk` (`font-sans`).
- **Telemetry & Tabular Numbers**: `Geist Mono` (`font-mono`, `tabular-nums`).
- **Minimum Font Size**: 12px for body and utility labels (no sub-10px illegible text).

### C. Neural Spectrum Rule
The continuous rainbow Neural Spectrum is restricted **STRICTLY** to:
1. `.ak-progress--spectrum`: Active AI encounter synthesis.
2. `.ak-badge--ai`: AI-generated findings, verified differential insights.
3. `.ak-divider--spectrum`: Top hero or primary section divider (maximum 1 per page).
*Never apply the spectrum gradient to arbitrary buttons, borders, text, or cards.*

---

## 3. UI Primitives Reference

Import primitives directly from `src/components/ui`:

```tsx
import { 
  Button, 
  Badge, 
  Chip, 
  Card, 
  Dialog, 
  TextField, 
  Select, 
  ProgressBar,
  Stat 
} from '../ui';
```

### Button
- **Variants**: `primary`, `secondary`, `ghost`, `danger`.
- **Sizes**: `sm`, `md`, `lg`.
- **Props**: `leadingIcon`, `trailingIcon`, `isLoading`, `disabled`.
- **Label Rule**: Must start with a verb in sentence case (e.g., "Start analysis", "Sign report", "Admit patient").

```tsx
<Button 
  variant="primary" 
  size="md" 
  onClick={handleAdmit}
  leadingIcon={<UserPlus className="w-4 h-4" />}
>
  Admit patient
</Button>
```

### Badge & Chip
- **Badge Variants**: `neutral`, `brand` / `primary`, `success`, `warning`, `danger`, `ai`.
- **Chip**: Interactive filter pill with `isSelected` and optional `onRemove` affordance.

```tsx
<Badge variant="success">Discharged</Badge>
<Badge variant="ai">AI-assisted diagnosis</Badge>
<Chip isSelected={activeFilter === 'ICU'} onClick={() => setFilter('ICU')}>
  ICU Patients
</Chip>
```

### Card
- Clean white surface with hairline border and optional header slot.

```tsx
<Card className="p-4">
  <h3 className="text-sm font-semibold text-[var(--ak-color-text-primary)]">
    Patient Assessment
  </h3>
  <p className="text-xs text-[var(--ak-color-text-secondary)] mt-1">
    Telemetry vitals within normal parameters.
  </p>
</Card>
```

---

## 4. Page Templates & Layout Containers

When creating new views, wrap content with layout primitives from `src/components/layout/Templates.tsx`:

```tsx
import { AppPage, Container, PageHeader } from '../layout/Templates';

export const MyClinicalSection = () => {
  return (
    <AppPage>
      <Container>
        <PageHeader
          title="Inpatient Cardiology Directory"
          description="Real-time cardiac telemetry and bed allocations."
          action={<Button variant="primary">New consultation</Button>}
        />
        {/* Workstation body */}
      </Container>
    </AppPage>
  );
};
```

---

## 5. Developer Guard Rails & Linting

### The Zero-Debt Rule
Never introduce arbitrary Hex colors (`#xxx`), RGB values, or arbitrary Tailwind color classes (`bg-slate-800`, `text-blue-500`) into component files. Always utilize Asklevia CSS custom properties:
- `bg-[var(--ak-color-bg-app)]`
- `bg-[var(--ak-color-bg-surface)]`
- `bg-[var(--ak-color-bg-subtle)]`
- `border-[var(--ak-color-border-subtle)]`
- `text-[var(--ak-color-text-primary)]`
- `text-[var(--ak-color-text-secondary)]`
- `text-[var(--ak-color-text-muted)]`
- `text-[var(--ak-color-success)]`, `text-[var(--ak-color-danger)]`, `text-[var(--ak-color-warning)]`

### Brand Linter Command
Before opening a PR or committing changes, run:
```bash
npm run lint:brand
```
The build pipeline enforces **0 style debt count**.
