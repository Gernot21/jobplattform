import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ShieldCheck, ShieldOff, ScanLine } from "lucide-react";
import { toast } from "sonner";

export default function TwoFactorSettings() {
  const { user, hydrate } = useAuth();
  const [setupData, setSetupData] = useState(null);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [disableOpen, setDisableOpen] = useState(false);
  const [disableCode, setDisableCode] = useState("");

  const enabled = !!user?.totp_enabled;

  const beginSetup = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/auth/2fa/setup");
      setSetupData(data);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Fehler");
    } finally {
      setBusy(false);
    }
  };

  const confirmEnable = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/auth/2fa/enable", { code });
      toast.success("2FA aktiviert");
      setSetupData(null);
      setCode("");
      await hydrate();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Code ungültig");
    } finally {
      setBusy(false);
    }
  };

  const disable = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/auth/2fa/disable", { code: disableCode });
      toast.success("2FA deaktiviert");
      setDisableOpen(false);
      setDisableCode("");
      await hydrate();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Code ungültig");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card data-testid="twofa-settings">
      <CardHeader>
        <CardTitle className="font-display flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-600" />
          2-Faktor-Authentifizierung
          {enabled && <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Aktiv</Badge>}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!enabled && !setupData && (
          <div>
            <p className="text-sm text-slate-600 mb-4">
              Schütze dein Konto zusätzlich mit einer Authenticator-App (Google Authenticator, Authy, 1Password …).
            </p>
            <Button onClick={beginSetup} disabled={busy} className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="twofa-setup-btn">
              <ScanLine className="w-4 h-4 mr-2" />
              2FA einrichten
            </Button>
          </div>
        )}

        {setupData && (
          <form onSubmit={confirmEnable} className="space-y-4">
            <p className="text-sm text-slate-600">
              1. Scanne den QR-Code mit deiner Authenticator-App.<br />
              2. Gib den 6-stelligen Code zur Bestätigung ein.
            </p>
            <div className="flex items-start gap-6 flex-wrap">
              <img
                src={setupData.qr_data_url}
                alt="2FA QR Code"
                className="w-44 h-44 border border-slate-200 rounded-lg bg-white"
                data-testid="twofa-qr-img"
              />
              <div className="flex-1 min-w-[200px]">
                <div className="text-xs uppercase text-slate-500 font-medium tracking-wider">Geheimer Schlüssel</div>
                <code className="block mt-1 text-sm font-mono text-slate-800 bg-slate-50 px-3 py-2 rounded border border-slate-200 break-all" data-testid="twofa-secret">
                  {setupData.secret}
                </code>
                <p className="text-xs text-slate-500 mt-2">Falls du den QR-Code nicht scannen kannst, gib diesen Schlüssel manuell ein.</p>
              </div>
            </div>
            <div>
              <Input
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                placeholder="123456"
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                className="text-center text-xl tracking-[0.4em] font-display max-w-xs"
                data-testid="twofa-enable-code-input"
              />
            </div>
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={() => { setSetupData(null); setCode(""); }} data-testid="twofa-cancel-setup">
                Abbrechen
              </Button>
              <Button type="submit" disabled={busy || code.length !== 6} className="bg-emerald-600 hover:bg-emerald-700 text-white" data-testid="twofa-enable-btn">
                {busy ? "..." : "Aktivieren"}
              </Button>
            </div>
          </form>
        )}

        {enabled && !setupData && (
          <div>
            <p className="text-sm text-slate-600 mb-4">2FA ist aktiv. Bei jedem Login wirst du nach deinem Authenticator-Code gefragt.</p>
            <Button variant="outline" onClick={() => setDisableOpen(true)} data-testid="twofa-disable-btn">
              <ShieldOff className="w-4 h-4 mr-2" />
              2FA deaktivieren
            </Button>
          </div>
        )}

        <Dialog open={disableOpen} onOpenChange={setDisableOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>2FA deaktivieren</DialogTitle>
              <DialogDescription>Bestätige die Deaktivierung mit dem aktuellen TOTP-Code.</DialogDescription>
            </DialogHeader>
            <form onSubmit={disable} className="space-y-4">
              <p className="text-sm text-slate-600">Bitte zur Bestätigung den aktuellen 6-stelligen Code eingeben.</p>
              <Input
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                required
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ""))}
                className="text-center text-xl tracking-[0.4em] font-display"
                data-testid="twofa-disable-code-input"
              />
              <Button type="submit" disabled={busy || disableCode.length !== 6} className="w-full" data-testid="twofa-disable-confirm">
                Deaktivieren
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
