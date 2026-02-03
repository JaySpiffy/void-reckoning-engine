import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { controlApi } from '../../api/client';

export const Launcher: React.FC = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [configs, setConfigs] = useState<string[]>([]);
    const [selectedConfig, setSelectedConfig] = useState<string>('');
    const [universe, setUniverse] = useState<string>('eternal_crusade');
    const [universes, setUniverses] = useState<string[]>(['eternal_crusade']);

    useEffect(() => {
        // Fetch available data on mount
        const fetchData = async () => {
            try {
                // Fetch Configs
                const configRes = await controlApi.getConfigs();
                if (configRes.data.configs && configRes.data.configs.length > 0) {
                    setConfigs(configRes.data.configs);
                    setSelectedConfig(configRes.data.configs[0]);
                }

                // Fetch Universes
                const uniRes = await controlApi.getUniverses();
                if (uniRes.data.universes && uniRes.data.universes.length > 0) {
                    setUniverses(uniRes.data.universes);
                    // Default to first if current valid default not found? 
                    // ideally we keep eternal_crusade if it exists, or just pick first
                    if (!uniRes.data.universes.includes(universe)) {
                        setUniverse(uniRes.data.universes[0]);
                    }
                }
            } catch (err) {
                console.error("Failed to load launcher data:", err);
            }
        };
        fetchData();
    }, []);

    const handleStart = async () => {
        setLoading(true);
        try {
            await controlApi.launch(universe, selectedConfig);
            // Give it a moment to initialize before routing
            setTimeout(() => {
                navigate('/dashboard');
            }, 2000);
        } catch (error) {
            console.error("Failed to start:", error);
            alert("Failed to launch simulation. Check console.");
            setLoading(false);
        }
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100vh',
            backgroundColor: '#0a0a0a',
            color: '#fff',
            fontFamily: 'Inter, system-ui, sans-serif'
        }}>
            <div style={{
                padding: '3rem',
                border: '1px solid #333',
                borderRadius: '8px',
                background: 'rgba(20, 20, 20, 0.8)',
                backdropFilter: 'blur(10px)',
                textAlign: 'center',
                maxWidth: '500px',
                width: '100%'
            }}>
                <h1 style={{ marginBottom: '1rem', fontSize: '2.5rem', background: 'linear-gradient(45deg, #4f46e5, #06b6d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    Eternal Crusade
                </h1>
                <p style={{ color: '#888', marginBottom: '2rem' }}>
                    Multi-Universe Grand Strategy Simulator
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', textAlign: 'left' }}>

                    <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: '#666', marginBottom: '0.5rem' }}>UNIVERSE</label>
                        <select
                            value={universe}
                            onChange={(e) => setUniverse(e.target.value)}
                            style={{
                                width: '100%', padding: '0.8rem', background: '#111', border: '1px solid #333', color: 'white', borderRadius: '4px'
                            }}
                        >
                            {universes.map(u => (
                                <option key={u} value={u}>{u}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label style={{ display: 'block', fontSize: '0.8rem', color: '#666', marginBottom: '0.5rem' }}>CONFIGURATION</label>
                        <select
                            value={selectedConfig}
                            onChange={(e) => setSelectedConfig(e.target.value)}
                            style={{
                                width: '100%', padding: '0.8rem', background: '#111', border: '1px solid #333', color: 'white', borderRadius: '4px'
                            }}
                        >
                            {configs.map(c => (
                                <option key={c} value={c}>{c}</option>
                            ))}
                        </select>
                    </div>

                    <button
                        onClick={handleStart}
                        disabled={loading}
                        style={{
                            marginTop: '1rem',
                            padding: '1rem 2rem',
                            fontSize: '1.1rem',
                            fontWeight: 600,
                            color: 'white',
                            backgroundColor: '#4f46e5',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: loading ? 'wait' : 'pointer',
                            transition: 'all 0.2s',
                            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
                        }}
                        onMouseOver={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
                        onMouseOut={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                    >
                        {loading ? 'INITIALIZING ENGINE...' : 'START NEW CAMPAIGN'}
                    </button>

                    <button
                        onClick={() => navigate('/dashboard')}
                        style={{
                            background: 'transparent',
                            border: '1px solid #333',
                            color: '#888',
                            padding: '0.8rem',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Enter Existing Dashboard
                    </button>

                    <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid #222', fontSize: '0.8rem', color: '#444', textAlign: 'center' }}>
                        v2.1.0 - SYSTEM READY
                    </div>
                </div>
            </div>
        </div>
    );
};
