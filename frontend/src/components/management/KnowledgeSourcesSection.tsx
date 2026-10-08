import React, { useState, useEffect } from 'react';
import {
  Globe,
  Plus,
  RefreshCw,
  AlertCircle,
  Power,
  Trash2,
  BookOpen,
  Cpu,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';


import {
  Button,
  Badge,
  Card,
  CardHead,
  CardTitle,
  CardMeta,
  TextField,
  TextArea,
  Select,
  Stat,
  EmptyState,
  Alert,
} from '../ui';
import { AppPage } from '../layout/Templates';
import type { KnowledgeSource, KnowledgeSourceStatus, KnowledgeSourceType } from '../../types';

export const KnowledgeSourcesSection: React.FC = () => {
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'danger' | 'info'; text: string } | null>(null);

  // Form State
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [description, setDescription] = useState('');
  const [sourceType, setSourceType] = useState<KnowledgeSourceType>('CUSTOM');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const fetchSources = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/knowledge/sources');
      if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
      const data = await res.json();
      setSources(data.sources || []);
      setError(null);
    } catch (err: any) {
      setError('Unable to load clinical knowledge sources. Please verify backend connectivity.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, []);

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !url.trim()) return;

    setIsSubmitting(true);
    setActionMessage(null);

    try {
      const res = await fetch('/api/knowledge/sources', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          url: url.trim(),
          description: description.trim(),
          source_type: sourceType,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to save knowledge source');
      }

      setName('');
      setUrl('');
      setDescription('');
      setSourceType('CUSTOM');
      setActionMessage({
        type: 'success',
        text: 'Medical knowledge source registered and synchronized with MedGemma & Nemotron synthesis engine.',
      });
      await fetchSources();
    } catch (err: any) {
      setActionMessage({
        type: 'danger',
        text: err.message || 'Error creating knowledge source',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleStatus = async (source: KnowledgeSource) => {
    const nextStatus: KnowledgeSourceStatus = source.status === 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      const res = await fetch(`/api/knowledge/sources/${source.id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!res.ok) throw new Error('Status update failed');
      setSources((prev) =>
        prev.map((s) => (s.id === source.id ? { ...s, status: nextStatus } : s))
      );
      setActionMessage({
        type: 'info',
        text: `Source "${source.name}" is now ${nextStatus}. ${
          nextStatus === 'ACTIVE' ? 'Evidence is now available to MedGemma and Nemotron synthesis.' : 'Excluded from live diagnostic reasoning.'
        }`,
      });
    } catch (err: any) {
      setActionMessage({
        type: 'danger',
        text: `Failed to change status: ${err.message}`,
      });
    }
  };

  const handleSync = async (sourceId: string) => {
    setSyncingId(sourceId);
    setActionMessage(null);
    try {
      const res = await fetch(`/api/knowledge/sources/${sourceId}/sync`, {
        method: 'POST',
      });
      const data = await res.json();
      if (!res.ok || data.status === 'ERROR') {
        throw new Error(data.message || 'Synchronization check failed');
      }
      setActionMessage({
        type: 'success',
        text: `Source synchronized successfully. Verified connection and active pipeline registration.`,
      });
      await fetchSources();
    } catch (err: any) {
      setActionMessage({
        type: 'danger',
        text: `Sync error: ${err.message}`,
      });
      await fetchSources();
    } finally {
      setSyncingId(null);
    }
  };

  const handleDelete = async (sourceId: string, sourceName: string) => {
    if (!window.confirm(`Are you sure you want to remove "${sourceName}" from knowledge sources?`)) {
      return;
    }
    try {
      const res = await fetch(`/api/knowledge/sources/${sourceId}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('Delete request failed');
      setSources((prev) => prev.filter((s) => s.id !== sourceId));
      setActionMessage({
        type: 'info',
        text: `Knowledge source "${sourceName}" removed.`,
      });
    } catch (err: any) {
      setActionMessage({
        type: 'danger',
        text: `Delete failed: ${err.message}`,
      });
    }
  };

  const activeCount = sources.filter((s) => s.status === 'ACTIVE').length;
  const syncingCount = sources.filter((s) => s.status === 'SYNCING').length;
  const errorCount = sources.filter((s) => s.status === 'ERROR').length;

  const renderStatusBadge = (status: KnowledgeSourceStatus) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <Badge variant="success" hasDot>
            Active
          </Badge>
        );
      case 'INACTIVE':
        return (
          <Badge variant="neutral">
            Inactive
          </Badge>
        );
      case 'SYNCING':
        return (
          <Badge variant="brand" hasDot>
            Syncing
          </Badge>
        );
      case 'ERROR':
        return (
          <Badge variant="danger" hasDot>
            Error
          </Badge>
        );
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <AppPage
      title="Knowledge Sources"
      description="Manage approved medical knowledge sources synchronized with MedGemma, Harrison's knowledge base, and the Nemotron diagnostic synthesis engine."
      actions={
        <Button
          variant="secondary"
          size="sm"
          onClick={fetchSources}
          disabled={loading}
          leadingIcon={<RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />}
        >
          Refresh Sources
        </Button>
      }
    >
      {/* Architectural Pipeline Banner */}
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-default)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
          <ShieldCheck style={{ width: 18, height: 18, color: 'var(--color-primary)' }} />
          <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-primary)' }}>
            Shared Clinical Knowledge Pipeline Architecture
          </span>
        </div>
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: 'var(--space-3)',
            fontSize: '0.8125rem',
            color: 'var(--text-secondary)',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 500, color: 'var(--text-primary)' }}>
            <Globe style={{ width: 14, height: 14, color: 'var(--color-primary)' }} />
            Active Knowledge Sources
          </span>
          <ArrowRight style={{ width: 14, height: 14, color: 'var(--text-muted)' }} />
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 500, color: 'var(--text-primary)' }}>
            <Layers style={{ width: 14, height: 14, color: 'var(--color-primary)' }} />
            Retrieve Evidence
          </span>
          <ArrowRight style={{ width: 14, height: 14, color: 'var(--text-muted)' }} />
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 500, color: 'var(--text-primary)' }}>
            <BookOpen style={{ width: 14, height: 14, color: 'var(--color-primary)' }} />
            MedGemma + Harrison's + Sources
          </span>
          <ArrowRight style={{ width: 14, height: 14, color: 'var(--text-muted)' }} />
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 500, color: 'var(--text-primary)' }}>
            <Cpu style={{ width: 14, height: 14, color: 'var(--color-primary)' }} />
            Nemotron-3-Nano-30B-A3B
          </span>
          <ArrowRight style={{ width: 14, height: 14, color: 'var(--text-muted)' }} />
          <span style={{ fontWeight: 600, color: 'var(--color-success)' }}>
            Evidence-Grounded Diagnostic Report
          </span>
        </div>
      </div>

      {/* Global Stat Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 'var(--space-4)',
          marginBottom: 'var(--space-6)',
        }}
      >
        <Stat
          label="Total Registered Sources"
          value={sources.length}
          delta="Approved clinical endpoints"
        />
        <Stat
          label="Active Diagnostic Sources"
          value={activeCount}
          delta="Synchronized with MedGemma"
        />
        <Stat
          label="Syncing / Verifying"
          value={syncingCount}
          delta="Real-time connectivity"
        />
        <Stat
          label="Operational Errors"
          value={errorCount}
          delta={errorCount > 0 ? 'Needs attention' : 'All systems normal'}
        />
      </div>

      {actionMessage && (
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <Alert
            variant={actionMessage.type}
            title={actionMessage.type === 'success' ? 'Pipeline Synchronized' : actionMessage.type === 'danger' ? 'Pipeline Notice' : 'Source Updated'}
          >
            {actionMessage.text}
          </Alert>
        </div>
      )}

      {error && (
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <Alert variant="danger" title="Service Connection Error">
            {error}
          </Alert>
        </div>
      )}


      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: 'var(--space-6)',
        }}
      >
        {/* Registration Form Card */}
        <Card>
          <CardHead>
            <div>
              <CardTitle>Add Medical Knowledge Source</CardTitle>
              <CardMeta>Register an authoritative clinical repository or literature feed by URL</CardMeta>
            </div>
          </CardHead>

          <form onSubmit={handleAddSource} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <TextField
              label="Source Name"
              required
              placeholder="e.g. PubMed NCBI, OpenFDA Drug Registry, RxNorm Formulary"
              value={name}
              onChange={(e) => setName(e.target.value)}
              helpText="Descriptive label displayed on clinical citations and reports"
            />

            <TextField
              label="Source URL / API Endpoint"
              required
              placeholder="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/ or https://api.fda.gov/drug/label.json"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              leadingIcon={<Globe style={{ width: 16, height: 16, color: 'var(--text-muted)' }} />}
              helpText="Valid HTTP/HTTPS medical ontology, search, or label endpoint"
            />

            <Select
              label="Source Architecture Category"
              value={sourceType}
              onChange={(e) => setSourceType(e.target.value as KnowledgeSourceType)}
            >
              <option value="CUSTOM">Custom Medical Reference / Institution Guidelines</option>
              <option value="PUBMED">PubMed / MEDLINE Peer-Reviewed Literature</option>
              <option value="OPENFDA">openFDA Drug Labels & Safety Alerts</option>
              <option value="RXNORM">NLM RxNorm Clinical Formulary</option>
            </Select>

            <TextArea
              label="Source Description"
              rows={3}
              placeholder="Clinical scope, evidence tier, covered therapeutic classes, or hospital guidelines..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              helpText="Contextual metadata provided to MedGemma and Nemotron"
            />

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
              <Button
                type="submit"
                variant="primary"
                disabled={isSubmitting || !name.trim() || !url.trim()}
                leadingIcon={<Plus className="w-4 h-4" />}
              >
                {isSubmitting ? 'Saving Source...' : 'Save Knowledge Source'}
              </Button>
            </div>
          </form>
        </Card>

        {/* Sources List & Management Card */}
        <Card>
          <CardHead>
            <div>
              <CardTitle>Configured Knowledge Sources</CardTitle>
              <CardMeta>
                {sources.length} total source{sources.length === 1 ? '' : 's'} registered in AI-VH shared pipeline
              </CardMeta>
            </div>
          </CardHead>

          {loading && sources.length === 0 ? (
            <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-secondary)' }}>
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
              <p style={{ fontSize: '0.875rem' }}>Loading configured medical knowledge sources...</p>
            </div>
          ) : sources.length === 0 ? (
            <EmptyState
              title="No Knowledge Sources Configured"
              description="Add your first medical literature or pharmacology source using the registration form."
              action={
                <Button variant="secondary" size="sm" onClick={() => setName('PubMed / MEDLINE Clinical Library')}>
                  Fill Example
                </Button>
              }
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {sources.map((source) => {
                const isActive = source.status === 'ACTIVE';
                const isSyncing = syncingId === source.id || source.status === 'SYNCING';

                return (
                  <div
                    key={source.id}
                    style={{
                      background: 'var(--bg-canvas)',
                      border: '1px solid var(--border-default)',
                      borderRadius: 'var(--radius-md)',
                      padding: 'var(--space-4)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 'var(--space-3)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)' }}>
                            {source.name}
                          </span>
                          {renderStatusBadge(source.status)}
                          <span
                            style={{
                              fontSize: '0.75rem',
                              fontFamily: 'monospace',
                              padding: '2px 6px',
                              background: 'var(--bg-surface)',
                              border: '1px solid var(--border-subtle)',
                              borderRadius: 'var(--radius-sm)',
                              color: 'var(--text-secondary)',
                            }}
                          >
                            {source.source_type}
                          </span>
                        </div>

                        <div
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            fontSize: '0.75rem',
                            color: 'var(--text-muted)',
                            marginTop: 4,
                            wordBreak: 'break-all',
                          }}
                        >
                          <Globe style={{ width: 12, height: 12, flexShrink: 0 }} />
                          <span>{source.url}</span>
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexShrink: 0 }}>
                        <Button
                          variant={isActive ? 'secondary' : 'primary'}
                          size="sm"
                          onClick={() => handleToggleStatus(source)}
                          leadingIcon={<Power className="w-3.5 h-3.5" />}
                        >
                          {isActive ? 'Deactivate' : 'Activate'}
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={isSyncing}
                          onClick={() => handleSync(source.id)}
                          aria-label={`Sync ${source.name}`}
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                        </Button>

                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(source.id, source.name)}
                          aria-label={`Delete ${source.name}`}
                          style={{ color: 'var(--color-danger)' }}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>

                    {source.description && (
                      <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', margin: 0 }}>
                        {source.description}
                      </p>
                    )}

                    {source.error_message && (
                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                          fontSize: '0.75rem',
                          color: 'var(--color-danger)',
                          background: 'var(--color-danger-subtle)',
                          padding: '6px 10px',
                          borderRadius: 'var(--radius-sm)',
                        }}
                      >
                        <AlertCircle style={{ width: 14, height: 14, flexShrink: 0 }} />
                        <span>{source.error_message}</span>
                      </div>
                    )}

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        fontSize: '0.6875rem',
                        color: 'var(--text-muted)',
                        borderTop: '1px solid var(--border-subtle)',
                        paddingTop: 'var(--space-2)',
                      }}
                    >
                      <span>ID: {source.id}</span>
                      <span>
                        Last Synced:{' '}
                        {source.last_synced_at
                          ? new Date(source.last_synced_at).toLocaleString()
                          : 'Never'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>
    </AppPage>
  );
};
