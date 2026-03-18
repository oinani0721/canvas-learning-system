/**
 * Canvas Learning System - App Root
 *
 * Main application component with routing.
 * Currently routes to the Settings page (Story 1.3).
 * Additional routes will be added in later stories.
 */

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { SettingsPage } from "@/components/settings/settings-page";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/settings" element={<SettingsPage />} />
        {/* Default redirect to settings for now */}
        <Route path="*" element={<Navigate to="/settings" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
