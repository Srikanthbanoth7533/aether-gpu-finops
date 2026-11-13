import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import {
  TrendingUp,
  DollarSign,
  Percent,
  ShoppingCart,
  Users,
  ShoppingBag,
  Sparkles,
  Terminal,
  Calendar,
  ArrowUpRight,
  RefreshCw,
  Grid,
  Layers,
  HelpCircle,
  Database
} from 'lucide-react';

// API Base URL (configured to backend running on localhost:8002 by default)
const API_BASE = 'http://127.0.0.1:8002';

interface KPIs {
  total_revenue: number;
  total_profit: number;
  profit_margin: number;
  average_order_value: number;
  conversion_rate: number;
  repeat_customer_rate: number;
  total_orders: number;
  total_customers: number;
}

interface TrendPoint {
  date: string;
  sales: number;
  profit: number;
  orders: number;
}

interface CategoryProfitability {
  category: string;
  sub_category: string;
  sales: number;
  profit: number;
  quantity: number;
  profit_margin: number;
}

interface TopProduct {
  product_id: string;
  name: string;
  category: string;
  sales: number;
  profit: number;
  quantity_sold: number;
}

interface FunnelStage {
  stage: string;
  count: number;
  percentage: number;
}

interface CohortRow {
  cohort: string;
  size: number;
  retention: Record<string, number>;
}

interface Recommendation {
  id: number;
  category: string;
  title: string;
  description: string;
  impact: string;
  estimated_val: number;
}

interface SQLResult {
  columns: string[];
  rows: any[][];
  execution_time_ms: number;
  error: string | null;
}

const PRESET_QUERIES = [
  {
    name: 'Customer CLV by Segment',
    sql: `SELECT c.segment,\n       COUNT(DISTINCT o.order_id) as total_orders,\n       ROUND(SUM(oi.sales), 2) as total_sales,\n       ROUND(AVG(oi.sales), 2) as avg_order_sales\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nJOIN order_items oi ON o.order_id = oi.order_id\nGROUP BY c.segment\nORDER BY total_sales DESC`
  },
  {
    name: 'Top 5 Most Profitable Products',
    sql: `SELECT p.name,\n       p.category,\n       ROUND(SUM(oi.sales), 2) as total_sales,\n       ROUND(SUM(oi.profit), 2) as total_profit\nFROM products p\nJOIN order_items oi ON p.product_id = oi.product_id\nGROUP BY p.product_id\nORDER BY total_profit DESC\nLIMIT 5`
  },
  {
    name: 'Monthly Revenue Performance',
    sql: `SELECT strftime('%Y-%m', o.order_date) as month,\n       ROUND(SUM(oi.sales), 2) as total_sales,\n       ROUND(SUM(oi.profit), 2) as total_profit,\n       COUNT(DISTINCT o.order_id) as total_orders\nFROM orders o\nJOIN order_items oi ON o.order_id = oi.order_id\nGROUP BY month\nORDER BY month ASC`
  },
  {
    name: 'Top 10 Repeat Buyers',
    sql: `SELECT c.customer_id,\n       c.name,\n       COUNT(o.order_id) as order_count,\n       ROUND(SUM(oi.sales), 2) as total_spent\nFROM customers c\nJOIN orders o ON c.customer_id = o.customer_id\nJOIN order_items oi ON o.order_id = oi.order_id\nGROUP BY c.customer_id\nHAVING order_count >= 2\nORDER BY order_count DESC\nLIMIT 10`
  }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'cohorts' | 'products' | 'sql-console' | 'recommendations'>('overview');
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters State
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedSegment, setSelectedSegment] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  // Analytics Data State
  const [kpis, setKpis] = useState<KPIs | null>(null);
  const [trends, setTrends] = useState<TrendPoint[]>([]);
  const [categories, setCategories] = useState<CategoryProfitability[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [funnel, setFunnel] = useState<FunnelStage[]>([]);
  const [cohorts, setCohorts] = useState<CohortRow[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);

  // SQL Console State
  const [sqlQuery, setSqlQuery] = useState(PRESET_QUERIES[0].sql);
  const [sqlResult, setSqlResult] = useState<SQLResult | null>(null);
  const [executingQuery, setExecutingQuery] = useState(false);

  // Fetch Dashboard Data
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Build query string
      const params = new URLSearchParams();
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);
      if (selectedSegment) params.append('segment', selectedSegment);
      if (selectedCategory) params.append('category', selectedCategory);

      const qs = params.toString() ? `?${params.toString()}` : '';

      // Run parallel fetches for core metrics
      const [kpiRes, trendRes, catRes, topRes, funnelRes, cohortRes, recRes] = await Promise.all([
        fetch(`${API_BASE}/api/kpis${qs}`),
        fetch(`${API_BASE}/api/trends${qs}`),
        fetch(`${API_BASE}/api/categories${qs}`),
        fetch(`${API_BASE}/api/products/top?limit=10${selectedCategory ? `&category=${selectedCategory}` : ''}`),
        fetch(`${API_BASE}/api/funnel${qs}`),
        fetch(`${API_BASE}/api/cohorts`),
        fetch(`${API_BASE}/api/recommendations`)
      ]);

      if (!kpiRes.ok || !trendRes.ok || !catRes.ok || !topRes.ok || !funnelRes.ok || !cohortRes.ok || !recRes.ok) {
        throw new Error('API server returned error. Check connection settings.');
      }

      setKpis(await kpiRes.json());
      setTrends(await trendRes.json());
      setCategories(await catRes.json());
      setTopProducts(await topRes.json());
      setFunnel(await funnelRes.json());
      setCohorts(await cohortRes.json());
      setRecommendations(await recRes.json());
    } catch (e: any) {
      console.error(e);
      setError('Could not connect to FastAPI Backend. Make sure backend is running on port 8002.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate, selectedSegment, selectedCategory]);

  // Execute SQL Query
  const runSQLQuery = async (queryText = sqlQuery) => {
    setExecutingQuery(true);
    setSqlResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText })
      });
      if (!res.ok) {
        const errObj = await res.json();
        throw new Error(errObj.detail || 'Query Execution Failed');
      }
      const data = await res.json();
      setSqlResult(data);
    } catch (e: any) {
      setSqlResult({
        columns: [],
        rows: [],
        execution_time_ms: 0,
        error: e.message || 'Unknown network error'
      });
    } finally {
      setExecutingQuery(false);
    }
  };

  // Seed Database Trigger
  const triggerSeed = async () => {
    if (!window.confirm('Do you want to re-seed the SQLite database? This will reset all transaction and traffic history.')) return;
    setSeeding(true);
    try {
      const res = await fetch(`${API_BASE}/api/seed`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'success') {
        alert('Database seeded successfully!');
        fetchData();
      } else {
        alert('Seeding failed: ' + data.message);
      }
    } catch (e: any) {
      alert('Error triggering seeding: ' + e.message);
    } finally {
      setSeeding(false);
    }
  };

  // Reset Filters
  const resetFilters = () => {
    setStartDate('');
    setEndDate('');
    setSelectedSegment('');
    setSelectedCategory('');
  };

  // Trend Chart Configuration
  const getTrendChartOption = () => {
    return {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross', label: { backgroundColor: '#18181b' } }
      },
      legend: {
        data: ['Sales ($)', 'Profit ($)'],
        textStyle: { color: '#a1a1aa' }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: trends.map((t) => t.date),
        axisLine: { lineStyle: { color: '#27272a' } },
        axisLabel: { color: '#a1a1aa' }
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#27272a' } },
        axisLabel: { color: '#a1a1aa' },
        splitLine: { lineStyle: { color: 'rgba(39, 39, 42, 0.5)' } }
      },
      series: [
        {
          name: 'Sales ($)',
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: trends.map((t) => t.sales),
          itemStyle: { color: '#6366f1' },
          lineStyle: { width: 3 }
        },
        {
          name: 'Profit ($)',
          type: 'line',
          smooth: true,
          showSymbol: false,
          data: trends.map((t) => t.profit),
          itemStyle: { color: '#10b981' },
          lineStyle: { width: 3 }
        }
      ]
    };
  };

  // Category Profitability Chart Configuration
  const getCategoryChartOption = () => {
    const cats = Array.from(new Set(categories.map((c) => c.category)));
    const salesData = cats.map((cat) =>
      categories.filter((c) => c.category === cat).reduce((sum, current) => sum + current.sales, 0)
    );
    const profitData = cats.map((cat) =>
      categories.filter((c) => c.category === cat).reduce((sum, current) => sum + current.profit, 0)
    );

    return {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: {
        data: ['Sales', 'Profit'],
        textStyle: { color: '#a1a1aa' }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: {
        type: 'value',
        axisLabel: { color: '#a1a1aa' },
        axisLine: { lineStyle: { color: '#27272a' } },
        splitLine: { lineStyle: { color: 'rgba(39, 39, 42, 0.5)' } }
      },
      yAxis: {
        type: 'category',
        data: cats,
        axisLabel: { color: '#a1a1aa' },
        axisLine: { lineStyle: { color: '#27272a' } }
      },
      series: [
        {
          name: 'Sales',
          type: 'bar',
          data: salesData,
          itemStyle: { color: '#6366f1', borderRadius: [0, 4, 4, 0] }
        },
        {
          name: 'Profit',
          type: 'bar',
          data: profitData,
          itemStyle: { color: '#10b981', borderRadius: [0, 4, 4, 0] }
        }
      ]
    };
  };

  // Get Cohort Grid Background Intensity
  const getHeatmapColor = (val: number) => {
    if (val === 0) return 'rgba(0,0,0,0.1)';
    if (val === 100) return 'rgba(99, 102, 241, 0.8)';
    const pct = val / 100;
    return `rgba(99, 102, 241, ${0.1 + pct * 0.7})`;
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="brand-section">
          <Database className="logo-icon" size={32} />
          <div>
            <h1 className="title-main">E-commerce Sales Analytics</h1>
            <p className="subtitle-main">SQL & Python-backed Portfolio Dashboard</p>
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <button
            className="tab-btn"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'var(--text-secondary)'
            }}
            onClick={triggerSeed}
            disabled={seeding}
          >
            <RefreshCw className={seeding ? 'spin' : ''} size={14} />
            {seeding ? 'Seeding...' : 'Reset & Seed DB'}
          </button>
        </div>
      </header>

      {/* Filter Bar */}
      <section className="filter-bar">
        <div className="filter-group">
          <label className="filter-label">Start Date</label>
          <input
            type="date"
            className="date-input"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label className="filter-label">End Date</label>
          <input
            type="date"
            className="date-input"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <div className="filter-group">
          <label className="filter-label">Customer Segment</label>
          <select
            className="select-input"
            value={selectedSegment}
            onChange={(e) => setSelectedSegment(e.target.value)}
          >
            <option value="">All Segments</option>
            <option value="Consumer">Consumer</option>
            <option value="Corporate">Corporate</option>
            <option value="Home Office">Home Office</option>
          </select>
        </div>
        <div className="filter-group">
          <label className="filter-label">Product Category</label>
          <select
            className="select-input"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="">All Categories</option>
            <option value="Technology">Technology</option>
            <option value="Furniture">Furniture</option>
            <option value="Office Supplies">Office Supplies</option>
          </select>
        </div>
        <button
          onClick={resetFilters}
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            fontSize: '0.875rem',
            cursor: 'pointer',
            padding: '0.5rem',
            alignSelf: 'flex-end'
          }}
        >
          Reset Filters
        </button>
      </section>

      {/* Error Alert */}
      {error && (
        <div className="error-banner" style={{ marginBottom: '1.5rem' }}>
          {error}
        </div>
      )}

      {/* KPI Cards Grid */}
      <section className="kpi-grid">
        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Total Revenue</span>
            <DollarSign className="kpi-icon text-success" size={18} />
          </div>
          <div className="kpi-value">${kpis ? kpis.total_revenue.toLocaleString() : '0.00'}</div>
          <div className="kpi-footer">
            <TrendingUp size={12} className="text-success" />
            <span>Cumulative Sales</span>
          </div>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Total Profit</span>
            <DollarSign className="kpi-icon text-success" size={18} />
          </div>
          <div className="kpi-value">${kpis ? kpis.total_profit.toLocaleString() : '0.00'}</div>
          <div className="kpi-footer">
            <span className={kpis && kpis.profit_margin >= 20 ? 'text-success' : 'text-warning'}>
              Margin: {kpis ? kpis.profit_margin : 0}%
            </span>
          </div>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Average Order Value</span>
            <ShoppingCart className="kpi-icon text-success" size={18} />
          </div>
          <div className="kpi-value">${kpis ? kpis.average_order_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : '0.00'}</div>
          <div className="kpi-footer">
            <span>Per Completed Order</span>
          </div>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Traffic Conversion</span>
            <Percent className="kpi-icon text-success" size={18} />
          </div>
          <div className="kpi-value">{kpis ? kpis.conversion_rate : 0}%</div>
          <div className="kpi-footer">
            <span>Sessions to Purchases</span>
          </div>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <span className="kpi-title">Repeat Buyer Rate</span>
            <Users className="kpi-icon text-success" size={18} />
          </div>
          <div className="kpi-value">{kpis ? kpis.repeat_customer_rate : 0}%</div>
          <div className="kpi-footer">
            <span>Customers with ≥ 2 orders</span>
          </div>
        </div>
      </section>

      {/* Main Content Tabs */}
      <section className="card" style={{ padding: '1.5rem', minHeight: '550px' }}>
        <div className="tabs-header">
          <button
            className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            <Grid size={14} style={{ marginRight: '0.35rem', display: 'inline' }} />
            Overview
          </button>
          <button
            className={`tab-btn ${activeTab === 'products' ? 'active' : ''}`}
            onClick={() => setActiveTab('products')}
          >
            <ShoppingBag size={14} style={{ marginRight: '0.35rem', display: 'inline' }} />
            Product Analytics
          </button>
          <button
            className={`tab-btn ${activeTab === 'cohorts' ? 'active' : ''}`}
            onClick={() => setActiveTab('cohorts')}
          >
            <Layers size={14} style={{ marginRight: '0.35rem', display: 'inline' }} />
            Customer Cohorts
          </button>
          <button
            className={`tab-btn ${activeTab === 'sql-console' ? 'active' : ''}`}
            onClick={() => setActiveTab('sql-console')}
          >
            <Terminal size={14} style={{ marginRight: '0.35rem', display: 'inline' }} />
            Interactive SQL Console
          </button>
          <button
            className={`tab-btn ${activeTab === 'recommendations' ? 'active' : ''}`}
            onClick={() => setActiveTab('recommendations')}
          >
            <Sparkles size={14} style={{ marginRight: '0.35rem', display: 'inline' }} />
            Strategic Insights
          </button>
        </div>

        {loading ? (
          <div className="loading-spinner">
            <RefreshCw className="spin" size={24} />
            <span style={{ marginLeft: '0.5rem' }}>Loading analytics data...</span>
          </div>
        ) : (
          <div>
            {/* Tab: Overview */}
            {activeTab === 'overview' && (
              <div>
                <div className="dashboard-row-2cols">
                  {/* Left: Trend Line Chart */}
                  <div className="card" style={{ background: '#121217', borderColor: 'transparent' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Revenue & Profitability Growth Trends</h3>
                    {trends.length > 0 ? (
                      <ReactECharts option={getTrendChartOption()} style={{ height: '320px' }} />
                    ) : (
                      <div className="empty-state">No trend data available for current selection</div>
                    )}
                  </div>

                  {/* Right: Funnel Tracking */}
                  <div className="card" style={{ background: '#121217', borderColor: 'transparent' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Web Conversion Funnel</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', marginTop: '1rem' }}>
                      {funnel.map((stage, idx) => (
                        <div key={idx}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.35rem' }}>
                            <span style={{ color: 'var(--text-secondary)' }}>{stage.stage}</span>
                            <span style={{ fontWeight: 600 }}>{stage.count.toLocaleString()} sessions ({stage.percentage}%)</span>
                          </div>
                          {/* Funnel Visual Progress Bar */}
                          <div style={{ height: '14px', background: '#27272a', borderRadius: '4px', overflow: 'hidden' }}>
                            <div
                              style={{
                                height: '100%',
                                background: idx === 0 ? '#6366f1' : idx === 1 ? '#818cf8' : '#10b981',
                                width: `${stage.percentage}%`,
                                transition: 'width 0.8s ease-out'
                              }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="dashboard-row-equal">
                  {/* Left: Categories Sales Bar */}
                  <div className="card" style={{ background: '#121217', borderColor: 'transparent' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Category Profitability</h3>
                    {categories.length > 0 ? (
                      <ReactECharts option={getCategoryChartOption()} style={{ height: '240px' }} />
                    ) : (
                      <div className="empty-state">No category data available</div>
                    )}
                  </div>

                  {/* Right: Top Selling Mini Table */}
                  <div className="card" style={{ background: '#121217', borderColor: 'transparent' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1.25rem' }}>Top Products by Revenue</h3>
                    <div className="table-container">
                      <table className="analytics-table">
                        <thead>
                          <tr>
                            <th>Product</th>
                            <th>Category</th>
                            <th style={{ textAlign: 'right' }}>Revenue</th>
                            <th style={{ textAlign: 'right' }}>Profit</th>
                          </tr>
                        </thead>
                        <tbody>
                          {topProducts.slice(0, 5).map((p, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 500 }}>{p.name}</td>
                              <td style={{ color: 'var(--text-muted)' }}>{p.category}</td>
                              <td style={{ textAlign: 'right' }}>${p.sales.toLocaleString()}</td>
                              <td style={{ textAlign: 'right', color: p.profit >= 0 ? 'var(--success)' : 'var(--error)' }}>
                                ${p.profit.toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Tab: Products */}
            {activeTab === 'products' && (
              <div className="card" style={{ background: '#121217', borderColor: 'transparent' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '1rem' }}>Catalog Performance Details</h3>
                <div className="table-container">
                  <table className="analytics-table">
                    <thead>
                      <tr>
                        <th>Product ID</th>
                        <th>Product Name</th>
                        <th>Category</th>
                        <th style={{ textAlign: 'right' }}>Quantity Sold</th>
                        <th style={{ textAlign: 'right' }}>Total Revenue</th>
                        <th style={{ textAlign: 'right' }}>Total Profit</th>
                        <th style={{ textAlign: 'right' }}>Profit Margin</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topProducts.map((p, idx) => {
                        const margin = (p.profit / p.sales) * 100;
                        return (
                          <tr key={idx}>
                            <td className="font-mono text-secondary">{p.product_id}</td>
                            <td style={{ fontWeight: 500 }}>{p.name}</td>
                            <td>{p.category}</td>
                            <td style={{ textAlign: 'right' }}>{p.quantity_sold}</td>
                            <td style={{ textAlign: 'right' }}>${p.sales.toLocaleString()}</td>
                            <td style={{ textAlign: 'right', color: p.profit >= 0 ? 'var(--success)' : 'var(--error)' }}>
                              ${p.profit.toLocaleString()}
                            </td>
                            <td style={{ textAlign: 'right', fontWeight: 600, color: margin >= 20 ? 'var(--success)' : margin >= 5 ? 'var(--text)' : 'var(--error)' }}>
                              {margin.toFixed(1)}%
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab: Cohorts */}
            {activeTab === 'cohorts' && (
              <div className="card" style={{ background: '#121217', borderColor: 'transparent' }}>
                <div style={{ marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Monthly Customer Retention Heatmap</h3>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    Constructed using Pandas in the backend. Tracks customer order continuation based on cohort signup month.
                  </p>
                </div>
                <div className="cohort-matrix">
                  <table className="cohort-table">
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left', paddingLeft: '1rem' }}>Cohort Month</th>
                        <th>Size</th>
                        <th>Month 0</th>
                        <th>Month 1</th>
                        <th>Month 2</th>
                        <th>Month 3</th>
                        <th>Month 4</th>
                        <th>Month 5</th>
                        <th>Month 6</th>
                        <th>Month 7</th>
                        <th>Month 8</th>
                        <th>Month 9</th>
                        <th>Month 10</th>
                        <th>Month 11</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cohorts.map((row, idx) => (
                        <tr key={idx}>
                          <td style={{ textAlign: 'left', fontWeight: 600, paddingLeft: '1rem', background: '#1c1c24' }}>
                            {row.cohort}
                          </td>
                          <td style={{ fontWeight: 500, background: '#18181b' }}>{row.size}</td>
                          {Array.from({ length: 12 }).map((_, mIdx) => {
                            const val = row.retention[mIdx.toString()];
                            const isPresent = val !== undefined;
                            return (
                              <td
                                key={mIdx}
                                className="cohort-cell"
                                style={{
                                  backgroundColor: isPresent ? getHeatmapColor(val) : 'transparent',
                                  color: isPresent ? '#fff' : '#4b5563'
                                }}
                              >
                                {isPresent ? `${val.toFixed(0)}%` : '-'}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Tab: SQL Console */}
            {activeTab === 'sql-console' && (
              <div className="sql-console">
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Interactive SQL Query Console</h3>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                    Execute direct queries against SQLite schema tables: <code style={{color: 'var(--primary)'}}>customers</code>, <code style={{color: 'var(--primary)'}}>products</code>, <code style={{color: 'var(--primary)'}}>orders</code>, <code style={{color: 'var(--primary)'}}>order_items</code>, and <code style={{color: 'var(--primary)'}}>web_traffic</code>.
                  </p>
                </div>

                <div className="preset-queries">
                  {PRESET_QUERIES.map((pq, idx) => (
                    <button
                      key={idx}
                      className="preset-btn"
                      onClick={() => {
                        setSqlQuery(pq.sql);
                        runSQLQuery(pq.sql);
                      }}
                    >
                      {pq.name}
                    </button>
                  ))}
                </div>

                <div className="sql-editor-container">
                  <textarea
                    className="sql-textarea"
                    value={sqlQuery}
                    onChange={(e) => setSqlQuery(e.target.value)}
                    placeholder="SELECT * FROM orders LIMIT 10..."
                  />
                  <div className="console-actions">
                    <button
                      className="run-btn"
                      onClick={() => runSQLQuery()}
                      disabled={executingQuery || !sqlQuery.trim()}
                    >
                      <Terminal size={14} />
                      {executingQuery ? 'Running...' : 'Execute SELECT Query'}
                    </button>
                    {sqlResult && !sqlResult.error && (
                      <span className="query-result-meta">
                        Returned {sqlResult.rows.length} rows in {sqlResult.execution_time_ms} ms
                      </span>
                    )}
                  </div>
                </div>

                {sqlResult && sqlResult.error && (
                  <div className="error-banner">
                    Error executing SQL query:
                    <br />
                    {sqlResult.error}
                  </div>
                )}

                {sqlResult && !sqlResult.error && sqlResult.columns.length > 0 && (
                  <div className="card" style={{ background: '#121217', borderColor: 'transparent' }}>
                    <h4 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
                      Query Output
                    </h4>
                    <div className="table-container" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      <table className="analytics-table">
                        <thead>
                          <tr>
                            {sqlResult.columns.map((col, idx) => (
                              <th key={idx}>{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {sqlResult.rows.map((row, rIdx) => (
                            <tr key={rIdx}>
                              {row.map((val, cIdx) => (
                                <td key={cIdx} className={typeof val === 'number' ? 'font-mono' : ''}>
                                  {val === null ? <em style={{ color: 'var(--text-muted)' }}>NULL</em> : String(val)}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Tab: Strategic Recommendations */}
            {activeTab === 'recommendations' && (
              <div>
                <div style={{ marginBottom: '1.25rem' }}>
                  <h3 style={{ fontSize: '1rem', fontWeight: 600 }}>Business Performance Insights</h3>
                  <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    Actionable recommendation models computed by evaluating recent database sales performance and customer retention patterns.
                  </p>
                </div>
                <div className="recommendation-list">
                  {recommendations.map((rec) => (
                    <div key={rec.id} className="recommendation-card">
                      <div className="rec-header">
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <span className={`rec-badge ${rec.impact.toLowerCase()}`}>{rec.impact} Impact</span>
                          <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                            {rec.category}
                          </span>
                        </div>
                        <span className="rec-est">Est. Opportunity: +${rec.estimated_val.toLocaleString()}</span>
                      </div>
                      <h4 style={{ fontSize: '1rem', fontWeight: 600, marginTop: '0.25rem' }}>{rec.title}</h4>
                      <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                        {rec.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
