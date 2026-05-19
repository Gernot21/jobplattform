import { useAuth } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { ShieldCheck, LogOut, Languages } from "lucide-react";

export default function Header({ title }) {
  const { user, logout } = useAuth();
  const { lang, setLang, t } = useI18n();

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200" data-testid="app-header">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-slate-900 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5 text-emerald-400" strokeWidth={2.2} />
          </div>
          <div className="leading-tight">
            <div className="font-display font-bold text-slate-900 text-lg" data-testid="app-name">
              {t("appName")}
            </div>
            <div className="text-xs text-slate-500">{title || "20% – 80%"}</div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setLang(lang === "de" ? "en" : "de")}
            className="text-sm font-medium text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-md hover:bg-slate-100 flex items-center gap-1.5"
            data-testid="lang-switch-btn"
          >
            <Languages className="w-4 h-4" />
            {lang.toUpperCase()}
          </button>
          {user && (
            <>
              <span className="hidden sm:inline text-sm text-slate-500" data-testid="header-user-email">
                {user.email}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                data-testid="logout-btn"
                className="text-slate-600"
              >
                <LogOut className="w-4 h-4 mr-1.5" />
                {t("logout")}
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
