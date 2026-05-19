import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { ShieldCheck, Sparkles, Briefcase, Languages, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

const HERO_IMG =
  "https://images.unsplash.com/photo-1765366417030-16d9765d920a?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600";

export default function Landing() {
  const { login, register } = useAuth();
  const { lang, setLang, t } = useI18n();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("employee");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    const fn = mode === "login" ? login(email, password) : register(email, password, role);
    const res = await fn;
    setBusy(false);
    if (!res.ok) {
      toast.error(res.error || "Fehler");
    } else {
      toast.success(t("welcome"));
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Top bar */}
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

      {/* Hero */}
      <section className="hero-grain border-b border-slate-200">
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

          {/* Auth card */}
          <Card className="bg-white border-slate-200 shadow-xl shadow-slate-200/50" data-testid="auth-card">
            <CardContent className="p-6 sm:p-8">
              <Tabs value={mode} onValueChange={setMode} className="w-full">
                <TabsList className="grid grid-cols-2 w-full mb-6">
                  <TabsTrigger value="login" data-testid="tab-login">{t("login")}</TabsTrigger>
                  <TabsTrigger value="register" data-testid="tab-register">{t("register")}</TabsTrigger>
                </TabsList>

                <form onSubmit={submit} className="space-y-4">
                  {mode === "register" && (
                    <div>
                      <Label className="text-sm font-medium text-slate-700">{t("role")}</Label>
                      <div className="mt-2 grid grid-cols-2 gap-2">
                        {["employee", "employer"].map((r) => (
                          <button
                            type="button"
                            key={r}
                            onClick={() => setRole(r)}
                            data-testid={`role-${r}`}
                            className={`px-4 py-3 rounded-lg border text-sm font-medium transition-all ${
                              role === r
                                ? "bg-slate-900 text-white border-slate-900"
                                : "bg-white text-slate-700 border-slate-200 hover:border-slate-300"
                            }`}
                          >
                            {t(r)}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  <div>
                    <Label htmlFor="email">{t("email")}</Label>
                    <Input
                      id="email"
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="name@firma.ch"
                      data-testid="auth-email-input"
                      className="mt-1.5"
                    />
                  </div>
                  <div>
                    <Label htmlFor="password">{t("password")}</Label>
                    <Input
                      id="password"
                      type="password"
                      required
                      minLength={6}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      data-testid="auth-password-input"
                      className="mt-1.5"
                    />
                  </div>

                  <Button
                    type="submit"
                    disabled={busy}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-6 text-base font-medium"
                    data-testid="auth-submit-btn"
                  >
                    {busy ? "..." : mode === "login" ? t("login") : t("register")}
                  </Button>
                </form>

                <div className="mt-5 flex items-center gap-2 text-xs text-slate-500">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Verschlüsselte Datenübertragung · DSGVO-konform
                </div>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer mini */}
      <footer className="mt-auto py-6 border-t border-slate-200 text-center text-sm text-slate-500">
        © {new Date().getFullYear()} {t("appName")} · Schweiz
      </footer>
    </div>
  );
}
