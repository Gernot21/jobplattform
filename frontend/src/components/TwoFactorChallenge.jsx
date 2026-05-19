import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ShieldCheck } from "lucide-react";
import { toast } from "sonner";

export default function TwoFactorChallenge({ challenge_token, onClose, onSuccess }) {
  const { hydrate } = useAuth();
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.post("/auth/2fa/login", { challenge_token, code });
      localStorage.setItem("token", data.token);
      await hydrate();
      onSuccess?.();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Code ungültig");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Dialog open={true} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent className="sm:max-w-md" data-testid="twofa-challenge-dialog">
        <DialogHeader>
          <DialogTitle className="font-display flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            2-Faktor-Authentifizierung
          </DialogTitle>
          <DialogDescription>Bestätige deinen Login mit dem Code aus deiner Authenticator-App.</DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-4">
          <p className="text-sm text-slate-600">Bitte den 6-stelligen Code aus deiner Authenticator-App eingeben.</p>
          <Input
            inputMode="numeric"
            pattern="[0-9]{6}"
            maxLength={6}
            placeholder="123456"
            required
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            className="text-center text-2xl tracking-[0.4em] font-display"
            data-testid="twofa-code-input"
          />
          <Button
            type="submit"
            disabled={busy || code.length !== 6}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white"
            data-testid="twofa-submit"
          >
            {busy ? "..." : "Bestätigen"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
