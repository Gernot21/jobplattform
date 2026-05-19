import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ShieldCheck, Sparkles, Briefcase, Languages, CheckCircle2, Lock } from "lucide-react";
import { toast } from "sonner";
import TwoFactorChallenge from "@/components/TwoFactorChallenge";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
const handleGoogleLogin = () => {
  const redirectUrl = window.location.origin + "/auth/callback";
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
};

export default function Landing() {
  const { login } = useAuth();
  const { lang, setLang, t } = useI18n();
  const [adminOpen, setAdminOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [twofa, setTwofa] = useState(null); // {challenge_token}

  const adminLogin = async (e) => {
    e.preventDefault();
    setBusy(true);
    const res = await login(email, password);
    setBusy(false);
    if (res.requires_2fa) {
      setTwofa({ challenge_token: res.challenge_token });
      return;
    }
    if (!res.ok) {
      toast.error(res.error || "Fehler");
    } else {
      toast.success(t("welcome"));
      setAdminOpen(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <div className="bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5" data-testid="brand">
            <div className="w-8 h-8 rounded-md bg-emerald-500/20 ring-1 ring-emerald-400/40 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <span className="font-display font-bold tracking-tight">{t("appName")}</span>
          </div>
          <button
            onClick={() => setLang(lang === "de" ? "en" : "de")}
            className="text-sm text-slate-300 hover:text-white flex items-center gap-1.5"
            data-testid="landing-lang-switch"
          >
            <Languages className="w-4 h-4" />
            {lang === "de" ? "EN" : "DE"}
          </button>
        </div>
      </div>

      <section className="hero-grain border-b border-slate-200 flex-1">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-14 lg:py-20 grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-medium border border-emerald-200 mb-5" data-testid="hero-badge">
              <Sparkles className="w-3.5 h-3.5" /> 20% – 80% · KI-Matching
            </div>
            <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-slate-900 leading-[1.05]" data-testid="hero-title">
              {t("tagline")}
            </h1>
            <p className="mt-5 text-lg text-slate-600 max-w-xl leading-relaxed" data-testid="hero-subtitle">
              {t("subtagline")}
            </p>

            <div className="mt-8 grid grid-cols-3 gap-4 max-w-md">
              {[
                { icon: ShieldCheck, label: t("trustBadge1") },
                { icon: Sparkles, label: t("trustBadge2") },
                { icon: Briefcase, label: t("trustBadge3") },
              ].map((b, i) => (
                <div key={i} className="flex flex-col items-start gap-2" data-testid={`trust-badge-${i}`}>
                  <div className="w-9 h-9 rounded-md bg-white border border-slate-200 flex items-center justify-center">
                    <b.icon className="w-4 h-4 text-emerald-600" />
                  </div>
                  <span className="text-xs font-medium text-slate-700 leading-tight">{b.label}</span>
                </div>
              ))}
            </div>
          </div>

          <Card className="bg-white border-slate-200 shadow-xl shadow-slate-200/50" data-testid="auth-card">
            <CardContent className="p-8 sm:p-10">
              <h2 className="font-display text-2xl font-bold text-slate-900 mb-1">Anmelden</h2>
              <p className="text-sm text-slate-500 mb-6">Sicher mit deinem Google-Konto fortfahren.</p>

              <Button
                onClick={handleGoogleLogin}
                className="w-full bg-white hover:bg-slate-50 text-slate-900 border border-slate-300 py-6 text-base font-medium flex items-center justify-center gap-3"
                data-testid="google-login-btn"
              >
                <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
                  <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.2-.1-2.3-.4-3.5z"/>
                  <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16.1 19 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
                  <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2c-2 1.4-4.5 2.4-7.2 2.4-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/>
                  <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.1 5.6l6.2 5.2c-.4.4 6.6-4.8 6.6-14.8 0-1.2-.1-2.3-.4-3.5z"/>
                </svg>
                Mit Google fortfahren
              </Button>

              <div className="mt-5 flex items-center gap-2 text-xs text-slate-500">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Verschlüsselte Datenübertragung · DSGVO-konform · 2FA-Schutz
              </div>

              <div className="mt-8 pt-5 border-t border-slate-100 text-center">
                <button
                  onClick={() => setAdminOpen(true)}
                  className="text-xs text-slate-500 hover:text-slate-900 inline-flex items-center gap-1.5"
                  data-testid="admin-login-link"
                >
                  <Lock className="w-3 h-3" /> Admin-Login
                </button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <footer className="py-6 border-t border-slate-200 text-center text-sm text-slate-500">
        © {new Date().getFullYear()} {t("appName")} · Schweiz
      </footer>

      {/* Admin login dialog */}
      <Dialog open={adminOpen} onOpenChange={setAdminOpen}>
        <DialogContent className="sm:max-w-md" data-testid="admin-login-dialog">
          <DialogHeader>
            <DialogTitle className="font-display">Admin-Anmeldung</DialogTitle>
          </DialogHeader>
          <form onSubmit={adminLogin} className="space-y-4">
            <div>
              <Label>{t("email")}</Label>
              <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} data-testid="admin-email-input" className="mt-1.5" />
            </div>
            <div>
              <Label>{t("password")}</Label>
              <Input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} data-testid="admin-password-input" className="mt-1.5" />
            </div>
            <Button type="submit" disabled={busy} className="w-full bg-slate-900 hover:bg-slate-800 text-white" data-testid="admin-submit">
              {busy ? "..." : "Anmelden"}
            </Button>
          </form>
        </DialogContent>
      </Dialog>

      {twofa && (
        <TwoFactorChallenge
          challenge_token={twofa.challenge_token}
          onClose={() => setTwofa(null)}
          onSuccess={() => { setTwofa(null); setAdminOpen(false); }}
        />
      )}
    </div>
  );
}
