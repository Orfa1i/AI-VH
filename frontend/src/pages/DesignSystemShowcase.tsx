import React, { useState } from 'react';
import {
  Button,
  Badge,
  Chip,
  Card,
  CardHead,
  CardTitle,
  CardMeta,
  Dialog,
  TextField,
  TextArea,
  Select,
  Checkbox,
  ProgressBar,
  Alert,
  Table,
  Tabs,
  Stat,
  EmptyState,
  Divider,
} from '../components/ui';
import {
  Search,
  ShieldCheck,
} from 'lucide-react';

export const DesignSystemShowcase: React.FC = () => {
  const [activeTab, setActiveTab] = useState('primitives');
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [selectValue, setSelectValue] = useState('cardio');
  const [progressVal, setProgressVal] = useState(65);
  const [chipSelected, setChipSelected] = useState(true);

  return (
    <div style={{ padding: '32px 24px', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 40 }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 className="heading-1">Asklevia Design System</h1>
          <Badge variant="ai">AI System</Badge>
          <Badge variant="outline">v1.0.0</Badge>
        </div>
        <p className="body" style={{ color: 'var(--text-secondary)', marginTop: 8 }}>
          Living component specification and test harness adhering to BRAND-CONTRACT.md.
        </p>
      </div>

      <Divider />

      {/* Tabs */}
      <Tabs
        activeId={activeTab}
        onChange={setActiveTab}
        tabs={[
          { id: 'primitives', label: 'Actions & Inputs' },
          { id: 'status', label: 'Badges, Progress & Feedback' },
          { id: 'surfaces', label: 'Cards, Modals & Data Tables' },
          { id: 'brand', label: 'Brand Identity & Assets' },
        ]}
      />

      {/* SECTION 1: Buttons & Inputs */}
      {activeTab === 'primitives' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* Buttons */}
          <Card>
            <CardHead>
              <CardTitle>Buttons</CardTitle>
              <CardMeta>Pill-shaped, sentence-case verb labels</CardMeta>
            </CardHead>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center' }}>
              <Button variant="primary">Start analysis</Button>
              <Button variant="secondary">Review findings</Button>
              <Button variant="ghost">View telemetry</Button>
              <Button variant="danger">Discharge patient</Button>
              <Button variant="primary" size="sm">Small action</Button>
              <Button variant="primary" size="lg">Large action</Button>
              <Button variant="primary" isLoading>Processing</Button>
              <Button variant="primary" disabled>Disabled action</Button>
              <Button variant="ghost" isIconOnly aria-label="Search records">
                <Search aria-hidden="true" style={{ width: 18, height: 18 }} />
              </Button>
            </div>
          </Card>

          {/* Form Inputs */}
          <Card>
            <CardHead>
              <CardTitle>Form Inputs & Selects</CardTitle>
              <CardMeta>8px radius, accessible focus rings, error states</CardMeta>
            </CardHead>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
              <TextField
                label="Patient Name"
                placeholder="e.g. Eleanor Vance"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                helpText="Full legal name from admission form"
              />
              <TextField
                label="MRN / Record ID"
                placeholder="Search MRN..."
                leadingIcon={<Search aria-hidden="true" />}
              />
              <TextField
                label="Invalid Example"
                value="Erroneous Lab Metric"
                error="Value exceeds valid clinical range (0-100)"
                readOnly
              />
              <Select
                label="Medical Specialty"
                value={selectValue}
                onChange={(e) => setSelectValue(e.target.value)}
              >
                <option value="cardio">Cardiology</option>
                <option value="internal">Internal Medicine</option>
                <option value="pulm">Pulmonology</option>
                <option value="neuro">Neurology</option>
              </Select>
            </div>

            <div style={{ marginTop: 16 }}>
              <TextArea
                label="Clinical Presentation & Symptoms"
                placeholder="Enter subjective symptoms and chief complaint..."
                rows={3}
              />
            </div>

            <div style={{ display: 'flex', gap: 24, marginTop: 16 }}>
              <Checkbox label="Admit to Intensive Care" hint="Requires attending signoff" defaultChecked />
              <Checkbox label="High-Risk Stratification" hint="Triggers immediate telemetry" />
            </div>
          </Card>
        </div>
      )}

      {/* SECTION 2: Badges, Progress & Feedback */}
      {activeTab === 'status' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* Badges & Chips */}
          <Card>
            <CardHead>
              <CardTitle>Badges & Filter Chips</CardTitle>
              <CardMeta>Calibrated semantic tints; Neural Spectrum restricted strictly to AI badge</CardMeta>
            </CardHead>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
              <Badge variant="neutral">Draft</Badge>
              <Badge variant="brand">Scheduled</Badge>
              <Badge variant="success" hasDot>Active Census</Badge>
              <Badge variant="warning">Pending Review</Badge>
              <Badge variant="danger">Critical Alert</Badge>
              <Badge variant="info">In Workup</Badge>
              <Badge variant="outline">ICD-10</Badge>
              <Badge variant="ai">AI-assisted diagnosis</Badge>
            </div>

            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <Chip isSelected={chipSelected} onClick={() => setChipSelected(!chipSelected)}>
                Filter: Cardiology
              </Chip>
              <Chip isSelected={false}>Filter: Unreviewed</Chip>
              <Chip isSelected={false}>Filter: Discharged</Chip>
            </div>
          </Card>

          {/* Progress Indicators */}
          <Card>
            <CardHead>
              <CardTitle>Progress Bars & AI Trajectory</CardTitle>
              <CardMeta>Neural Spectrum progress strictly for AI encounter synthesis</CardMeta>
            </CardHead>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              <ProgressBar
                label="Autonomous Diagnosis Encounter"
                variant="spectrum"
                value={progressVal}
              />
              <ProgressBar
                label="Attending Physician Review Queue"
                variant="primary"
                value={42}
              />
              <ProgressBar
                label="Clinical Safety Gate"
                variant="success"
                value={100}
              />
              <div style={{ display: 'flex', gap: 12, marginTop: 8 }}>
                <Button size="sm" variant="secondary" onClick={() => setProgressVal(Math.max(0, progressVal - 15))}>
                  -15%
                </Button>
                <Button size="sm" variant="secondary" onClick={() => setProgressVal(Math.min(100, progressVal + 15))}>
                  +15%
                </Button>
              </div>
            </div>
          </Card>

          {/* Alerts */}
          <Card>
            <CardHead>
              <CardTitle>Alerts</CardTitle>
              <CardMeta>Inline clinical notices</CardMeta>
            </CardHead>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <Alert variant="info" title="Clinical Guidance">
                Patient presentation suggests acute coronary syndrome. Recommend 12-lead ECG and Troponin panel.
              </Alert>
              <Alert variant="success" title="Encounter Completed">
                Clinical diagnosis report synthesized and committed to persistent database.
              </Alert>
              <Alert variant="warning" title="Pending Verification">
                Attending physician review required before final discharge authorization.
              </Alert>
              <Alert variant="danger" title="Safety Gate Warning">
                Discrepancy detected between patient vital signs and recommended dosage.
              </Alert>
            </div>
          </Card>
        </div>
      )}

      {/* SECTION 3: Surfaces, Tables & Modals */}
      {activeTab === 'surfaces' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
          {/* Stats */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <Card>
              <Stat label="Total Admitted Census" value="28" delta="+3 since 08:00" />
            </Card>
            <Card>
              <Stat label="Pending Reviews" value="4" delta="Target < 5" />
            </Card>
            <Card>
              <Stat label="Diagnostic Agreement" value="96.4%" delta="MedGemma 4B" />
            </Card>
          </div>

          {/* Table */}
          <Card>
            <CardHead>
              <CardTitle>Patient Census Roster</CardTitle>
              <CardMeta>Hairline rows, tabular figures in Geist Mono</CardMeta>
            </CardHead>
            <Table>
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>MRN</th>
                  <th>Department</th>
                  <th>Triage Status</th>
                  <th className="is-num">Confidence</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Charles Brown</strong></td>
                  <td className="is-num">PAT-08921</td>
                  <td>Internal Medicine</td>
                  <td><Badge variant="warning">Under Workup</Badge></td>
                  <td className="is-num">94%</td>
                  <td style={{ textAlign: 'right' }}>
                    <Button size="sm" variant="ghost">View Chart</Button>
                  </td>
                </tr>
                <tr>
                  <td><strong>Eleanor Vance</strong></td>
                  <td className="is-num">PAT-09142</td>
                  <td>Cardiology</td>
                  <td><Badge variant="success">Admitted</Badge></td>
                  <td className="is-num">98%</td>
                  <td style={{ textAlign: 'right' }}>
                    <Button size="sm" variant="ghost">View Chart</Button>
                  </td>
                </tr>
              </tbody>
            </Table>
          </Card>

          {/* Modal Demo Button */}
          <Card>
            <CardHead>
              <CardTitle>Modal Dialogs</CardTitle>
              <CardMeta>Focus trap, escape key handling, scrim backdrop</CardMeta>
            </CardHead>
            <div>
              <Button variant="primary" onClick={() => setIsDialogOpen(true)}>
                Open clinical dialog
              </Button>
            </div>
          </Card>

          <Dialog
            isOpen={isDialogOpen}
            onClose={() => setIsDialogOpen(false)}
            title="Authorize Patient Discharge"
            description="Patient Charles Brown is clinically stable with completed diagnostic synthesis."
            actions={
              <>
                <Button variant="secondary" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" onClick={() => setIsDialogOpen(false)}>
                  Confirm discharge
                </Button>
              </>
            }
          >
            <p className="body" style={{ color: 'var(--text-secondary)' }}>
              All lab panels, radiology consults, and primary differential evaluations have been verified by the attending physician.
            </p>
          </Dialog>

          {/* Empty State */}
          <Card>
            <EmptyState
              icon={<ShieldCheck aria-hidden="true" />}
              title="Review Queue Clear"
              description="All autonomous diagnosis reports have been reviewed and finalized by attending staff."
              action={<Button variant="secondary">Ingest new case</Button>}
            />
          </Card>
        </div>
      )}

      {/* SECTION 4: Brand Identity & Logos */}
      {activeTab === 'brand' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          <Card>
            <CardHead>
              <div>
                <CardTitle>Official Lockups</CardTitle>
                <CardMeta>Vector SVG master lockups from the Virtual Hospital brand kit</CardMeta>
              </div>
            </CardHead>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-6)', marginTop: 'var(--space-4)' }}>
              <div style={{ padding: 'var(--space-6)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <span className="caption" style={{ color: 'var(--text-secondary)' }}>Primary Horizontal (Header Master)</span>
                <img src="/logos/vh-logo-horizontal.svg" alt="Virtual Hospital by Asklevia" style={{ height: 38, width: 'auto', alignSelf: 'flex-start' }} />
              </div>
              <div style={{ padding: 'var(--space-6)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <span className="caption" style={{ color: 'var(--text-secondary)' }}>Compact Lockup (&lt; 160px Contexts)</span>
                <img src="/logos/vh-logo-compact.svg" alt="Virtual Hospital Compact" style={{ height: 34, width: 'auto', alignSelf: 'flex-start' }} />
              </div>
              <div style={{ padding: 'var(--space-6)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <span className="caption" style={{ color: 'var(--text-secondary)' }}>Stacked Centered Mark</span>
                <img src="/logos/vh-logo-stacked.svg" alt="Virtual Hospital Stacked" style={{ height: 64, width: 'auto', alignSelf: 'flex-start' }} />
              </div>
            </div>
          </Card>

          <Card>
            <CardHead>
              <div>
                <CardTitle>Symbols & Application Marks</CardTitle>
                <CardMeta>Medical cross helix symbol, small-format symbol, and rounded app icon</CardMeta>
              </div>
            </CardHead>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-6)', marginTop: 'var(--space-4)' }}>
              <div style={{ padding: 'var(--space-6)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
                <img src="/logos/vh-symbol.svg" alt="Virtual Hospital Helix Symbol" style={{ width: 64, height: 64 }} />
                <span className="caption" style={{ color: 'var(--text-secondary)' }}>Cross Helix Symbol</span>
              </div>
              <div style={{ padding: 'var(--space-6)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
                <img src="/logos/vh-symbol-small.svg" alt="Virtual Hospital Micro Symbol" style={{ width: 48, height: 48 }} />
                <span className="caption" style={{ color: 'var(--text-secondary)' }}>Small Symbol (&le; 48px)</span>
              </div>
              <div style={{ padding: 'var(--space-6)', border: '1px solid var(--border-default)', borderRadius: 'var(--radius-md)', background: 'var(--bg-surface)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
                <img src="/logos/vh-app-icon-rounded.svg" alt="Virtual Hospital App Icon" style={{ width: 64, height: 64 }} />
                <span className="caption" style={{ color: 'var(--text-secondary)' }}>Rounded App Icon (PWA)</span>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
