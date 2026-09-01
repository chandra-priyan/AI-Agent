import { AnalysisSession } from '../types';
import { getFormattedDate } from './dateUtils';

export const getMockAnalyses = (): AnalysisSession[] => {
  const todayStr = getFormattedDate();
  
  return [
    {
      id: 'demo_sales_01',
      analysis_id: 'demo_sales_01',
      dataset_id: 'ds_sales_2026',
      datasetName: 'enterprise_sales_q3.csv',
      filename: 'enterprise_sales_q3.csv',
      question: 'What are the main drivers of quarterly revenue variance across product categories?',
      status: 'COMPLETED',
      job_stage: 'ANALYSIS_COMPLETE',
      job_progress: 100,
      conclusion: 'Quarterly sales revenue increased by 24.5% year-over-year, primarily driven by enterprise software subscriptions and strategic price optimization in North American markets.',
      confidence: 'HIGH',
      createdAt: todayStr,
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
    },
    {
      id: 'demo_churn_02',
      analysis_id: 'demo_churn_02',
      dataset_id: 'ds_churn_2026',
      datasetName: 'customer_churn_analysis.csv',
      filename: 'customer_churn_analysis.csv',
      question: 'Which customer usage behaviors correlate most strongly with 90-day churn risk?',
      status: 'COMPLETED',
      job_stage: 'ANALYSIS_COMPLETE',
      job_progress: 100,
      conclusion: 'Account churn probability rises sharply by 38% when customer support tickets remain unresolved past 72 hours, particularly in mid-tier accounts.',
      confidence: 'HIGH',
      createdAt: todayStr,
      rows: 2480,
      columns: 15,
      column_names: ['customer_id', 'tenure_months', 'support_tickets', 'monthly_charges', 'churn_label'],
      findings: [
        {
          id: 'f3',
          category: 'Customer Churn',
          title: 'Support Resolution Velocity',
          summary: 'Accounts with support resolution time > 72h exhibit 3.4x higher churn rate.',
          confidence: 'HIGH'
        }
      ],
      hypotheses: [
        {
          id: 'h2',
          title: 'Contract Length Retention Effect',
          description: 'Multi-year contract signups reduce annual churn rate by 42%.',
          status: 'validated',
          confidence: 'HIGH'
        }
      ]
    }
  ];
};

export const MOCK_ANALYSES: AnalysisSession[] = getMockAnalyses();
