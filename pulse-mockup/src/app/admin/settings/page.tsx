"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { AlertTriangle, AlertCircle, X } from "lucide-react";
import {
  CREDIT_COST_CONFIG,
  MOCK_ALERTS,
  type AlertItem,
} from "@/lib/mock-data";

export default function AdminSettingsPage() {
  // Credit costs: initialize from CREDIT_COST_CONFIG
  const [costs, setCosts] = useState<Record<string, number>>(
    Object.fromEntries(CREDIT_COST_CONFIG.map((c) => [c.activity, c.costPerUnit]))
  );

  // Alerts: initialize from MOCK_ALERTS, dismiss removes from array
  const [alerts, setAlerts] = useState<AlertItem[]>(MOCK_ALERTS);

  // Threshold inputs
  const [creditThreshold, setCreditThreshold] = useState("300");
  const [dayThreshold, setDayThreshold] = useState("30");

  // Save feedback
  const [saved, setSaved] = useState(false);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="text-sm text-muted-foreground mt-1">
        Configure workspace behavior and alert thresholds
      </p>

      {/* SECTION 1: Workspace Credit Costs */}
      <div className="bg-card border border-border rounded-lg p-6 mt-6">
        <h2 className="text-lg font-semibold">Workspace Credit Costs</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Set the credit cost for each activity type.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] items-center gap-x-8 gap-y-4 mt-6">
          {CREDIT_COST_CONFIG.map((c) => (
            <>
              <div key={`label-${c.activity}`}>
                <p className="text-sm font-medium">{c.activity}</p>
                <p className="text-xs text-muted-foreground">{c.description}</p>
              </div>
              <div key={`input-${c.activity}`} className="flex items-center gap-2">
                <Input
                  type="number"
                  min={0}
                  className="w-24 text-right"
                  value={costs[c.activity]}
                  onChange={(e) =>
                    setCosts((prev) => ({
                      ...prev,
                      [c.activity]: Number(e.target.value),
                    }))
                  }
                />
                <span className="text-xs text-muted-foreground">credits</span>
              </div>
            </>
          ))}
        </div>

        <div className="mt-6">
          <Button
            onClick={() => {
              setSaved(true);
              setTimeout(() => setSaved(false), 2000);
            }}
          >
            {saved ? "Saved!" : "Save Changes"}
          </Button>
        </div>
      </div>

      {/* SECTION 2: Workspace Alerts */}
      <div className="bg-card border border-border rounded-lg p-6 mt-6">
        <h2 className="text-lg font-semibold">Workspace Alerts</h2>

        {/* Threshold configuration */}
        <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide mt-4">
          Alert Thresholds
        </p>

        <div className="flex items-center gap-2 flex-wrap text-sm mt-3">
          <span>Alert when a user exceeds</span>
          <Input
            type="number"
            min={0}
            className="w-24"
            value={creditThreshold}
            onChange={(e) => setCreditThreshold(e.target.value)}
          />
          <span>credits in</span>
          <Input
            type="number"
            min={0}
            className="w-16"
            value={dayThreshold}
            onChange={(e) => setDayThreshold(e.target.value)}
          />
          <span>days</span>
        </div>

        <Button variant="outline" size="sm" className="mt-3">
          Update Thresholds
        </Button>

        {/* Active alerts */}
        <div className="mt-6">
          <p className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
            Active Alerts ({alerts.length})
          </p>

          {alerts.length === 0 && (
            <p className="text-sm text-muted-foreground py-4">No active alerts.</p>
          )}

          <div className="mt-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-start gap-3 rounded-lg border border-border bg-background p-4 mb-3"
              >
                {/* Severity icon */}
                {alert.severity === "critical" ? (
                  <AlertCircle className="h-5 w-5 text-destructive shrink-0 mt-0.5" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-yellow-500 shrink-0 mt-0.5" />
                )}

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium">{alert.message}</p>
                  <p className="text-xs text-muted-foreground mt-1">{alert.timestamp}</p>
                </div>

                {/* Dismiss button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="shrink-0 h-8 w-8 p-0 text-muted-foreground hover:text-foreground"
                  onClick={() =>
                    setAlerts((prev) => prev.filter((a) => a.id !== alert.id))
                  }
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
