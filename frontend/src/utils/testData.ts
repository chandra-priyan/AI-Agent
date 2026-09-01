import { AnalysisSession } from '../types';

export const MOCK_ANALYSES: AnalysisSession[] = [
  {
    id: 'demo_sales_01',
    analysis_id: 'demo_sales_01',
    dataset_id: 'ds_sales_2026',
    datasetName: 'demo_sales.csv',
    filename: 'demo_sales.csv',
    question: 'What are the main drivers of quarterly revenue variance across product categories?',
    status: 'COMPLETED',
    job_stage: 'ANALYSIS_COMPLETE',
    job_progress: 100,
    conclusion: 'Quarterly sales revenue increased by 24.5% year-over-year, primarily driven by enterprise software subscriptions and strategic price optimization in North American markets.',
    confidence: 'HIGH',
    createdAt: '2026-09-01 08:30',
    rows: 1540,
    columns: 12,
    column_names: ['date', 'region', 'category', 'revenue', 'units', 'discount', 'customer_type', 'net_profit'],
    findings: [
      {
        id: 'f1',
        category: 'Revenue Growth',
        title: 'Enterprise Subscription Expansion',
        summary: 'Enterprise customers generated 62% of total recurring revenue with a 94% retention rate.',
        confidence: 'HIGH'
      },
      {
        id: 'f2',
        category: 'Profit Margin',
        title: 'Discount Impact on Margin',
        summary: 'Discounts exceeding 15% led to a 28% drop in unit gross margin without significant volume elasticity.',
        confidence: 'HIGH'
      }
    ],
    hypotheses: [
      {
        id: 'h1',
        title: 'Regional Price Elasticity',
        description: 'Higher price resistance observed in LATAM region due to local currency fluctuations.',
        status: 'validated',
        confidence: 'HIGH'
      }
    ]
  }
];
