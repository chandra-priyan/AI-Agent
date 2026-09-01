import React, { useState } from 'react';
import { Settings, Cpu, Shield, Database, Save, Check } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { PageHeader } from '../components/ui/PageHeader';

export function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [modelName, setModelName] = useState('qwen2.5-coder:3b-instruct-q4_K_M');
  const [confidenceThreshold, setConfidenceThreshold] = useState('0.85');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <PageHeader
        title="Engine Settings"
        subtitle="Configure local Ollama, fallback LLM providers, and analytical threshold parameters"
      />

      <Card className="p-6">
        <form onSubmit={handleSave} className="space-y-6">
          {/* AI Engine Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2 border-b border-gray-100 pb-2">
              <Cpu className="w-4 h-4 text-[#6D28D9]" />
              <span>AI Provider & Model Engine</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1.5">Primary Provider</label>
                <select
                  value={llmProvider}
                  onChange={(e) => setLlmProvider(e.target.value)}
                  className="w-full p-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-[#6D28D9]"
                >
                  <option value="ollama">Local Ollama (Offline / Private)</option>
                  <option value="groq">Groq High-Speed Cloud</option>
                  <option value="gemini">Google Gemini API</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1.5">Model Specification</label>
                <input
                  type="text"
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  className="w-full p-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-[#6D28D9]"
                />
              </div>
            </div>
          </div>

          {/* Statistical Thresholds */}
          <div className="space-y-4 pt-4 border-t border-gray-100">
            <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider flex items-center gap-2 border-b border-gray-100 pb-2">
              <Database className="w-4 h-4 text-emerald-600" />
              <span>Statistical Confidence Bounds</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1.5">Alpha Significance Threshold (p-value)</label>
                <input
                  type="text"
                  defaultValue="0.05"
                  className="w-full p-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-[#6D28D9]"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1.5">Confidence Level Cutoff</label>
                <input
                  type="text"
                  value={confidenceThreshold}
                  onChange={(e) => setConfidenceThreshold(e.target.value)}
                  className="w-full p-2.5 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-[#6D28D9]"
                />
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-gray-100 flex justify-end">
            <Button
              type="submit"
              icon={saved ? <Check className="w-4 h-4 text-emerald-300" /> : <Save className="w-4 h-4" />}
              className="font-bold"
            >
              {saved ? 'Settings Saved!' : 'Save Engine Preferences'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

export default SettingsPage;
