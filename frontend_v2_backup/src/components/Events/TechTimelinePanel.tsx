import React from 'react';
import { Card } from '../Layout/Card';
import TechTimeline from './TechTimeline';
import styles from './TechTimelinePanel.module.css';

const TechTimelinePanel: React.FC = () => {
    return (
        <Card title="Technology Feed">
            <div className={styles.container}>
                <TechTimeline />
            </div>
        </Card>
    );
};

export default TechTimelinePanel;
