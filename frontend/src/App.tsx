import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './components/Layout/DashboardLayout';
import { Header } from './components/Header/Header';
import { LoadingOverlay } from './components/Common/LoadingOverlay';
import { GridContainer } from './components/Layout/GridColumn';
import { LeftColumn } from './components/Layout/LeftColumn';
import { CenterColumn } from './components/Layout/CenterColumn';
import { RightColumn } from './components/Layout/RightColumn';
import { useStatus, useWebSocket } from './hooks';
import { WS_URL } from './utils/constants';
import { Launcher } from './components/Launcher/Launcher';

const DEFAULT_FACTIONS = [
    'Solar_Hegemony',
    'Iron_Vanguard',
    'Void_Corsairs',
    'Rift_Daemons',
    'Scavenger_Clans',
    'Ancient_Guardians',
    'Ascended_Order',
    'Cyber_Synod',
    'Hive_Swarm',
    'Zealot_Legions'
];

function Dashboard() {
    const { loading, error } = useStatus();
    useWebSocket(WS_URL);

    if (error) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--error)' }}>
                <h2>SYSTEM CRITICAL ERROR</h2>
                <p>{error.message}</p>
                <button onClick={() => window.location.reload()}>REBOOT SYSTEM</button>
            </div>
        );
    }

    return (
        <DashboardLayout factions={DEFAULT_FACTIONS}>
            <LoadingOverlay visible={loading} />

            {!loading && (
                <>
                    <Header />
                    <GridContainer>
                        <LeftColumn />
                        <CenterColumn />
                        <RightColumn />
                    </GridContainer>
                </>
            )}
        </DashboardLayout>
    );
}

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Launcher />} />
                <Route path="/dashboard" element={<Dashboard />} />
                {/* Fallback to Launcher for unknown routes */}
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    );
}

export default App;
