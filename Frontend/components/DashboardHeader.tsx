import { ThemeToggle } from "@/components/ThemeToggle";

export function DashboardHeader() {
  return (
    <header className="dashboard-header">
      <div>
        <p className="eyebrow">Academic analytics / support workspace</p>
        <h1>Student Support Risk Prediction System</h1>
        <p className="header-copy">
          ML-powered academic risk assessment and student support insights.
        </p>
      </div>
      <div className="header-tools">
        <ThemeToggle />
      </div>
    </header>
  );
}
