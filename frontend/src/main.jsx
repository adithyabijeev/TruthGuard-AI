import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { ShieldCheck, Search, Activity, AlertTriangle, Network, History, ChevronRight, Zap, LockKeyhole, CircleCheck, Loader2, CheckCircle2, ShieldAlert, ArrowRight, FileText, Check, X, AlertCircle, HelpCircle, ExternalLink, Layers, FileCheck2, Scale, Newspaper } from 'lucide-react'
import './styles.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

async function api(path, options = {}) {
  const r = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }, ...options })
  if (!r.ok) throw new Error((await r.text()) || 'API request failed')
  return r.json()
}

function Badge({ children, level }) { return <span className={`badge ${level || ''}`}>{children}</span> }

function Stat({ icon: Icon, label, value, sub, accent }) {
  return (
    <div className={`stat ${accent || ''}`}>
      <div className="stat-icon"><Icon size={20} /></div>
      <div className="stat-body">
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
        {sub && <div className="stat-sub">{sub}</div>}
      </div>
    </div>
  )
}

function App() {
  const [tab, setTab] = useState('scan');
  const [analysisMode, setAnalysisMode] = useState('full'); // 'full' | 'authenticity' | 'fraud'
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [source, setSource] = useState('Web / Message');
  const [result, setResult] = useState(null);
  const [scans, setScans] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [s, h] = await Promise.all([api('/scans/?limit=10'), api('/stats/')]);
      setScans(s);
      setStats(h);
    } catch (e) {
      setError('Backend is not reachable. Start Django on port 8000.')
    }
  }

  useEffect(() => { load() }, [])

  const run = async () => {
    if (!content.trim()) return;
    setLoading(true);
    setError('');
    try {
      const r = await api('/analyze/', {
        method: 'POST',
        body: JSON.stringify({ title, content, source })
      });
      setResult(r);
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const authStats = stats.authenticity_stats || {};

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo"><ShieldCheck size={26} /></div>
          <div>
            <b>TRUTHGUARD AI</b>
            <span>FRAUD INTELLIGENCE</span>
          </div>
        </div>

        <nav>
          {[
            ['scan', Search, 'ANALYZE'],
            ['history', History, 'HISTORY'],
            ['graph', Network, 'ATTACK GRAPH']
          ].map(([id, IconComponent, label]) => (
            <button
              className={tab === id ? 'active' : ''}
              onClick={() => setTab(id)}
              key={id}
            >
              <IconComponent size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="side-note">
          <div className="side-note-header">
            <LockKeyhole size={16} />
            <b>DUAL INTELLIGENCE</b>
          </div>
          <p>TruthGuard evaluates <strong>Content Authenticity</strong> alongside <strong>Fraud Behavior</strong> to uncover weaponized genuine information.</p>
        </div>

        <div className="version">TRUTHGUARD AI · v2.0</div>
      </aside>

      <main>
        <header>
          <div>
            <div className="eyebrow">TRUTHGUARD AI // FRAUD INTELLIGENCE & CONTENT AUTHENTICITY</div>
            <h1>INTELLIGENCE BEYOND TRUE OR FALSE</h1>
            <p>Investigate whether content is authentic, manipulated, misleading, or weaponized for fraud.</p>
          </div>
          <div className="health">
            <span className="health-pulse"></span>
            DUAL ENGINE ONLINE
          </div>
        </header>

        {/* NEO-BRUTALIST FRAUD & AUTHENTICITY FLOW BANNER */}
        <section className="fraud-banner">
          <div className="banner-title">
            <ShieldAlert size={18} />
            <span>CORE PRINCIPLE: THE INFORMATION CAN BE REAL. THE ACTION CAN STILL BE FRAUD.</span>
          </div>
          <div className="banner-flow">
            <div className="flow-step safe">
              <span className="step-num">01</span>
              <span className="step-text">CONTENT AUTHENTICITY</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step warning">
              <span className="step-num">02</span>
              <span className="step-text">FRAUDULENT CONTEXT ADDED</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step danger">
              <span className="step-num">03</span>
              <span className="step-text">VICTIM TARGETED</span>
            </div>
            <div className="flow-arrow">→</div>
            <div className="flow-step critical">
              <span className="step-num">04</span>
              <span className="step-text">MONEY / DATA LOSS</span>
            </div>
          </div>
        </section>

        {error && <div className="error"><strong>[SYSTEM ERROR]</strong> {error}</div>}

        {tab === 'scan' && (
          <>
            <section className="stats">
              <Stat icon={Activity} label="TOTAL SCANS" value={stats.total_scans || 0} accent="blue" />
              <Stat icon={AlertTriangle} label="HIGH / CRITICAL FRAUD" value={(stats.high || 0) + (stats.critical || 0)} accent="red" />
              <Stat icon={FileCheck2} label="AUTHENTIC CONTENT" value={authStats.genuine || 0} accent="lime" />
              <Stat icon={Scale} label="MANIPULATED / FALSE" value={(authStats.misleading || 0) + (authStats.false || 0)} accent="yellow" />
            </section>

            <section className="workspace">
              <div className="panel input-panel">
                <div className="panel-head">
                  <div>
                    <h2>ANALYZE THE ATTACK & AUTHENTICITY</h2>
                    <p>Paste text, email, link, or call transcript for dual-layer investigation.</p>
                  </div>
                </div>

                <div className="mode-selector">
                  <span className="mode-label">ANALYSIS VIEW FOCUS:</span>
                  <button className={`mode-btn ${analysisMode === 'full' ? 'active' : ''}`} onClick={() => setAnalysisMode('full')}>FULL INTELLIGENCE</button>
                  <button className={`mode-btn ${analysisMode === 'authenticity' ? 'active' : ''}`} onClick={() => setAnalysisMode('authenticity')}>CONTENT AUTHENTICITY</button>
                  <button className={`mode-btn ${analysisMode === 'fraud' ? 'active' : ''}`} onClick={() => setAnalysisMode('fraud')}>FRAUD ANALYSIS</button>
                </div>

                <label>
                  TITLE / CONTEXT
                  <input
                    value={title}
                    onChange={e => setTitle(e.target.value)}
                    placeholder="e.g. Bank verification SMS, Government benefit claim..."
                  />
                </label>

                <label>
                  CHANNEL / SOURCE
                  <select value={source} onChange={e => setSource(e.target.value)}>
                    <option>Web / Message</option>
                    <option>News Article / URL</option>
                    <option>SMS</option>
                    <option>Email</option>
                    <option>WhatsApp</option>
                    <option>Social media</option>
                    <option>Phone / Call notes</option>
                  </select>
                </label>

                <label>
                  CONTENT FOR ANALYSIS
                  <textarea
                    value={content}
                    onChange={e => setContent(e.target.value)}
                    placeholder="Paste suspicious text, link details, or message content here..."
                  />
                </label>

                <button
                  className="analyze"
                  disabled={loading || !content.trim()}
                  onClick={run}
                >
                  {loading ? (
                    <span className="analyzing-text">
                      <Loader2 className="spin" size={20} /> RUNNING DUAL-LAYER INVESTIGATION...
                    </span>
                  ) : (
                    <>
                      <span>RUN TRUTHGUARD ANALYSIS</span>
                      <ArrowRight size={20} />
                    </>
                  )}
                </button>

                {loading && (
                  <div className="loading-sequence">
                    <div className="seq-step done"><CheckCircle2 size={15} /> EXTRACTING CLAIMS & ENTITIES</div>
                    <div className="seq-step done"><CheckCircle2 size={15} /> EVALUATING AUTHORITATIVE EVIDENCE</div>
                    <div className="seq-step active"><Zap size={15} /> CHECKING CONTENT AUTHENTICITY & MANIPULATION</div>
                    <div className="seq-step pending"><span>[ ]</span> ANALYZING FRAUD BEHAVIOR & ATTACK GRAPH</div>
                  </div>
                )}
              </div>

              <Result result={result} mode={analysisMode} />
            </section>
          </>
        )}

        {tab === 'history' && (
          <HistoryView
            scans={scans}
            onOpen={s => {
              setResult({ scan_id: s.id, ...s.analysis });
              setTab('scan');
            }}
          />
        )}

        {tab === 'graph' && <GraphView result={result} />}
      </main>
    </div>
  )
}

function Result({ result, mode }) {
  if (!result) {
    return (
      <div className="panel empty">
        <Network size={54} />
        <h2>WAITING FOR INTELLIGENCE</h2>
        <p>Run a scan to generate Content Authenticity verification, Fraud DNA, risk verdict, and attack graphs.</p>
      </div>
    )
  }

  const r = result;
  const auth = r.content_authenticity || {
    verdict: 'UNVERIFIED',
    status_code: 'unverified',
    confidence: null,
    summary: 'Content analysis pending independent evidence verification.',
    claims: [],
    supporting_evidence: [],
    contradicting_evidence: [],
    manipulated_elements: []
  };

  const severityClass = (r.severity || 'low').toLowerCase();

  const getAuthBadgeLevel = (verdict) => {
    if (verdict.includes('GENUINE')) return 'lime';
    if (verdict.includes('FALSE')) return 'critical';
    if (verdict.includes('MISLEADING') || verdict.includes('MANIPULATED')) return 'medium';
    return 'blue';
  };

  const authLevel = getAuthBadgeLevel(auth.verdict);

  const showAuth = mode === 'full' || mode === 'authenticity';
  const showFraud = mode === 'full' || mode === 'fraud';

  return (
    <div className="panel result-panel">
      {/* TWO-DIMENSION HEADERS */}
      <div className="two-dim-header">
        {showAuth && (
          <div className="dim-card auth-dim">
            <div className="dim-eyebrow">DIMENSION 1: CONTENT AUTHENTICITY</div>
            <div className="dim-title-row">
              <h3>{auth.verdict}</h3>
              <Badge level={authLevel}>AUTHENTICITY</Badge>
            </div>
            <p className="dim-summary">{auth.summary}</p>
            {auth.confidence && (
              <div className="confidence-pill">
                CONFIDENCE SCORE: <strong>{Math.round(auth.confidence * 100)}%</strong>
              </div>
            )}
            {r.source_access && r.source_access.status !== 'NOT_APPLICABLE' && (
              <div className={`source-access-bar ${r.source_access.status.toLowerCase()}`}>
                <div className="source-access-badge-row">
                  <span className="source-access-label">SOURCE ACCESS</span>
                  <Badge level={
                    r.source_access.status === 'ACCESSIBLE' ? 'lime' :
                    r.source_access.status === 'BLOCKED' ? 'medium' :
                    r.source_access.status === 'NOT_FOUND' ? 'medium' :
                    r.source_access.status === 'TIMEOUT' ? 'medium' : 'blue'
                  }>
                    {r.source_access.status}{r.source_access.http_status ? ` — HTTP ${r.source_access.http_status}` : ''}
                  </Badge>
                </div>
                <div className="source-access-msg">
                  {r.source_access.status === 'BLOCKED' ? (
                    'The source could not be retrieved due to access restrictions (e.g. HTTP 403), limiting independent verification. This is an access limitation and does not indicate that the content is false.'
                  ) : r.source_access.status === 'NOT_FOUND' ? (
                    'The requested source URL returned HTTP 404 Not Found, limiting automated extraction.'
                  ) : r.source_access.status === 'TIMEOUT' ? (
                    'The source did not respond within the allowed time, limiting automated extraction.'
                  ) : (
                    r.source_access.message || 'Source access status recorded.'
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {showFraud && (
          <div className={`dim-card fraud-dim ${severityClass}`}>
            <div className="dim-eyebrow">DIMENSION 2: FRAUD RISK & SEVERITY</div>
            <div className="dim-title-row">
              <div className="score-val">
                <strong>{r.risk_score}</strong>
                <span>/100</span>
              </div>
              <Badge level={severityClass}>{r.severity}</Badge>
            </div>
            <div className="verdict-text">{r.verdict}</div>
            <div className="campaign-tag">
              CAMPAIGN FINGERPRINT: <code>{r.campaign_fingerprint || '0000'}</code>
            </div>
          </div>
        )}
      </div>

      {/* CORE INSIGHT BANNER */}
      {showAuth && showFraud && (
        <div className="insight-callout">
          <AlertTriangle size={18} />
          <span>
            {auth.verdict.includes('GENUINE') && (severityClass === 'high' || severityClass === 'critical')
              ? 'WARNING: The underlying information is authentic, but fraudulent context/requests have been attached to victimize users!'
              : 'TRUTHGUARD DUAL VERDICT: Evaluates information truth against weaponized fraud behavior.'}
          </span>
        </div>
      )}

      {/* CONTENT AUTHENTICITY SECTION */}
      {showAuth && (
        <div className="section-block auth-section">
          {/* NEWS LINK & MEDIA OUTLET VERIFICATION */}
          {r.news_verification && r.news_verification.has_news_links && (
            <div className="news-verify-block">
              <h4>NEWS LINK & MEDIA CHANNEL VERIFICATION</h4>
              <div className="news-links-grid">
                {r.news_verification.links.map((link, idx) => (
                  <div className={`news-link-card ${link.is_trusted ? 'trusted' : 'unverified'}`} key={idx}>
                    <div className="news-card-header">
                      <div className="news-channel-info">
                        <Newspaper size={18} />
                        <div>
                          <b className="news-name">{link.source_name}</b>
                          <span className="news-cat">{link.source_category}</span>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        <Badge level={link.is_trusted ? 'lime' : 'blue'}>
                          {link.domain_status.replaceAll('_', ' ')}
                        </Badge>
                        {link.source_access && link.source_access.status !== 'NOT_APPLICABLE' && (
                          <Badge level={link.source_access.status === 'ACCESSIBLE' ? 'lime' : 'medium'}>
                            {link.source_access.status}{link.source_access.http_status ? ` (${link.source_access.http_status})` : ''}
                          </Badge>
                        )}
                      </div>
                    </div>

                    {link.page_title && (
                      <div className="news-headline">
                        <strong>Headline:</strong> {link.page_title}
                      </div>
                    )}

                    {link.extracted_article_snippet && (
                      <div className="news-snippet">
                        <span className="snippet-label">Extracted Article Content:</span>
                        <p>{link.extracted_article_snippet.slice(0, 300)}...</p>
                      </div>
                    )}

                    <div className="news-footer">
                      <a href={link.url} target="_blank" rel="noopener noreferrer" className="news-url-link">
                        <span>{link.domain}</span>
                        <ExternalLink size={12} />
                      </a>
                      <span className="reputation-text">{link.reputation_note}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CLAIMS BREAKDOWN */}
          {auth.claims && auth.claims.length > 0 && (
            <div className="claims-block">
              <h4>CLAIM & INFORMATION BREAKDOWN</h4>
              <div className="claims-grid">
                {auth.claims.map((c, i) => {
                  const isSupp = c.status === 'SUPPORTED';
                  const isContr = c.status === 'CONTRADICTED';
                  const isPart = c.status === 'PARTIALLY_SUPPORTED';

                  return (
                    <div className={`claim-card ${c.status.toLowerCase()}`} key={i}>
                      <div className="claim-header">
                        <span className="claim-icon">
                          {isSupp && <Check size={16} />}
                          {isContr && <X size={16} />}
                          {isPart && <AlertCircle size={16} />}
                          {!isSupp && !isContr && !isPart && <HelpCircle size={16} />}
                        </span>
                        <span className="claim-status">{c.status.replaceAll('_', ' ')}</span>
                      </div>
                      <div className="claim-text">"{c.claim}"</div>
                      <div className="claim-evidence"><strong>Evidence:</strong> {c.evidence}</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* MANIPULATION DETECTION */}
          {auth.manipulated_elements && auth.manipulated_elements.length > 0 && (
            <div className="manipulation-block">
              <h4>MANIPULATION & CONTEXT ATTACHMENT</h4>
              {auth.manipulated_elements.map((m, i) => (
                <div className="manip-card" key={i}>
                  <div className="manip-col original">
                    <span className="manip-label">SUPPORTED ORIGINAL INFO</span>
                    <p>{m.supported_info}</p>
                  </div>
                  <div className="manip-vs">VS</div>
                  <div className="manip-col context">
                    <span className="manip-label">FRAUDULENT / MANIPULATED CONTEXT ADDED</span>
                    <p>{m.manipulated_context}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* EVIDENCE SOURCES */}
          {(auth.supporting_evidence?.length > 0 || auth.contradicting_evidence?.length > 0) && (
            <div className="evidence-block">
              <h4>AUTHORITATIVE EVIDENCE & SOURCES</h4>
              <div className="evidence-grid">
                {[...(auth.supporting_evidence || []), ...(auth.contradicting_evidence || [])].map((ev, i) => (
                  <div className={`evidence-card ${ev.status.toLowerCase()}`} key={i}>
                    <div className="ev-header">
                      <b className="ev-source">{ev.source}</b>
                      <span className="ev-type">{ev.source_type}</span>
                    </div>
                    <div className="ev-rel">{ev.relevance}</div>
                    <Badge level={ev.status === 'SUPPORTS' ? 'lime' : 'critical'}>{ev.status}</Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* FRAUD ANALYSIS SECTION */}
      {showFraud && (
        <div className="section-block fraud-section">
          <h3>FRAUD INTELLIGENCE & INDICATORS</h3>

          <div className="riskbar-container">
            <div className="riskbar-label">
              <span>FRAUD RISK SPECTRUM</span>
              <span>{r.risk_score}%</span>
            </div>
            <div className="riskbar">
              <div className={`riskbar-fill ${severityClass}`} style={{ width: `${r.risk_score}%` }} />
            </div>
          </div>

          <div className="result-grid">
            <div className="dna-section">
              <h3>FRAUD DNA</h3>
              <div className="dna">
                {Object.entries(r.fraud_dna || {}).map(([k, v]) => (
                  <div className={v === true ? 'on' : ''} key={k}>
                    <span className="dna-key">{k.replaceAll('_', ' ')}</span>
                    <span className="dna-val">{v === true ? 'DETECTED' : String(v).toUpperCase()}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="signals-section">
              <h3>FRAUD SIGNALS</h3>
              {r.signals && r.signals.length ? (
                <div className="signals">
                  {r.signals.map((s, i) => (
                    <div className="signal" key={i}>
                      <div>
                        <b>{s.type.replaceAll('_', ' ').toUpperCase()}</b>
                        <small>{s.evidence.join(' · ')}</small>
                      </div>
                      <Badge level="weight">+{s.weight}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted">No strong behavioral risk signals detected.</p>
              )}
            </div>
          </div>

          <div className="lower-grid">
            <div className="graph-section">
              <h3>ATTACK GRAPH</h3>
              <div className="graphline">
                {r.attack_graph && r.attack_graph.length ? (
                  r.attack_graph.map((e, i) => (
                    <div className="node" key={i}>
                      <b className="node-from">{e.from}</b>
                      <div className="node-rel">
                        <span>{e.relation}</span>
                        <ChevronRight size={14} />
                      </div>
                      <b className="node-to">{e.to}</b>
                    </div>
                  ))
                ) : (
                  <p className="muted">No attack chain constructed.</p>
                )}
              </div>
            </div>

            <div className="actions-section">
              <h3>PREVENTION ACTIONS</h3>
              <ul className="actions">
                {(r.prevention_actions || []).map((x, i) => (
                  <li key={i}>
                    <CircleCheck size={18} />
                    <span>{x}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function HistoryView({ scans, onOpen }) {
  return (
    <section className="panel wide">
      <div className="panel-head">
        <div>
          <h2>SCAN HISTORY DOSSIER</h2>
          <p>Recent dual intelligence records stored by the TruthGuard backend engine.</p>
        </div>
      </div>
      <div className="table">
        {scans && scans.length ? (
          scans.map(s => {
            const auth = (s.analysis || {}).get?.('content_authenticity') || (s.analysis || {}).content_authenticity || {};
            const authVerdict = auth.verdict || 'UNVERIFIED';

            return (
              <button className="row" key={s.id} onClick={() => onOpen(s)}>
                <div className="row-main">
                  <b>{s.title || 'Untitled scan'}</b>
                  <small>{new Date(s.created_at).toLocaleString()}</small>
                </div>
                <div className="row-source">{s.source || 'Unknown'}</div>
                <div className="row-auth">
                  <Badge level={authVerdict.includes('GENUINE') ? 'lime' : authVerdict.includes('FALSE') ? 'critical' : 'medium'}>
                    {authVerdict.replace('LIKELY ', '')}
                  </Badge>
                </div>
                <Badge level={(s.severity || 'low').toLowerCase()}>{s.severity}</Badge>
                <strong className="row-score">{s.risk_score}</strong>
                <ChevronRight size={18} />
              </button>
            )
          })
        ) : (
          <div className="empty mini">
            <History size={36} />
            <p>No scans recorded in history yet.</p>
          </div>
        )}
      </div>
    </section>
  )
}

function GraphView({ result }) {
  return (
    <section className="panel wide">
      <div className="panel-head">
        <div>
          <h2>ATTACK GRAPH EXPLORER</h2>
          <p>TruthGuard maps the structural attack sequence from threat actor behavior to victim action and loss destination.</p>
        </div>
      </div>

      {result?.attack_graph?.length ? (
        <div className="biggraph">
          {result.attack_graph.map((e, i) => (
            <div className="graphcard" key={i}>
              <div className="circle">0{i + 1}</div>
              <div className="graphcard-content">
                <div className="node-box from-box">{e.from}</div>
                <div className="rel-pill">{e.relation}</div>
                <div className="node-box to-box">{e.to}</div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="graph-placeholder">
          <Network size={64} />
          <h3>NO ACTIVE ATTACK GRAPH</h3>
          <p>Run an intelligence scan first to generate a full visual attack sequence.</p>
        </div>
      )}
    </section>
  )
}

createRoot(document.getElementById('root')).render(<App />)
