import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Settings as SettingsIcon, Server, Palette, Bell, HardDrive, Trash2, RefreshCw, CheckCircle, Loader2 } from "lucide-react";
import { getStorageStats, clearAllData, checkBackendHealth, type StorageStats } from "@/lib/api";
import { useResearch } from "@/hooks/use-research";

const Settings = () => {
  const [storageStats, setStorageStats] = useState<StorageStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);
  const [backendConnected, setBackendConnected] = useState(true);
  const { reset: resetResearchState } = useResearch();

  const fetchStorageStats = async () => {
    setIsLoadingStats(true);
    try {
      const connected = await checkBackendHealth();
      setBackendConnected(connected);
      if (connected) {
        const stats = await getStorageStats();
        setStorageStats(stats);
      }
    } catch (error) {
      console.error("Failed to fetch storage stats:", error);
      setBackendConnected(false);
    } finally {
      setIsLoadingStats(false);
    }
  };

  useEffect(() => {
    fetchStorageStats();
  }, []);

  const handleClearData = async () => {
    if (!confirm("Are you sure you want to delete all stored data? This cannot be undone.")) {
      return;
    }
    
    setIsClearing(true);
    setClearSuccess(false);
    try {
      await clearAllData();
      resetResearchState(); // Also clear frontend state
      setClearSuccess(true);
      await fetchStorageStats(); // Refresh stats
      setTimeout(() => setClearSuccess(false), 3000);
    } catch (error) {
      console.error("Failed to clear data:", error);
      alert("Failed to clear data. Check if backend is running.");
    } finally {
      setIsClearing(false);
    }
  };

  return (
    <DashboardLayout 
      title="Settings" 
      description="Configure your ScholarAI preferences"
    >
      <div className="max-w-2xl space-y-6">
        {/* Storage Management - Most Important */}
        <Card className="border-accent/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <HardDrive className="h-5 w-5 text-accent" />
              <CardTitle>Storage Management</CardTitle>
            </div>
            <CardDescription>
              Manage local storage used by uploaded documents and processed data
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!backendConnected ? (
              <Alert variant="destructive">
                <AlertDescription>
                  Backend not connected. Start the backend server to view storage stats.
                </AlertDescription>
              </Alert>
            ) : storageStats ? (
              <>
                {/* Storage Usage Display */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <p className="text-2xl font-bold text-foreground">{storageStats.total_mb} MB</p>
                    <p className="text-sm text-muted-foreground">Total Storage Used</p>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <p className="text-2xl font-bold text-foreground">{storageStats.uploads.files + storageStats.processed.files}</p>
                    <p className="text-sm text-muted-foreground">Total Files</p>
                  </div>
                </div>

                {/* Breakdown */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Uploaded Documents</span>
                    <span className="font-medium">{storageStats.uploads.files} files ({storageStats.uploads.mb} MB)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Processed Files</span>
                    <span className="font-medium">{storageStats.processed.files} files ({storageStats.processed.mb} MB)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Vector Database</span>
                    <span className="font-medium">{storageStats.chroma_mb} MB</span>
                  </div>
                </div>

                <Separator />

                {/* Clear Data Button */}
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="text-disagreement font-medium">Clear All Data</Label>
                    <p className="text-xs text-muted-foreground">
                      Delete all uploads, processed files, and session data
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={fetchStorageStats}
                      disabled={isLoadingStats}
                    >
                      {isLoadingStats ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                    </Button>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={handleClearData}
                      disabled={isClearing}
                    >
                      {isClearing ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4 mr-2" />
                      )}
                      {isClearing ? "Clearing..." : "Clear Data"}
                    </Button>
                  </div>
                </div>

                {clearSuccess && (
                  <Alert className="bg-consensus/10 border-consensus/20">
                    <CheckCircle className="h-4 w-4 text-consensus" />
                    <AlertDescription className="text-consensus">
                      All data cleared successfully!
                    </AlertDescription>
                  </Alert>
                )}
              </>
            ) : (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* API Configuration */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-accent" />
              <CardTitle>API Configuration</CardTitle>
            </div>
            <CardDescription>
              Configure your backend API connection settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="api-url">Backend API URL</Label>
              <Input 
                id="api-url" 
                defaultValue="http://localhost:8000" 
                placeholder="http://localhost:8000"
              />
              <p className="text-xs text-muted-foreground">
                The URL where your ScholarAI backend is running
              </p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <div className={`h-2 w-2 rounded-full ${backendConnected ? 'bg-consensus' : 'bg-disagreement'}`} />
              <span className={backendConnected ? 'text-consensus' : 'text-disagreement'}>
                {backendConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Palette className="h-5 w-5 text-accent" />
              <CardTitle>Appearance</CardTitle>
            </div>
            <CardDescription>
              Customize how ScholarAI looks
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Dark Mode</Label>
                <p className="text-xs text-muted-foreground">
                  Use dark theme for the interface
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Compact Mode</Label>
                <p className="text-xs text-muted-foreground">
                  Reduce spacing for denser information display
                </p>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-accent" />
              <CardTitle>Notifications</CardTitle>
            </div>
            <CardDescription>
              Configure notification preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Processing Complete</Label>
                <p className="text-xs text-muted-foreground">
                  Notify when document processing finishes
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Error Alerts</Label>
                <p className="text-xs text-muted-foreground">
                  Show alerts when errors occur
                </p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-end">
          <Button>Save Settings</Button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Settings;
