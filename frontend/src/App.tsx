import React, { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { 
  Cpu, DollarSign, Activity, MessageSquare, Send, Zap, 
  RefreshCw, AlertTriangle, Leaf, ArrowRight, Clock, Settings,
  Database, ShieldAlert, Sparkles, Server, FileText, Lock, 
  Unlock, Download, User, X, ChevronRight, CheckCircle, TrendingUp
} from 'lucide-react';

interface GPUClusterNode {
  id: string;
  provider: string;
  region: string;
  gpu_type: string;
  gpu_count: number;
  hourly_cost: number;
  carbon_intensity: number;
  status: string;
}

interface ModelDeployment {
  id: string;
  name: string;
  node_id: string;
  gpu_allocated: number;
  sla_latency_ms: number;
  target_tps: number;
}

interface KPIOverview {
  total_spend_usd: number;
  gpu_idle_cost_penalty_usd: number;
  gpu_idle_cost_penalty_pct: number;
  avg_model_compute_efficiency: number;
  sla_violation_exposure_index: number;
  total_carbon_emitted_kg: number;
  carbon_offset_roi: number;
}

interface TimelineDataPoint {
  timestamp: string;
  gpu_utilization_pct: number;
  power_draw_watts: number;
  hourly_cost_usd: number;
  carbon_emitted_kg: number;
}

interface ModelEfficiencyDataPoint {
  model_id: string;
  model_name: string;
  tokens_per_watt_hour: number;
  avg_latency_ms: number;
  sla_violation_pct: number;
}

interface ProviderMetrics {
  provider: string;
  total_spend_usd: number;
  carbon_emitted_kg: number;
  avg_utilization_pct: number;
}

interface SimulatorResult {
  current_cost_usd: number;
  projected_cost_usd: number;
  current_carbon_kg: number;
  projected_carbon_kg: number;
  current_sla_violation_pct: number;
  projected_sla_violation_pct: number;
  monthly_savings_usd: number;
  net_carbon_saved_kg: number;
}

interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  suggested_actions?: Array<{
    title: string;
    action_type: string;
    impact: string;
  }>;
}

interface Recommendation {
  id: string;
  title: string;
  category: string;
  impact: string;
  metrics: {
    cost_saving_usd: number;
    carbon_saving_kg: number;
    sla_improvement_pct: number;
    efficiency_gain_pct: number;
  };
  explanation: string;
  action_step: string;
}

interface Anomaly {
  timestamp: string;
  type: string;
  target: string;
  severity: string;
  description: string;
  root_cause: string;
  recommended_action: string;
}

interface UserActivityLog {
  id: number;
  timestamp: string;
  username: string;
  action: string;
  ip_address: string;
}

const App: React.FC = () => {
  // Navigation
  const [activeTab, setActiveTab] = useState<'dashboard' | 'executive' | 'anomalies' | 'case_study' | 'admin'>('dashboard');
  
  // Datasets
  const [nodes, setNodes] = useState<GPUClusterNode[]>([]);
  const [deployments, setDeployments] = useState<ModelDeployment[]>([]);
  const [kpis, setKpis] = useState<KPIOverview | null>(null);
  const [timeline, setTimeline] = useState<TimelineDataPoint[]>([]);
  const [models, setModels] = useState<ModelEfficiencyDataPoint[]>([]);
  const [providers, setProviders] = useState<ProviderMetrics[]>([]);
  
  // Secured Datasets (Require JWT)
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [activityLogs, setActivityLogs] = useState<UserActivityLog[]>([]);
  
  // Sizing Simulator State
  const [selectedNode, setSelectedNode] = useState<string>('aws-us-east-1-h100-01');
  const [gpuMultiplier, setGpuMultiplier] = useState<number>(1.0);
  const [activeHours, setActiveHours] = useState<number>(24);
  const [concurrency, setConcurrency] = useState<number>(1.0);
  const [routingStrategy, setRoutingStrategy] = useState<string>('default');
  const [simResult, setSimResult] = useState<SimulatorResult | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);

  // Authentication State
  const [token, setToken] = useState<string | null>(localStorage.getItem('aetherfin_token'));
  const [userRole, setUserRole] = useState<string | null>(localStorage.getItem('aetherfin_role'));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem('aetherfin_email'));
  const [authEmail, setAuthEmail] = useState<string>('admin@aetherfin.com');
  const [authPassword, setAuthPassword] = useState<string>('admin_password_2026');
  const [authError, setAuthError] = useState<string | null>(null);
  const [isRegister, setIsRegister] = useState<boolean>(false);

  // Drill-Down Modal State
  const [drillDownMetric, setDrillDownMetric] = useState<'spend' | 'gicp' | 'mces' | 'coroi' | null>(null);

  // Chat Advisor State
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    {
      sender: 'ai',
      text: `### AetherFin Strategic Advisor Initialized.
How can I assist you with your GPU cluster strategy today?
Click one of the quick options below, or type your own inquiry.`,
      suggested_actions: [
        { title: "How can I reduce costs by 20%?", action_type: "scale", impact: "Savings analysis" },
        { title: "Which nodes should be optimized?", action_type: "decommission", impact: "Scan idle nodes" }
      ]
    }
  ]);
  const [chatInput, setChatInput] = useState<string>('');
  const [sendingChat, setSendingChat] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  // Load standard data
  const fetchData = async () => {
    try {
      setLoading(true);
      const [nodesRes, depRes, kpiRes, timelineRes, modelsRes, provRes] = await Promise.all([
        fetch('/api/nodes').then(r => r.json()),
        fetch('/api/deployments').then(r => r.json()),
        fetch('/api/kpi-overview').then(r => r.json()),
        fetch('/api/charts/timeline').then(r => r.json()),
        fetch('/api/charts/models').then(r => r.json()),
        fetch('/api/charts/providers').then(r => r.json())
      ]);

      setNodes(nodesRes);
      setDeployments(depRes);
      setKpis(kpiRes);
      setTimeline(timelineRes);
      setModels(modelsRes);
      setProviders(provRes);
      
      if (nodesRes.length > 0) {
        setSelectedNode(nodesRes[0].id);
      }
    } catch (e) {
      console.error("Error loading AetherFin metrics:", e);
    } finally {
      setLoading(false);
    }
  };

  // Load secured data if token is active
  const fetchSecuredData = async () => {
    if (!token) return;
    try {
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const recsRes = await fetch('/api/recommendations', { headers }).then(r => r.ok ? r.json() : []);
      setRecommendations(recsRes);

      const anomsRes = await fetch('/api/anomalies', { headers }).then(r => r.ok ? r.json() : []);
      setAnomalies(anomsRes);

      if (userRole === 'Admin') {
        const logsRes = await fetch('/api/admin/activity-logs', { headers }).then(r => r.ok ? r.json() : []);
        setActivityLogs(logsRes);
      }
    } catch (e) {
      console.error("Error loading secured metrics:", e);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (token) {
      fetchSecuredData();
    } else {
      setRecommendations([]);
      setAnomalies([]);
      setActivityLogs([]);
    }
  }, [token]);

  // Sizing Simulation loop
  useEffect(() => {
    if (selectedNode) {
      triggerSimulation();
    }
  }, [selectedNode, gpuMultiplier, activeHours, concurrency, routingStrategy]);

  const triggerSimulation = async () => {
    setSimulating(true);
    try {
      const res = await fetch('/api/simulator', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          node_id: selectedNode,
          gpu_count_multiplier: gpuMultiplier,
          active_hours_per_day: activeHours,
          target_model_concurrency: concurrency,
          routing_strategy: routingStrategy
        })
      });
      const data = await res.json();
      setSimResult(data);
    } catch (e) {
      console.error("Simulation failed:", e);
    } finally {
      setSimulating(false);
    }
  };

  // Login handler
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    const path = isRegister ? "/api/auth/register" : "/api/auth/login";
    const body = isRegister 
      ? { email: authEmail, password: authPassword, role: authEmail.includes("admin") ? "Admin" : "User" }
      : { email: authEmail, password: authPassword };

    try {
      const res = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed");
      }

      if (isRegister) {
        setIsRegister(false);
        alert("Registration successful! Please login.");
      } else {
        localStorage.setItem('aetherfin_token', data.access_token);
        localStorage.setItem('aetherfin_role', data.role);
        localStorage.setItem('aetherfin_email', data.email);
        setToken(data.access_token);
        setUserRole(data.role);
        setUserEmail(data.email);
        setActiveTab('dashboard');
      }
    } catch (err: any) {
      setAuthError(err.message);
    }
  };

  // Logout handler
  const handleLogout = () => {
    localStorage.removeItem('aetherfin_token');
    localStorage.removeItem('aetherfin_role');
    localStorage.removeItem('aetherfin_email');
    setToken(null);
    setUserRole(null);
    setUserEmail(null);
    setActiveTab('dashboard');
  };

  // AI chat advisor submit
  const handleSendChat = async (messageText: string) => {
    if (!messageText.trim()) return;
    setSendingChat(true);
    setChatInput('');
    setChatHistory(prev => [...prev, { sender: 'user', text: messageText }]);

    try {
      const res = await fetch('/api/chat-advisor', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText })
      });
      const data = await res.json();
      setChatHistory(prev => [...prev, { 
        sender: 'ai', 
        text: data.response, 
        suggested_actions: data.suggested_actions 
      }]);
    } catch (e) {
      setChatHistory(prev => [...prev, { sender: 'ai', text: "**Error communicating with advisor.**" }]);
    } finally {
      setSendingChat(false);
    }
  };

  // Export helper
  const triggerExport = (dataset: string, format: string) => {
    if (!token) {
      alert("Please login via the Admin tab to authorize data reports download.");
      setActiveTab('admin');
      return;
    }
    window.open(`/api/reports/export?dataset=${dataset}&format=${format}&token=${token}`);
  };

  // Charts
  const getTimelineOption = () => {
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0c0c0f',
        borderColor: '#1e1e24',
        textStyle: { color: '#fafafa' }
      },
      legend: {
        data: ['GPU Utilization (%)', 'Power Draw (W)'],
        textStyle: { color: '#a1a1aa', fontFamily: 'Outfit' },
        bottom: 0
      },
      grid: { top: '8%', left: '4%', right: '4%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: timeline.map(t => t.timestamp),
        axisLine: { lineStyle: { color: '#1e1e24' } },
        axisLabel: { color: '#71717a', fontFamily: 'Outfit' }
      },
      yAxis: [
        {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { formatter: '{value} %', color: '#71717a' },
          splitLine: { lineStyle: { color: '#1e1e24' } }
        },
        {
          type: 'value',
          axisLabel: { formatter: '{value} W', color: '#71717a' },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'GPU Utilization (%)',
          type: 'line',
          smooth: true,
          showSymbol: false,
          color: '#3b82f6',
          data: timeline.map(t => t.gpu_utilization_pct)
        },
        {
          name: 'Power Draw (W)',
          type: 'line',
          smooth: true,
          showSymbol: false,
          yAxisIndex: 1,
          color: '#f59e0b',
          data: timeline.map(t => t.power_draw_watts)
        }
      ]
    };
  };

  const getModelOption = () => {
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#0c0c0f',
        borderColor: '#1e1e24',
        textStyle: { color: '#fafafa' }
      },
      legend: {
        data: ['Efficiency (Tokens / Wh)', 'SLA Breach Rate (%)'],
        textStyle: { color: '#a1a1aa', fontFamily: 'Outfit' },
        bottom: 0
      },
      grid: { top: '8%', left: '4%', right: '4%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: models.map(m => m.model_name),
        axisLine: { lineStyle: { color: '#1e1e24' } },
        axisLabel: { color: '#71717a', fontFamily: 'Outfit' }
      },
      yAxis: [
        {
          type: 'value',
          axisLabel: { color: '#71717a' },
          splitLine: { lineStyle: { color: '#1e1e24' } }
        },
        {
          type: 'value',
          min: 0,
          max: 100,
          axisLabel: { formatter: '{value}%', color: '#71717a' },
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: 'Efficiency (Tokens / Wh)',
          type: 'bar',
          barWidth: '30%',
          color: '#10b981',
          data: models.map(m => m.tokens_per_watt_hour)
        },
        {
          name: 'SLA Breach Rate (%)',
          type: 'line',
          yAxisIndex: 1,
          color: '#ef4444',
          data: models.map(m => m.sla_violation_pct)
        }
      ]
    };
  };

  return (
    <div className="app-container">
      {/* Top Header */}
      <div className="header">
        <div className="brand-section">
          <Cpu className="logo-icon" size={32} />
          <div>
            <h1 className="brand-title">AetherFin GPU Ops</h1>
            <p className="brand-subtitle">GenAI FinOps & Carbon Intelligence Product</p>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="segmented-control" style={{ margin: 0 }}>
          <button className={`segmented-btn ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            Dashboard
          </button>
          <button className={`segmented-btn ${activeTab === 'executive' ? 'active' : ''}`} onClick={() => setActiveTab('executive')}>
            Executive Summary
          </button>
          <button className={`segmented-btn ${activeTab === 'anomalies' ? 'active' : ''}`} onClick={() => setActiveTab('anomalies')}>
            Anomaly Audit {anomalies.length > 0 && <span className="trend-pill trend-down" style={{ marginLeft: 6, padding: '1px 5px' }}>{anomalies.length}</span>}
          </button>
          <button className={`segmented-btn ${activeTab === 'case_study' ? 'active' : ''}`} onClick={() => setActiveTab('case_study')}>
            Case Study
          </button>
          <button className={`segmented-btn ${activeTab === 'admin' ? 'active' : ''}`} onClick={() => setActiveTab('admin')}>
            {token ? <Unlock size={13} style={{ display: 'inline', marginRight: 5, color: '#10b981' }} /> : <Lock size={13} style={{ display: 'inline', marginRight: 5 }} />}
            Security Logs
          </button>
        </div>

        {/* User Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {token ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="node-pill" style={{ color: '#10b981', fontWeight: 600 }}>{userRole}</span>
              <span className="text-secondary" style={{ fontSize: '0.8rem' }}>{userEmail}</span>
              <button className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }} onClick={handleLogout}>
                Logout
              </button>
            </div>
          ) : (
            <button className="btn btn-primary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }} onClick={() => setActiveTab('admin')}>
              <Lock size={12} /> Login
            </button>
          )}
        </div>
      </div>

      {loading && !kpis ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
          <div className="spinner" style={{ width: '40px', height: '40px', borderWidth: '3px' }}></div>
        </div>
      ) : (
        <>
          {/* Actionable KPIs Row */}
          <div className="kpi-grid">
            <div className="kpi-card" onClick={() => setDrillDownMetric('spend')} style={{ cursor: 'pointer' }}>
              <div className="kpi-header">
                <span>Total Compute Spend</span>
                <DollarSign size={16} style={{ color: '#a1a1aa' }} />
              </div>
              <div className="kpi-value">${kpis?.total_spend_usd.toLocaleString()}</div>
              <div className="kpi-footer">
                <span className="text-secondary">Click for historical factors</span>
                <ChevronRight size={14} style={{ marginLeft: 'auto', color: '#71717a' }} />
              </div>
            </div>

            <div className="kpi-card" onClick={() => setDrillDownMetric('gicp')} style={{ cursor: 'pointer' }}>
              <div className="kpi-header">
                <span>GPU Idle Penalty (GICP)</span>
                <AlertTriangle size={16} style={{ color: '#ef4444' }} />
              </div>
              <div className="kpi-value">${kpis?.gpu_idle_cost_penalty_usd.toLocaleString()}</div>
              <div className="kpi-footer">
                <span className="trend-pill trend-down">{kpis?.gpu_idle_cost_penalty_pct}% waste</span>
                <ChevronRight size={14} style={{ marginLeft: 'auto', color: '#71717a' }} />
              </div>
            </div>

            <div className="kpi-card" onClick={() => setDrillDownMetric('mces')} style={{ cursor: 'pointer' }}>
              <div className="kpi-header">
                <span>Compute Efficiency (MCES)</span>
                <Activity size={16} style={{ color: '#10b981' }} />
              </div>
              <div className="kpi-value font-mono">{kpis?.avg_model_compute_efficiency.toFixed(4)}</div>
              <div className="kpi-footer">
                <span className="text-secondary">Tokens / Watt-hour</span>
                <ChevronRight size={14} style={{ marginLeft: 'auto', color: '#71717a' }} />
              </div>
            </div>

            <div className="kpi-card" onClick={() => setDrillDownMetric('coroi')} style={{ cursor: 'pointer' }}>
              <div className="kpi-header">
                <span>Green Intensity Offset (COROI)</span>
                <Leaf size={16} style={{ color: '#10b981' }} />
              </div>
              <div className="kpi-value">{kpis?.carbon_offset_roi}%</div>
              <div className="kpi-footer">
                <span className="trend-pill trend-up" style={{ fontSize: '0.7rem' }}>{kpis?.total_carbon_emitted_kg.toFixed(0)} kg CO2</span>
                <ChevronRight size={14} style={{ marginLeft: 'auto', color: '#71717a' }} />
              </div>
            </div>
          </div>

          {/* Drill-down Sliding Side Panel */}
          {drillDownMetric && (
            <div style={{
              position: 'fixed', top: 0, right: 0, width: '450px', height: '100vh',
              backgroundColor: '#0c0c0f', borderLeft: '1px solid #1e1e24', zIndex: 999,
              boxShadow: '-10px 0 30px rgba(0,0,0,0.5)', padding: '2rem', display: 'flex', flexDirection: 'column'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h3 className="brand-title" style={{ fontSize: '1.25rem' }}>
                  {drillDownMetric === 'spend' && 'Spend Drill-Down Details'}
                  {drillDownMetric === 'gicp' && 'GICP Idle Waste Analysis'}
                  {drillDownMetric === 'mces' && 'Tokens Efficiency Breakdown'}
                  {drillDownMetric === 'coroi' && 'Offset ROI & Carbon intensity'}
                </h3>
                <button className="btn btn-secondary" style={{ padding: '0.4rem' }} onClick={() => setDrillDownMetric(null)}>
                  <X size={16} />
                </button>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                {drillDownMetric === 'spend' && (
                  <>
                    <p className="text-secondary">Total computed cluster cost across all providers (AWS, GCP, On-Prem). Spend is driven by node hour operations multiplied by hardware classification hourly costs.</p>
                    <div className="sim-results">
                      <div className="sim-row"><span>AWS spend</span><span className="font-mono">$5,562.90</span></div>
                      <div className="sim-row"><span>GCP spend</span><span className="font-mono">$1,512.00</span></div>
                      <div className="sim-row"><span>On-Prem spend</span><span className="font-mono">$770.08</span></div>
                    </div>
                    <div className="sim-saving-badge">💡 Recommendation: Enable Off-Peak Auto-Scaling to reduce spend by 18.4%.</div>
                  </>
                )}

                {drillDownMetric === 'gicp' && (
                  <>
                    <p className="text-secondary">GPU Idle Cost Penalty captures cluster waste: hours where nodes are allocated and drawing power, but mean GPU load remains below 15%.</p>
                    <div className="sim-results">
                      <div className="sim-row"><span>Wasted Idle Spend</span><span className="font-mono">${kpis?.gpu_idle_cost_penalty_usd}</span></div>
                      <div className="sim-row"><span>Total Nodes Logged</span><span className="font-mono">5 nodes</span></div>
                      <div className="sim-row"><span>Critical Idle Node</span><span className="font-mono" style={{ color: '#ef4444' }}>aws-us-east-1-a100-idle</span></div>
                    </div>
                    <div className="sim-saving-badge">💡 Recommendation: Decommission 'aws-us-east-1-a100-idle' to save $2,284/week.</div>
                  </>
                )}

                {drillDownMetric === 'mces' && (
                  <>
                    <p className="text-secondary">Model Compute Efficiency Score checks the number of output and input tokens processed per Joule of energy (Wh) consumed at the node cluster level.</p>
                    <div className="sim-results">
                      <div className="sim-row"><span>Llama-3-8B (GCP L4)</span><span className="font-mono">8.42 tokens/Wh</span></div>
                      <div className="sim-row"><span>Mixtral-8x7B (GCP A100)</span><span className="font-mono">1.94 tokens/Wh</span></div>
                      <div className="sim-row"><span>Llama-3-70B (AWS H100)</span><span className="font-mono">1.12 tokens/Wh</span></div>
                    </div>
                    <div className="sim-saving-badge">💡 Recommendation: Migrate minor Llama-3-70B workloads to the Llama-3-8B endpoint on GCP L4.</div>
                  </>
                )}

                {drillDownMetric === 'coroi' && (
                  <>
                    <p className="text-secondary">Carbon offset efficiency index. Evaluates regional electricity grid clean factors relative to hardware power utilization profiles.</p>
                    <div className="sim-results">
                      <div className="sim-row"><span>Grid Power Consumed</span><span className="font-mono">1,123.4 kWh</span></div>
                      <div className="sim-row"><span>Carbon Emitted</span><span className="font-mono">{kpis?.total_carbon_emitted_kg} kg CO2</span></div>
                      <div className="sim-row"><span>Offset Cost ($20/ton)</span><span className="font-mono">${(kpis ? kpis.total_carbon_emitted_kg * 0.02 : 0.0).toFixed(2)}</span></div>
                    </div>
                    <div className="sim-saving-badge">💡 Recommendation: Reroute Stable-Diffusion XL batches to Europe-West1 clean grid.</div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* TAB 1: SYSTEM DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div className="dashboard-body">
              {/* Left Main Charts */}
              <div className="main-column">
                {/* Nodes Table */}
                <div className="card">
                  <h3 className="card-title">
                    <Server size={18} />
                    Cluster Node Infrastructure
                    <span className="card-title-secondary">{nodes.length} Configured Nodes</span>
                  </h3>
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Node ID</th>
                          <th>Provider</th>
                          <th>GPU Type</th>
                          <th>Size</th>
                          <th>Hourly Cost</th>
                          <th>Grid Intensity</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {nodes.map(node => (
                          <tr key={node.id}>
                            <td><span className="font-mono node-pill">{node.id}</span></td>
                            <td>
                              <span style={{ 
                                color: node.provider === 'AWS' ? '#f59e0b' : node.provider === 'GCP' ? '#3b82f6' : '#10b981',
                                fontWeight: 600
                              }}>{node.provider}</span>
                              <span style={{ color: '#71717a', fontSize: '0.75rem', marginLeft: '0.4rem' }}>
                                ({node.region})
                              </span>
                            </td>
                            <td style={{ color: '#fafafa', fontWeight: 500 }}>{node.gpu_type}</td>
                            <td>{node.gpu_count}x GPUs</td>
                            <td className="font-mono">${node.hourly_cost.toFixed(2)}/hr</td>
                            <td className="font-mono">{node.carbon_intensity} g/kWh</td>
                            <td>
                              <span className={`badge ${node.status === 'Active' ? 'badge-active' : 'badge-idle'}`}>
                                {node.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Utilization Chart */}
                <div className="card">
                  <h3 className="card-title"><Activity size={18} /> Compute Power & Utilization (Last 48 Hours)</h3>
                  <div style={{ height: '320px' }}>
                    {timeline.length > 0 && <ReactECharts option={getTimelineOption()} style={{ height: '100%' }} />}
                  </div>
                </div>

                {/* Model Efficiency Chart */}
                <div className="card">
                  <h3 className="card-title"><Zap size={18} /> Model Compute Efficiency vs SLA Breaches</h3>
                  <div style={{ height: '320px' }}>
                    {models.length > 0 && <ReactECharts option={getModelOption()} style={{ height: '100%' }} />}
                  </div>
                </div>
              </div>

              {/* Right Simulator & Advisor */}
              <div className="side-column">
                {/* Simulator */}
                <div className="card">
                  <h3 className="card-title"><Settings size={18} /> What-If Sizing Simulator</h3>
                  
                  <div className="form-group">
                    <label>Target Node for Optimization</label>
                    <select className="input-select" value={selectedNode} onChange={(e) => setSelectedNode(e.target.value)}>
                      {nodes.map(n => <option key={n.id} value={n.id}>{n.id}</option>)}
                    </select>
                  </div>

                  <div className="slider-group">
                    <div className="slider-header">
                      <span>Node Scale Multiplier</span>
                      <span className="slider-val">{gpuMultiplier}x</span>
                    </div>
                    <input type="range" min="0.25" max="4.0" step="0.25" value={gpuMultiplier} onChange={(e) => setGpuMultiplier(parseFloat(e.target.value))} />
                  </div>

                  <div className="slider-group">
                    <div className="slider-header">
                      <span>Hours of Operation/Day</span>
                      <span className="slider-val">{activeHours} hrs</span>
                    </div>
                    <input type="range" min="1" max="24" step="1" value={activeHours} onChange={(e) => setActiveHours(parseInt(e.target.value))} />
                  </div>

                  <div className="slider-group">
                    <div className="slider-header">
                      <span>Traffic Concurrency multiplier</span>
                      <span className="slider-val">{concurrency}x</span>
                    </div>
                    <input type="range" min="0.5" max="3.0" step="0.1" value={concurrency} onChange={(e) => setConcurrency(parseFloat(e.target.value))} />
                  </div>

                  <div className="form-group">
                    <label>Routing Strategy</label>
                    <select className="input-select" value={routingStrategy} onChange={(e) => setRoutingStrategy(e.target.value)}>
                      <option value="default">Default Round-Robin</option>
                      <option value="cost-optimized">Cost-Optimized (Cheaper node shift)</option>
                      <option value="carbon-optimized">Carbon-Optimized (Clean region route)</option>
                    </select>
                  </div>

                  {simulating && !simResult ? (
                    <div style={{ display: 'flex', justifyContent: 'center', margin: '1rem 0' }}><div className="spinner"></div></div>
                  ) : simResult ? (
                    <div className="sim-results">
                      <div className="sim-row"><span>Projected Cost:</span><span className="font-mono">${simResult.projected_cost_usd.toLocaleString()}</span></div>
                      <div className="sim-row"><span>Projected Carbon:</span><span className="font-mono">{simResult.projected_carbon_kg.toFixed(0)} kg</span></div>
                      <div className="sim-row"><span>Projected SLA breaches:</span><span className="font-mono">{simResult.projected_sla_violation_pct}%</span></div>
                      {simResult.monthly_savings_usd > 0 ? (
                        <div className="sim-saving-badge">Projected Monthly Savings: ${simResult.monthly_savings_usd.toLocaleString()}</div>
                      ) : (
                        <div className="sim-saving-badge" style={{ backgroundColor: 'rgba(239,68,68,0.1)', color: 'var(--error)', borderColor: 'rgba(239,68,68,0.2)' }}>
                          Net Cost Increase: ${Math.abs(simResult.monthly_savings_usd).toLocaleString()}/mo
                        </div>
                      )}
                    </div>
                  ) : null}
                </div>

                {/* AI Chat Advisor */}
                <div className="card">
                  <h3 className="card-title"><MessageSquare size={18} /> FinOps AI Advisor</h3>
                  <div className="chat-container">
                    <div className="chat-messages">
                      {chatHistory.map((chat, idx) => (
                        <div key={idx} className={`chat-bubble ${chat.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}`}>
                          {chat.text.startsWith('###') || chat.text.startsWith('*') ? (
                            <div dangerouslySetInnerHTML={{ 
                              __html: chat.text
                                .replace(/^### (.*$)/gim, '<h4 style="color:#ffffff;margin:0.5rem 0 0.25rem 0">$1</h4>')
                                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                                .replace(/^\* (.*$)/gim, '<li style="margin-left: 1rem">$1</li>')
                            }} />
                          ) : (
                            chat.text
                          )}
                          {chat.suggested_actions && chat.suggested_actions.map((act, sidx) => (
                            <div key={sidx} className="action-chip" style={{ marginTop: '0.4rem' }} onClick={() => handleSendChat(act.title)}>
                              <span>{act.title}</span>
                              <span className="action-impact">{act.impact}</span>
                            </div>
                          ))}
                        </div>
                      ))}
                      {sendingChat && <div className="chat-bubble chat-bubble-ai"><div className="spinner" style={{ marginRight: 6 }}></div>Advisor scanning logs...</div>}
                    </div>

                    <form className="chat-input-row" onSubmit={(e) => { e.preventDefault(); handleSendChat(chatInput); }}>
                      <input type="text" className="chat-input" placeholder="Ask AetherFin Advisor..." value={chatInput} onChange={(e) => setChatInput(e.target.value)} disabled={sendingChat} />
                      <button className="btn btn-primary" type="submit" disabled={sendingChat || !chatInput.trim()}>Send</button>
                    </form>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: EXECUTIVE SUMMARY & ROI */}
          {activeTab === 'executive' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {/* Executive Summary Header */}
              <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h2 className="brand-title" style={{ fontSize: '1.5rem' }}>Executive Summary & Business Impact</h2>
                  <p className="text-secondary">Top actionable recommendations, current vs optimized sizing comparisons, and ROI savings projections.</p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn btn-secondary" onClick={() => triggerExport("kpis", "csv")}>
                    <Download size={14} /> Export KPIs (CSV)
                  </button>
                  <button className="btn btn-primary" onClick={() => triggerExport("executive-report", "text")}>
                    <FileText size={14} /> Download Markdown Report
                  </button>
                </div>
              </div>

              {/* Security Banner if guest */}
              {!token && (
                <div className="card" style={{ borderLeft: '4px solid var(--warning)', backgroundColor: 'var(--warning-bg)' }}>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <ShieldAlert style={{ color: 'var(--warning)' }} />
                    <div>
                      <h4 style={{ color: '#fafafa', fontWeight: 600 }}>Guest Mode Active</h4>
                      <p className="text-secondary" style={{ fontSize: '0.8rem' }}>Executive recommendations are locked. Please login via the <strong>Security Logs</strong> tab to authenticate.</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Recommendations grid */}
              {token && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <h3 className="brand-title" style={{ fontSize: '1.2rem', marginTop: '0.5rem' }}>
                    <Sparkles size={18} style={{ display: 'inline', marginRight: 8, color: '#10b981' }} />
                    Top actionable recommendations
                  </h3>
                  
                  {recommendations.length === 0 ? (
                    <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                      <div className="spinner" style={{ marginBottom: 12 }}></div>
                      <p className="text-secondary">Generating executive recommendations...</p>
                    </div>
                  ) : (
                    recommendations.map((rec, idx) => (
                      <div key={rec.id} className="card" style={{ position: 'relative', borderLeft: `4px solid ${idx < 2 ? '#ef4444' : '#3b82f6'}` }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                          <h4 style={{ color: '#fafafa', fontWeight: 700, fontSize: '1.05rem' }}>[{idx + 1}] {rec.title}</h4>
                          <span className="trend-pill trend-up" style={{ backgroundColor: 'var(--success-bg)', color: 'var(--success)', fontWeight: 700 }}>
                            {rec.impact}
                          </span>
                        </div>
                        <p className="text-secondary" style={{ marginBottom: '0.75rem', fontSize: '0.85rem' }}>{rec.explanation}</p>
                        
                        <div style={{ display: 'flex', gap: '1.5rem', margin: '0.75rem 0', padding: '0.5rem 0', borderTop: '1px solid #1e1e24', borderBottom: '1px solid #1e1e24' }}>
                          <div style={{ fontSize: '0.8rem' }}>
                            <span style={{ color: '#71717a' }}>Cost Saving: </span>
                            <strong style={{ color: '#10b981' }}>${rec.metrics.cost_saving_usd.toLocaleString()}/wk</strong>
                          </div>
                          <div style={{ fontSize: '0.8rem' }}>
                            <span style={{ color: '#71717a' }}>Carbon Avoided: </span>
                            <strong style={{ color: '#10b981' }}>{rec.metrics.carbon_saving_kg} kg CO2/wk</strong>
                          </div>
                          {rec.metrics.sla_improvement_pct !== 0 && (
                            <div style={{ fontSize: '0.8rem' }}>
                              <span style={{ color: '#71717a' }}>SLA Impact: </span>
                              <strong style={{ color: rec.metrics.sla_improvement_pct > 0 ? '#10b981' : '#ef4444' }}>
                                {rec.metrics.sla_improvement_pct > 0 ? `+${rec.metrics.sla_improvement_pct}` : rec.metrics.sla_improvement_pct}%
                              </strong>
                            </div>
                          )}
                        </div>
                        
                        <p style={{ fontSize: '0.8rem', color: '#3b82f6', fontWeight: 500 }}>
                          🎯 Action Step: {rec.action_step}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* ROI & Current vs Optimized state card */}
              <div className="card">
                <h3 className="card-title">
                  <TrendingUp size={18} />
                  Corporate ROI Sizing Projections
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginTop: '1rem' }}>
                  <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.03)', border: '1px solid rgba(239, 68, 68, 0.1)', padding: '1.25rem', borderRadius: '8px' }}>
                    <h4 style={{ color: '#ef4444', fontWeight: 600, marginBottom: '0.75rem' }}>Current Infrastructure Baseline</h4>
                    <ul style={{ listStyleType: 'none', paddingLeft: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <li>Weekly Run Rate Spend: <strong style={{ color: '#fafafa' }}>$7,844.98</strong></li>
                      <li>Idle Wasted Spend (GICP): <strong style={{ color: '#ef4444' }}>$5,073.76</strong></li>
                      <li>Weekly Carbon Emissions: <strong style={{ color: '#fafafa' }}>467.3 kg CO2</strong></li>
                      <li>SLA Violation Exposure Index: <strong style={{ color: '#ef4444' }}>2.89</strong></li>
                    </ul>
                  </div>

                  <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.03)', border: '1px solid rgba(16, 185, 129, 0.1)', padding: '1.25rem', borderRadius: '8px' }}>
                    <h4 style={{ color: '#10b981', fontWeight: 600, marginBottom: '0.75rem' }}>Optimized Infrastructure State</h4>
                    <ul style={{ listStyleType: 'none', paddingLeft: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
                      <li>Projected Spend: <strong style={{ color: '#fafafa' }}>$3,923.40</strong></li>
                      <li>Projected Wasted Spend: <strong style={{ color: '#10b981' }}>$342.20</strong></li>
                      <li>Projected Emissions: <strong style={{ color: '#10b981' }}>124.2 kg CO2</strong></li>
                      <li>Projected SLA Exposure: <strong style={{ color: '#10b981' }}>0.40</strong></li>
                    </ul>
                  </div>
                </div>

                <div className="sim-saving-badge" style={{ marginTop: '1.25rem', padding: '1rem', fontSize: '1rem' }}>
                  📈 Net Sizing Business Outcome: Save $3,921.58 / week ($16,980 monthly savings, 50.0% cost reduction, 73.4% carbon reduction)
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: ANOMALY AUDIT CENTER */}
          {activeTab === 'anomalies' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div className="card">
                <h2 className="brand-title" style={{ fontSize: '1.5rem' }}>Anomaly Detection System</h2>
                <p className="text-secondary">Detects system deviations and outliers using historical z-score statistical latency auditing.</p>
              </div>

              {!token && (
                <div className="card" style={{ borderLeft: '4px solid var(--warning)', backgroundColor: 'var(--warning-bg)' }}>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <ShieldAlert style={{ color: 'var(--warning)' }} />
                    <div>
                      <h4 style={{ color: '#fafafa', fontWeight: 600 }}>Guest Mode Active</h4>
                      <p className="text-secondary" style={{ fontSize: '0.8rem' }}>Detailed anomalies are locked. Please login via the <strong>Security Logs</strong> tab to authenticate.</p>
                    </div>
                  </div>
                </div>
              )}

              {token && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {anomalies.length === 0 ? (
                    <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                      <CheckCircle size={32} style={{ color: '#10b981', marginBottom: '0.75rem', display: 'inline' }} />
                      <p style={{ color: '#fafafa', fontWeight: 600 }}>Zero active anomalies detected in the past 24 hours.</p>
                      <p className="text-secondary" style={{ fontSize: '0.8rem' }}>Check again during peak cluster load hours.</p>
                    </div>
                  ) : (
                    anomalies.map((anom, idx) => (
                      <div key={idx} className="card" style={{ borderLeft: `4px solid ${anom.severity === 'High' ? '#ef4444' : '#f59e0b'}` }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <span style={{ color: '#71717a', fontSize: '0.75rem' }}>{anom.timestamp}</span>
                          <span className={`badge ${anom.severity === 'High' ? 'badge-idle' : 'badge-maintenance'}`}>
                            {anom.severity} Severity
                          </span>
                        </div>
                        <h4 style={{ color: '#fafafa', fontWeight: 700, fontSize: '1rem', marginBottom: '0.5rem' }}>
                          [{anom.type}] {anom.target}
                        </h4>
                        <p className="text-secondary" style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>{anom.description}</p>
                        <div style={{ backgroundColor: 'rgba(255,255,255,0.02)', padding: '0.5rem 0.75rem', borderRadius: '4px', fontSize: '0.8rem', border: '1px solid #1e1e24', marginBottom: '0.5rem' }}>
                          <strong>Root Cause</strong>: {anom.root_cause}
                        </div>
                        <p style={{ color: '#3b82f6', fontSize: '0.8rem', fontWeight: 500 }}>
                          💡 Recommended Action: {anom.recommended_action}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: PRODUCT ANALYTICS CASE STUDY */}
          {activeTab === 'case_study' && (
            <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', lineHeight: 1.7 }}>
              <h2 className="brand-title" style={{ fontSize: '1.75rem', letterSpacing: '-0.02em', borderBottom: '1px solid #1e1e24', paddingBottom: '0.75rem' }}>
                Product Case Study: AetherFin Analytical Framework
              </h2>
              
              <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '2rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div>
                    <h3 style={{ color: '#ffffff', fontWeight: 700, fontSize: '1.2rem', marginBottom: '0.5rem' }}>1. Problem Statement</h3>
                    <p className="text-secondary" style={{ fontSize: '0.9rem' }}>
                      In 2026, corporate GPU infrastructure costs represent a top-tier operational expense. However, standard system administration tools only measure raw cluster parameters (like CPU % or memory bytes), completely missing the link to LLM operational waste, model serving SLA latency violations, and the company's carbon sustainability footprint.
                    </p>
                  </div>

                  <div>
                    <h3 style={{ color: '#ffffff', fontWeight: 700, fontSize: '1.2rem', marginBottom: '0.5rem' }}>2. Business Challenges</h3>
                    <ul style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', paddingLeft: '1.25rem' }}>
                      <li><strong>Idle Resource Leakage</strong>: Costly H100 GPU clusters remain allocated 24/7 during off-peak hours with zero workload.</li>
                      <li><strong>SLA Penalties</strong>: Diurnal request concurrency spikes cause queuing, triggering target latency violations for production users.</li>
                      <li><strong>Grid Sustainability</strong>: Companies are increasingly mandated to monitor green indicators, but have no way to measure carbon coefficients relative to cloud node placement.</li>
                    </ul>
                  </div>

                  <div>
                    <h3 style={{ color: '#ffffff', fontWeight: 700, fontSize: '1.2rem', marginBottom: '0.5rem' }}>3. The Solution: Custom Index Metrics</h3>
                    <p className="text-secondary" style={{ fontSize: '0.9rem' }}>
                      AetherFin bridges the gap by implementing four novel business indexes:
                    </p>
                    <ul style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', paddingLeft: '1.25rem', marginTop: '0.5rem' }}>
                      <li><strong>GICP (GPU Idle Penalty)</strong>: Multiplies node costs by the duration of low utilization state, highlighting raw financial leaks.</li>
                      <li><strong>MCES (Compute Efficiency)</strong>: Measures output tokens per Wh, tracking structural model serving performance.</li>
                      <li><strong>SLA-VEI (SLA Violation Index)</strong>: Weights SLA failures non-linearly by latency breach severity, reflecting actual user frustration.</li>
                      <li><strong>COROI (Carbon Offset ROI)</strong>: Tracks carbon offsets cost-efficiency by balancing regional grid carbon factors.</li>
                    </ul>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.03)', border: '1px solid rgba(59, 130, 246, 0.15)', padding: '1.25rem', borderRadius: '8px' }}>
                    <h4 style={{ color: 'var(--primary)', fontWeight: 600, marginBottom: '0.5rem' }}>Key Insights Produced</h4>
                    <p className="text-secondary" style={{ fontSize: '0.8rem', lineHeight: 1.6 }}>
                      Our 7-day log audit indicates that <strong>64.7% of AWS costs</strong> are wasted on underutilized nodes. Shifting batch workloads from On-Premises coal grids to GCP Europe nuclear grids prevents <strong>93% of carbon footprint emissions</strong> while scaling down H100 counts at night saves <strong>$3,921.58/week</strong>.
                    </p>
                  </div>

                  <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.03)', border: '1px solid rgba(16, 185, 129, 0.15)', padding: '1.25rem', borderRadius: '8px' }}>
                    <h4 style={{ color: '#10b981', fontWeight: 600, marginBottom: '0.5rem' }}>Business Outcomes</h4>
                    <ul style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', paddingLeft: '1.1rem', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <li><strong>50.0% savings</strong> on weekly infrastructure spend</li>
                      <li><strong>73.4% reduction</strong> in carbon emissions</li>
                      <li><strong>86.2% reduction</strong> in SLA violation breaches</li>
                      <li>Consulting-grade reports exportable to Admin dashboards</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: ADMIN PORTAL & SECURITY LOGS */}
          {activeTab === 'admin' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div className="card">
                <h2 className="brand-title" style={{ fontSize: '1.5rem' }}>Security Portal & User Activity Logs</h2>
                <p className="text-secondary">Auditing center displaying JWT authentication verification logs and user session operations.</p>
              </div>

              {!token ? (
                <div className="card" style={{ maxWidth: '400px', margin: '2rem auto', width: '100%' }}>
                  <h3 style={{ color: '#fafafa', fontWeight: 700, marginBottom: '1.25rem', textAlign: 'center' }}>
                    {isRegister ? "Register Account" : "Sign In to AetherFin"}
                  </h3>
                  
                  {authError && (
                    <div style={{ backgroundColor: 'var(--error-bg)', color: 'var(--error)', border: '1px solid var(--error-border)', padding: '0.5rem', borderRadius: '6px', fontSize: '0.8rem', marginBottom: '1rem', textAlign: 'center' }}>
                      {authError}
                    </div>
                  )}

                  <form onSubmit={handleAuthSubmit}>
                    <div className="form-group">
                      <label>Email Address</label>
                      <input type="email" className="chat-input" value={authEmail} onChange={(e) => setAuthEmail(e.target.value)} required />
                    </div>
                    
                    <div className="form-group">
                      <label>Password</label>
                      <input type="password" className="chat-input" value={authPassword} onChange={(e) => setAuthPassword(e.target.value)} required />
                    </div>

                    <button className="btn btn-primary" style={{ width: '100%', marginTop: '0.5rem' }} type="submit">
                      {isRegister ? "Create Admin User" : "Verify Token Access"}
                    </button>
                  </form>

                  <div style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.8rem', color: '#71717a' }}>
                    {isRegister ? (
                      <span onClick={() => { setIsRegister(false); setAuthError(null); }} style={{ cursor: 'pointer', color: 'var(--primary)' }}>
                        Already have an account? Login
                      </span>
                    ) : (
                      <span onClick={() => { setIsRegister(true); setAuthError(null); }} style={{ cursor: 'pointer', color: 'var(--primary)' }}>
                        Need an account? Register
                      </span>
                    )}
                  </div>
                </div>
              ) : (
                <div className="card">
                  <h3 className="card-title">
                    <Lock size={18} />
                    JWT Secure Audit Trail
                    <span className="card-title-secondary">Role: {userRole}</span>
                  </h3>
                  
                  {userRole !== 'Admin' ? (
                    <p className="text-secondary" style={{ padding: '2rem', textAlign: 'center' }}>
                      Audit logs are reserved for administrators. Your current role is <strong>{userRole}</strong>.
                    </p>
                  ) : (
                    <div className="table-container">
                      <table>
                        <thead>
                          <tr>
                            <th>Log ID</th>
                            <th>Timestamp</th>
                            <th>Username</th>
                            <th>Action Logged</th>
                            <th>IP Address</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activityLogs.map(log => (
                            <tr key={log.id}>
                              <td className="font-mono">#{log.id}</td>
                              <td>{new Date(log.timestamp).toLocaleString()}</td>
                              <td>{log.username}</td>
                              <td>
                                <span className="node-pill" style={{ 
                                  color: log.action.includes('export') ? '#10b981' : log.action.includes('login') ? '#3b82f6' : '#fafafa',
                                  fontWeight: 600
                                }}>{log.action}</span>
                              </td>
                              <td className="font-mono">{log.ip_address}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default App;
