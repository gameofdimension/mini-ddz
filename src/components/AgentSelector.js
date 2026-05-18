import React from 'react';
import { useTranslation } from 'react-i18next';

const AGENT_DEFS = [
    {
        value: 'deep',
        labelKey: 'configurable_battle.agent_deep',
        descKey: 'configurable_battle.agent_deep_desc',
        icon: '🧠',
    },
    {
        value: 'llm',
        labelKey: 'configurable_battle.agent_llm',
        descKey: 'configurable_battle.agent_llm_desc',
        icon: '🤖',
    },
    {
        value: 'random',
        labelKey: 'configurable_battle.agent_random',
        descKey: 'configurable_battle.agent_random_desc',
        icon: '🎲',
    },
];

export default function AgentSelector({ value, onChange }) {
    const { t } = useTranslation();

    return (
        <div style={{ display: 'flex', gap: '8px' }}>
            {AGENT_DEFS.map((def) => {
                const selected = value === def.value;
                return (
                    <div
                        key={def.value}
                        onClick={() => onChange(def.value)}
                        style={{
                            flex: 1,
                            padding: '12px 10px',
                            border: selected ? '2px solid #1976d2' : '2px solid #e0e0e0',
                            borderRadius: '8px',
                            cursor: 'pointer',
                            backgroundColor: selected ? '#e3f2fd' : '#fff',
                            textAlign: 'center',
                            transition: 'border-color 0.2s, background-color 0.2s',
                            userSelect: 'none',
                        }}
                        onMouseEnter={(e) => {
                            if (!selected) e.currentTarget.style.borderColor = '#90caf9';
                        }}
                        onMouseLeave={(e) => {
                            if (!selected) e.currentTarget.style.borderColor = '#e0e0e0';
                        }}
                    >
                        <div style={{ fontSize: '24px', marginBottom: '4px' }}>{def.icon}</div>
                        <div style={{
                            fontWeight: selected ? 700 : 500,
                            fontSize: '14px',
                            color: selected ? '#1565c0' : '#333',
                        }}>
                            {t(def.labelKey)}
                        </div>
                        <div style={{ fontSize: '11px', color: '#888', marginTop: '2px' }}>
                            {t(def.descKey)}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
