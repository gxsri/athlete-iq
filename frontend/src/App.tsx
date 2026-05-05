import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { AthleteList } from './pages/AthleteList';
import { AthleteDetail } from './pages/AthleteDetail';
import { TrainingLog } from './pages/TrainingLog';
import { Planner } from './pages/Planner';
import { Alerts } from './pages/Alerts';
import { Reports } from './pages/Reports';
import { RehabCenter } from './pages/RehabCenter';
import { ExercisesPage } from './pages/ExercisesPage';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/athletes" element={<AthleteList />} />
          <Route path="/athletes/:id" element={<AthleteDetail />} />
          <Route path="/training-log" element={<TrainingLog />} />
          <Route path="/planner" element={<Planner />} />
          <Route path="/exercises" element={<ExercisesPage />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/rehab" element={<RehabCenter />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
