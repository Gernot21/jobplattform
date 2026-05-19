import { useEffect, useState } from "react";
import Header from "@/components/Header";
import { useI18n } from "@/lib/i18n";
import { api } from "@/lib/api";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Users, FileText, FlaskConical, Trash2, Send, Lock, Unlock } from "lucide-react";

export default function AdminDashboard() {
  const { t } = useI18n();
  const [tab, setTab] = useState("profiles");
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({});
  const [updates, setUpdates] = useState([]);
  const [env, setEnv] = useState("test");
  const [newUpd, setNewUpd] = useState({ title: "", content: "", environment: "test", published: false });

  useEffect(() => {
    refreshUsers();
    refreshStats();
    refreshUpdates();
  }, []);

  const refreshUsers = async () => {
    const { data } = await api.get("/admin/users");
    setUsers(data);
  };
  const refreshStats = async () => {
    const { data } = await api.get("/admin/stats");
    setStats(data);
  };
  const refreshUpdates = async () => {
    const { data } = await api.get("/admin/updates");
    setUpdates(data);
  };

  const block = async (id, blocked) => {
    await api.post(`/admin/users/${id}/block`, null, { params: { blocked } });
    toast.success(blocked ? "Gesperrt" : "Entsperrt");
    refreshUsers();
  };

  const del = async (id) => {
    if (!confirm(t("delete_confirm"))) return;
    await api.delete(`/admin/users/${id}`);
    toast.success("Gelöscht");
    refreshUsers();
    refreshStats();
  };

  const createUpdate = async (e) => {
    e.preventDefault();
    await api.post("/admin/updates", newUpd);
    toast.success("Erstellt");
    setNewUpd({ title: "", content: "", environment: env, published: false });
    refreshUpdates();
  };

  const publish = async (id) => {
    await api.post(`/admin/updates/${id}/publish`);
    toast.success("Veröffentlicht");
    refreshUpdates();
  };

  const deleteUpd = async (id) => {
    if (!confirm(t("delete_confirm"))) return;
    await api.delete(`/admin/updates/${id}`);
    refreshUpdates();
  };

  const StatCard = ({ label, value, testid }) => (
    <Card data-testid={testid}>
      <CardContent className="p-5">
        <div className="text-xs uppercase tracking-wider text-slate-500 font-medium">{label}</div>
        <div className="font-display text-3xl font-bold text-slate-900 mt-1">{value ?? "–"}</div>
      </CardContent>
    </Card>
  );

  const filteredUpdates = updates.filter((u) => u.environment === env);

  return (
    <div className="min-h-screen">
      <Header title={t("adminPanel")} />
      <main className="max-w-7xl mx-auto px-6 lg:px-8 py-8" data-testid="admin-dashboard">
        <h1 className="font-display text-3xl font-bold text-slate-900 mb-1">{t("adminPanel")}</h1>
        <p className="text-slate-500 mb-8">Backend · Superuser</p>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8" data-testid="admin-stats">
          <StatCard label={t("user")} value={stats.users} testid="stat-users" />
          <StatCard label={t("employee") + "s"} value={stats.employees} testid="stat-employees" />
          <StatCard label={t("employer") + "s"} value={stats.employers} testid="stat-employers" />
          <StatCard label={t("jobs")} value={stats.jobs} testid="stat-jobs" />
          <StatCard label={t("applications")} value={stats.applications} testid="stat-apps" />
        </div>

        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="bg-white border border-slate-200 p-1">
            <TabsTrigger value="profiles" data-testid="admin-tab-profiles"><Users className="w-4 h-4 mr-2" />{t("profiles")}</TabsTrigger>
            <TabsTrigger value="updates" data-testid="admin-tab-updates"><FileText className="w-4 h-4 mr-2" />{t("updates")}</TabsTrigger>
          </TabsList>

          <TabsContent value="profiles" className="mt-6">
            <Card>
              <CardHeader><CardTitle className="font-display">{t("profiles")}</CardTitle></CardHeader>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 text-slate-600 text-left">
                      <tr>
                        <th className="px-4 py-3 font-medium">{t("email")}</th>
                        <th className="px-4 py-3 font-medium">{t("role")}</th>
                        <th className="px-4 py-3 font-medium">Status</th>
                        <th className="px-4 py-3 font-medium text-right">—</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id} className="border-t border-slate-100" data-testid={`admin-user-${u.id}`}>
                          <td className="px-4 py-3 font-medium text-slate-900">{u.email}</td>
                          <td className="px-4 py-3"><Badge variant="outline">{u.role}</Badge></td>
                          <td className="px-4 py-3">
                            {u.blocked
                              ? <Badge className="bg-red-50 text-red-700 border-red-200">{t("blocked")}</Badge>
                              : <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Aktiv</Badge>}
                          </td>
                          <td className="px-4 py-3 text-right space-x-2">
                            {u.role !== "admin" && (
                              <>
                                <Button size="sm" variant="outline" onClick={() => block(u.id, !u.blocked)} data-testid={`block-${u.id}`}>
                                  {u.blocked ? <Unlock className="w-3.5 h-3.5 mr-1" /> : <Lock className="w-3.5 h-3.5 mr-1" />}
                                  {u.blocked ? t("unblock") : t("block")}
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => del(u.id)} data-testid={`delete-user-${u.id}`}>
                                  <Trash2 className="w-3.5 h-3.5 text-red-500" />
                                </Button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="updates" className="mt-6 space-y-6">
            <div className="flex items-center gap-3">
              <FlaskConical className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-medium text-slate-700">{t("environment")}:</span>
              <Select value={env} onValueChange={setEnv}>
                <SelectTrigger className="w-44" data-testid="env-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="test">{t("testEnv")}</SelectItem>
                  <SelectItem value="production">{t("production")}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Card>
              <CardHeader><CardTitle className="font-display">{t("addUpdate")}</CardTitle></CardHeader>
              <CardContent>
                <form onSubmit={createUpdate} className="grid sm:grid-cols-2 gap-5">
                  <div className="sm:col-span-2">
                    <Label>{t("title")}</Label>
                    <Input value={newUpd.title} onChange={(e) => setNewUpd({ ...newUpd, title: e.target.value })} required data-testid="upd-title" className="mt-1.5" />
                  </div>
                  <div className="sm:col-span-2">
                    <Label>{t("content")}</Label>
                    <Textarea value={newUpd.content} onChange={(e) => setNewUpd({ ...newUpd, content: e.target.value })} rows={4} required data-testid="upd-content" className="mt-1.5" />
                  </div>
                  <div>
                    <Label>{t("environment")}</Label>
                    <Select value={newUpd.environment} onValueChange={(v) => setNewUpd({ ...newUpd, environment: v })}>
                      <SelectTrigger className="mt-1.5" data-testid="upd-env"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="test">{t("testEnv")}</SelectItem>
                        <SelectItem value="production">{t("production")}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="sm:col-span-2">
                    <Button type="submit" className="bg-slate-900 hover:bg-slate-800 text-white" data-testid="upd-save">
                      <Send className="w-4 h-4 mr-2" />{t("save")}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <div className="space-y-3">
              {filteredUpdates.map((u) => (
                <Card key={u.id} data-testid={`upd-${u.id}`}>
                  <CardContent className="p-5">
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-display font-semibold text-slate-900">{u.title}</h3>
                          <Badge variant={u.environment === "production" ? "default" : "outline"}>
                            {u.environment === "production" ? t("production") : t("testEnv")}
                          </Badge>
                          {u.published && <Badge className="bg-emerald-50 text-emerald-700 border-emerald-200">Live</Badge>}
                        </div>
                        <p className="text-sm text-slate-600 mt-2 whitespace-pre-wrap">{u.content}</p>
                        <div className="text-xs text-slate-400 mt-2">{new Date(u.created_at).toLocaleString()}</div>
                      </div>
                      <div className="flex gap-2">
                        {!u.published && (
                          <Button size="sm" variant="outline" onClick={() => publish(u.id)} data-testid={`publish-${u.id}`}>
                            <Send className="w-3.5 h-3.5 mr-1" />{t("publish")}
                          </Button>
                        )}
                        <Button size="sm" variant="ghost" onClick={() => deleteUpd(u.id)} data-testid={`delete-upd-${u.id}`}>
                          <Trash2 className="w-3.5 h-3.5 text-red-500" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
              {filteredUpdates.length === 0 && (
                <Card><CardContent className="p-6 text-slate-500" data-testid="no-updates">—</CardContent></Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
