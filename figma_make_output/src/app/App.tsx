import { useState } from "react";
import {
  CheckSquare,
  Square,
  Plus,
  ChevronRight,
  MapPin,
  Calendar,
  Search,
  X,
  Luggage,
  Backpack,
  ShoppingBag,
  Trash2,
  ChevronDown,
  ChevronUp,
  Shirt,
  Zap,
  BookOpen,
  Package,
  Menu,
  ArrowLeft,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

type Bag = { id: number; name: string; icon: "luggage" | "backpack" | "tote" };
type Item = { id: number; name: string; packed: boolean; category: string; quantity: number; bagId: number | null };
type Trip = { id: number; name: string; destination: string; date: string };

// ─── Constants ───────────────────────────────────────────────────────────────

const CATEGORIES = [
  { name: "Clothing",    icon: Shirt,    color: "bg-amber-100 text-amber-800" },
  { name: "Electronics", icon: Zap,      color: "bg-blue-100 text-blue-800" },
  { name: "Documents",   icon: BookOpen, color: "bg-emerald-100 text-emerald-700" },
  { name: "Gear",        icon: Package,  color: "bg-orange-100 text-orange-800" },
];

const BAG_COLORS = [
  "bg-amber-100 text-amber-800",
  "bg-blue-100 text-blue-800",
  "bg-emerald-100 text-emerald-700",
  "bg-rose-100 text-rose-800",
  "bg-violet-100 text-violet-800",
];

// ─── Seed data ────────────────────────────────────────────────────────────────

const TRIPS: Trip[] = [
  { id: 1, name: "Lisbon & Porto",          destination: "Portugal", date: "Jul 12 – Jul 26" },
  { id: 2, name: "Weekend in the Dolomites", destination: "Italy",   date: "Aug 3 – Aug 6" },
  { id: 3, name: "Tokyo Photo Trip",         destination: "Japan",   date: "Sep 18 – Oct 2" },
];

const INIT_BAGS: Bag[] = [
  { id: 1, name: "Large suitcase", icon: "luggage" },
  { id: 2, name: "Carry-on",       icon: "luggage" },
  { id: 3, name: "Day pack",       icon: "backpack" },
  { id: 4, name: "Personal tote",  icon: "tote" },
];

const INIT_ITEMS: Item[] = [
  { id: 1,  name: "Merino wool t-shirts (3)",    packed: true,  category: "Clothing",     quantity: 3, bagId: 1 },
  { id: 2,  name: "Linen trousers",              packed: true,  category: "Clothing",     quantity: 1, bagId: 1 },
  { id: 3,  name: "Light rain jacket",           packed: false, category: "Clothing",     quantity: 1, bagId: 1 },
  { id: 4,  name: "Walking sandals",             packed: false, category: "Clothing",     quantity: 1, bagId: 1 },
  { id: 5,  name: "Swimsuit",                    packed: false, category: "Clothing",     quantity: 1, bagId: 1 },
  { id: 6,  name: "Passport & copies",           packed: true,  category: "Documents",    quantity: 1, bagId: 2 },
  { id: 7,  name: "Travel insurance docs",       packed: true,  category: "Documents",    quantity: 1, bagId: 2 },
  { id: 8,  name: "International plug adapter",  packed: false, category: "Electronics",  quantity: 1, bagId: 2 },
  { id: 9,  name: "USB-C charging cables",       packed: true,  category: "Electronics",  quantity: 2, bagId: 2 },
  { id: 10, name: "Noise-cancelling headphones", packed: false, category: "Electronics",  quantity: 1, bagId: 3 },
  { id: 11, name: "Portable battery pack",       packed: true,  category: "Electronics",  quantity: 1, bagId: 3 },
  { id: 12, name: "Microfiber towel",            packed: true,  category: "Gear",         quantity: 1, bagId: 3 },
  { id: 13, name: "Sunscreen SPF 50",            packed: false, category: "Gear",         quantity: 1, bagId: 3 },
  { id: 14, name: "Sunglasses",                  packed: false, category: "Gear",         quantity: 1, bagId: 4 },
  { id: 15, name: "Water bottle",                packed: true,  category: "Gear",         quantity: 1, bagId: null },
  { id: 16, name: "Phrase book",                 packed: false, category: "Documents",    quantity: 1, bagId: null },
];

// ─── Small helpers ────────────────────────────────────────────────────────────

function BagIcon({ icon, size = 15 }: { icon: Bag["icon"]; size?: number }) {
  if (icon === "backpack") return <Backpack size={size} />;
  if (icon === "tote")     return <ShoppingBag size={size} />;
  return <Luggage size={size} />;
}

function bagStats(bag: Bag, items: Item[]) {
  const bi = items.filter((i) => i.bagId === bag.id);
  const p  = bi.filter((i) => i.packed).length;
  return { total: bi.length, packed: p, pct: bi.length > 0 ? Math.round((p / bi.length) * 100) : 0 };
}

// ─── BagCard ─────────────────────────────────────────────────────────────────

function BagCard({
  bag, items, colorClass, onDelete, onToggleAll,
}: {
  bag: Bag; items: Item[]; colorClass: string;
  onDelete: () => void; onToggleAll: (packed: boolean) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const { total, packed, pct } = bagStats(bag, items);

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden mb-3">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-border/60">
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${colorClass}`}>
          <BagIcon icon={bag.icon} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{bag.name}</span>
            {pct === 100 && total > 0 && (
              <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full font-medium">Packed</span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1">
            <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-accent rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs text-muted-foreground shrink-0" style={{ fontFamily: "'DM Mono', monospace" }}>
              {packed}/{total}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-0.5 shrink-0">
          {total > 0 && (
            <button
              onClick={() => onToggleAll(packed < total)}
              className="text-xs text-muted-foreground hover:text-foreground px-2 py-1.5 rounded hover:bg-muted/60 transition-colors hidden sm:block"
            >
              {packed < total ? "Pack all" : "Unpack all"}
            </button>
          )}
          <button onClick={onDelete} className="p-2 text-muted-foreground hover:text-destructive transition-colors rounded hover:bg-destructive/10">
            <Trash2 size={13} />
          </button>
          <button onClick={() => setCollapsed((v) => !v)} className="p-2 text-muted-foreground hover:text-foreground transition-colors rounded hover:bg-muted/60">
            {collapsed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
          </button>
        </div>
      </div>
      {!collapsed && (
        <div>
          {items.length === 0 ? (
            <p className="text-xs text-muted-foreground px-4 py-4 italic">No items in this bag yet.</p>
          ) : (
            items.map((item) => (
              <div key={item.id} className="flex items-center gap-3 px-4 py-3.5 border-b border-border/30 last:border-b-0 hover:bg-muted/10 transition-colors">
                <span className={`flex-1 text-sm ${item.packed ? "line-through text-muted-foreground" : ""}`}>{item.name}</span>
                <span className="text-xs text-muted-foreground">{item.category}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// ─── AddItemSheet ─────────────────────────────────────────────────────────────

function AddItemSheet({
  bags, onAdd, onClose,
}: {
  bags: Bag[];
  onAdd: (name: string, category: string, bagId: number | null) => void;
  onClose: () => void;
}) {
  const [name, setName]         = useState("");
  const [category, setCategory] = useState(CATEGORIES[0].name);
  const [bagId, setBagId]       = useState<number | null>(bags[0]?.id ?? null);

  const submit = () => {
    if (!name.trim()) return;
    onAdd(name.trim(), category, bagId);
    onClose();
  };

  return (
    <>
      {/* Scrim */}
      <div className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm" onClick={onClose} />

      {/* Sheet — slides up from bottom on mobile, centered modal on desktop */}
      <div className="fixed z-50 inset-x-0 bottom-0 md:inset-0 md:flex md:items-center md:justify-center md:p-8">
        <div className="bg-card rounded-t-2xl md:rounded-2xl shadow-2xl w-full md:max-w-md border border-border/60">
          {/* Handle (mobile only) */}
          <div className="flex justify-center pt-3 pb-1 md:hidden">
            <div className="w-10 h-1 rounded-full bg-border" />
          </div>

          <div className="px-5 pt-4 pb-2 flex items-center justify-between">
            <h2 className="text-base font-medium" style={{ fontFamily: "'DM Serif Display', serif" }}>
              Add item
            </h2>
            <button onClick={onClose} className="p-1.5 text-muted-foreground hover:text-foreground transition-colors rounded-md hover:bg-muted">
              <X size={16} />
            </button>
          </div>

          <div className="px-5 pb-6 space-y-4">
            <input
              autoFocus
              type="text"
              placeholder="Item name..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); if (e.key === "Escape") onClose(); }}
              className="w-full bg-input-background border border-border rounded-lg px-3 py-3 text-sm focus:outline-none focus:ring-1 focus:ring-ring placeholder:text-muted-foreground"
            />

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-muted-foreground block mb-1.5">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-input-background border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {CATEGORIES.map((c) => <option key={c.name}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-muted-foreground block mb-1.5">Bag</label>
                <select
                  value={bagId ?? ""}
                  onChange={(e) => setBagId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full bg-input-background border border-border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  <option value="">No bag</option>
                  {bags.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </div>
            </div>

            <button
              onClick={submit}
              className="w-full bg-accent text-accent-foreground py-3 rounded-xl text-sm font-medium hover:bg-accent/90 transition-colors"
            >
              Add to list
            </button>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── TripsDrawer (mobile) ─────────────────────────────────────────────────────

function TripsDrawer({
  trips, packed, total, onClose,
}: {
  trips: Trip[]; packed: number; total: number; onClose: () => void;
}) {
  return (
    <>
      <div className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed z-50 inset-y-0 left-0 w-72 bg-sidebar flex flex-col shadow-2xl">
        <div className="px-5 py-5 border-b border-sidebar-border flex items-center justify-between">
          <div>
            <span className="text-lg text-foreground tracking-tight" style={{ fontFamily: "'DM Serif Display', serif" }}>packwell.</span>
            <p className="text-xs text-muted-foreground mt-0.5 tracking-wide uppercase">travel inventory</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-muted-foreground hover:text-foreground"><X size={18} /></button>
        </div>
        <div className="px-4 py-5 flex-1 overflow-y-auto">
          <p className="text-xs font-medium tracking-widest uppercase text-muted-foreground px-2 mb-3">Trips</p>
          <div className="space-y-1">
            {trips.map((trip, i) => {
              const tPacked = i === 0 ? packed : 0;
              const tTotal  = i === 0 ? total  : [9, 18][i - 1] ?? 0;
              const tPct    = tTotal > 0 ? Math.round((tPacked / tTotal) * 100) : 0;
              return (
                <div key={trip.id} className={`px-3 py-3 rounded-lg ${i === 0 ? "bg-sidebar-accent" : "text-muted-foreground"}`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{trip.name}</p>
                      <div className="flex items-center gap-1 mt-0.5 text-xs opacity-70">
                        <MapPin size={10} />{trip.destination}
                      </div>
                    </div>
                    {i === 0 && <ChevronRight size={14} className="text-accent" />}
                  </div>
                  <div className="mt-2">
                    <div className="h-1 bg-sidebar-border rounded-full overflow-hidden">
                      <div className="h-full bg-accent rounded-full" style={{ width: `${tPct}%` }} />
                    </div>
                    <p className="text-xs mt-1 opacity-60">{tPacked}/{tTotal} packed</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <div className="px-4 py-4 border-t border-sidebar-border">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-sidebar-accent transition-colors">
            <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center text-white text-xs font-medium">L</div>
            <div>
              <p className="text-sm font-medium">Luna Sofia</p>
              <p className="text-xs text-muted-foreground">3 active trips</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  const [items, setItems]             = useState<Item[]>(INIT_ITEMS);
  const [bags, setBags]               = useState<Bag[]>(INIT_BAGS);
  const [view, setView]               = useState<"bags" | "category" | "list">("bags");
  const [searchQuery, setSearchQuery] = useState("");
  const [showAdd, setShowAdd]         = useState(false);
  const [addingBag, setAddingBag]     = useState(false);
  const [newBagName, setNewBagName]   = useState("");
  const [newBagIcon, setNewBagIcon]   = useState<Bag["icon"]>("luggage");
  const [showDrawer, setShowDrawer]   = useState(false);
  const [showSearch, setShowSearch]   = useState(false);

  const toggleItem   = (id: number) => setItems((p) => p.map((i) => i.id === id ? { ...i, packed: !i.packed } : i));
  const toggleAllBag = (bagId: number, packed: boolean) => setItems((p) => p.map((i) => i.bagId === bagId ? { ...i, packed } : i));
  const deleteBag    = (bagId: number) => { setBags((p) => p.filter((b) => b.id !== bagId)); setItems((p) => p.map((i) => i.bagId === bagId ? { ...i, bagId: null } : i)); };

  const addItem = (name: string, category: string, bagId: number | null) =>
    setItems((p) => [...p, { id: Date.now(), name, packed: false, category, quantity: 1, bagId }]);

  const addBag = () => {
    if (!newBagName.trim()) return;
    setBags((p) => [...p, { id: Date.now(), name: newBagName.trim(), icon: newBagIcon }]);
    setNewBagName("");
    setAddingBag(false);
  };

  const packed   = items.filter((i) => i.packed).length;
  const total    = items.length;
  const progress = total > 0 ? Math.round((packed / total) * 100) : 0;

  const unbagged         = items.filter((i) => i.bagId === null);
  const filteredUnbagged = unbagged.filter((i) => i.name.toLowerCase().includes(searchQuery.toLowerCase()));

  const filtered = (list: Item[]) => list.filter((i) => i.name.toLowerCase().includes(searchQuery.toLowerCase()));

  return (
    <div className="min-h-screen bg-background text-foreground flex" style={{ fontFamily: "'Inter', sans-serif" }}>

      {/* ── Desktop sidebar ── */}
      <aside className="hidden md:flex w-64 shrink-0 bg-sidebar border-r border-sidebar-border flex-col">
        <div className="px-6 py-6 border-b border-sidebar-border">
          <span className="text-xl text-foreground tracking-tight" style={{ fontFamily: "'DM Serif Display', serif" }}>packwell.</span>
          <p className="text-xs text-muted-foreground mt-0.5 tracking-wide uppercase">travel inventory</p>
        </div>
        <div className="px-4 py-5 flex-1 overflow-y-auto">
          <div className="flex items-center justify-between mb-3 px-2">
            <span className="text-xs font-medium tracking-widest uppercase text-muted-foreground">Trips</span>
            <button className="text-muted-foreground hover:text-foreground transition-colors"><Plus size={14} /></button>
          </div>
          <div className="space-y-1">
            {TRIPS.map((trip, i) => {
              const tPacked = i === 0 ? packed : 0;
              const tTotal  = i === 0 ? total  : [9, 18][i - 1] ?? 0;
              const tPct    = tTotal > 0 ? Math.round((tPacked / tTotal) * 100) : 0;
              return (
                <div key={trip.id} className={`px-3 py-3 rounded-md transition-colors ${i === 0 ? "bg-sidebar-accent text-foreground" : "text-muted-foreground"}`}>
                  <div className="flex items-start justify-between">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{trip.name}</p>
                      <div className="flex items-center gap-1 mt-0.5"><MapPin size={10} /><span className="text-xs truncate">{trip.destination}</span></div>
                    </div>
                    {i === 0 && <ChevronRight size={14} className="mt-0.5 shrink-0 text-accent" />}
                  </div>
                  <div className="mt-2">
                    <div className="h-1 bg-sidebar-border rounded-full overflow-hidden">
                      <div className="h-full bg-accent rounded-full transition-all" style={{ width: `${tPct}%` }} />
                    </div>
                    <p className="text-xs mt-1 opacity-70">{tPacked}/{tTotal} packed</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <div className="px-4 py-4 border-t border-sidebar-border">
          <div className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-sidebar-accent transition-colors cursor-pointer">
            <div className="w-7 h-7 rounded-full bg-accent flex items-center justify-center text-white text-xs font-medium">L</div>
            <div>
              <p className="text-sm font-medium">Luna Sofia</p>
              <p className="text-xs text-muted-foreground">3 active trips</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Mobile / main content ── */}
      <div className="flex-1 flex flex-col min-h-screen overflow-hidden">

        {/* Mobile top nav */}
        <header className="md:hidden sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border px-4 py-3 flex items-center justify-between">
          <button onClick={() => setShowDrawer(true)} className="p-2 -ml-2 text-muted-foreground hover:text-foreground">
            <Menu size={20} />
          </button>
          <span className="text-lg tracking-tight" style={{ fontFamily: "'DM Serif Display', serif" }}>packwell.</span>
          <button onClick={() => setShowSearch((v) => !v)} className="p-2 -mr-2 text-muted-foreground hover:text-foreground">
            <Search size={18} />
          </button>
        </header>

        {/* Mobile search bar (expanded) */}
        {showSearch && (
          <div className="md:hidden px-4 py-2 border-b border-border bg-background">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                autoFocus
                type="text"
                placeholder="Search items..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-input-background border border-border rounded-lg pl-8 pr-8 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
              />
              <button onClick={() => { setSearchQuery(""); setShowSearch(false); }} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                <X size={13} />
              </button>
            </div>
          </div>
        )}

        <main className="flex-1 overflow-y-auto">
          {/* Trip header */}
          <div className="px-4 md:px-8 pt-5 md:pt-8 pb-5 md:pb-6 border-b border-border">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h1 className="text-2xl md:text-3xl text-foreground leading-tight" style={{ fontFamily: "'DM Serif Display', serif" }}>
                  Lisbon & Porto
                </h1>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5">
                  <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                    <MapPin size={13} /><span>Portugal</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-muted-foreground text-sm">
                    <Calendar size={13} /><span>Jul 12 – Jul 26, 2026</span>
                  </div>
                </div>
              </div>
              {/* Desktop add button */}
              <button
                onClick={() => setShowAdd(true)}
                className="hidden md:flex items-center gap-2 bg-accent text-accent-foreground px-4 py-2 rounded-md text-sm font-medium hover:bg-accent/90 transition-colors shrink-0"
              >
                <Plus size={15} />Add item
              </button>
            </div>

            {/* Progress bar */}
            <div className="mt-4">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs tracking-widest uppercase text-muted-foreground font-medium">Overall progress</span>
                <span className="text-sm font-medium" style={{ fontFamily: "'DM Mono', monospace" }}>{packed}/{total}</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-accent rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-xs text-muted-foreground mt-1.5">{progress}% — {total - packed} still to pack</p>
            </div>
          </div>

          <div className="px-4 md:px-8 py-4 md:py-6">
            {/* Bag chips — horizontal scroll on mobile */}
            <div className="flex gap-2 overflow-x-auto pb-1 mb-5 -mx-4 px-4 md:mx-0 md:px-0 md:flex-wrap scrollbar-none">
              {bags.map((bag, idx) => {
                const { total: bt, packed: bp, pct } = bagStats(bag, items);
                return (
                  <div key={bag.id} className="flex items-center gap-2 px-3 py-2 rounded-xl border border-border bg-card text-sm shrink-0">
                    <div className={`w-6 h-6 rounded flex items-center justify-center ${BAG_COLORS[idx % BAG_COLORS.length]}`}>
                      <BagIcon icon={bag.icon} size={13} />
                    </div>
                    <span className="font-medium whitespace-nowrap">{bag.name}</span>
                    <span className="text-muted-foreground text-xs" style={{ fontFamily: "'DM Mono', monospace" }}>{bp}/{bt}</span>
                    {pct === 100 && bt > 0 && <span className="text-xs text-emerald-600">✓</span>}
                  </div>
                );
              })}
              {unbagged.length > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-dashed border-border text-sm text-muted-foreground shrink-0">
                  <X size={12} /><span className="whitespace-nowrap">{unbagged.length} unbagged</span>
                </div>
              )}
            </div>

            {/* View toggle + desktop search */}
            <div className="flex items-center justify-between gap-3 mb-4">
              <div className="flex items-center bg-muted rounded-lg p-0.5 w-full md:w-auto">
                {(["bags", "category", "list"] as const).map((v) => (
                  <button
                    key={v}
                    onClick={() => setView(v)}
                    className={`flex-1 md:flex-none px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      view === v ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {v === "bags" ? "By bag" : v === "category" ? "By category" : "All items"}
                  </button>
                ))}
              </div>

              {/* Desktop search */}
              <div className="relative hidden md:block">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search items..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-input-background border border-border rounded-md pl-8 pr-8 py-2 text-sm w-52 placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
                />
                {searchQuery && (
                  <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                    <X size={13} />
                  </button>
                )}
              </div>
            </div>

            {/* ── By bag ── */}
            {view === "bags" && (
              <div>
                {bags.map((bag, idx) => (
                  <BagCard
                    key={bag.id}
                    bag={bag}
                    items={filtered(items.filter((i) => i.bagId === bag.id))}
                    colorClass={BAG_COLORS[idx % BAG_COLORS.length]}
                    onDelete={() => deleteBag(bag.id)}
                    onToggleAll={(p) => toggleAllBag(bag.id, p)}
                  />
                ))}

                {filteredUnbagged.length > 0 && (
                  <div className="bg-card border border-dashed border-border rounded-xl overflow-hidden mb-3">
                    <div className="flex items-center gap-3 px-4 py-3 border-b border-border/40">
                      <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-muted text-muted-foreground shrink-0">
                        <X size={14} />
                      </div>
                      <span className="text-sm font-medium text-muted-foreground">Unbagged</span>
                      <span className="text-xs text-muted-foreground ml-auto" style={{ fontFamily: "'DM Mono', monospace" }}>
                        {filteredUnbagged.filter((i) => i.packed).length}/{filteredUnbagged.length}
                      </span>
                    </div>
                    {filteredUnbagged.map((item) => (
                      <div
                        key={item.id}
                        className="flex items-center gap-3 px-4 py-4 border-b border-border/30 last:border-b-0 hover:bg-muted/10 transition-colors cursor-pointer"
                        onClick={() => toggleItem(item.id)}
                      >
                        <button className="shrink-0 text-muted-foreground">
                          {item.packed ? <CheckSquare size={18} className="text-accent" /> : <Square size={18} />}
                        </button>
                        <span className={`flex-1 text-sm ${item.packed ? "line-through text-muted-foreground" : ""}`}>{item.name}</span>
                      </div>
                    ))}
                  </div>
                )}

                {addingBag ? (
                  <div className="bg-card border border-accent/40 rounded-xl p-4 flex flex-wrap items-center gap-3">
                    <div className="flex items-center gap-2">
                      {(["luggage", "backpack", "tote"] as Bag["icon"][]).map((icon) => (
                        <button
                          key={icon}
                          onClick={() => setNewBagIcon(icon)}
                          className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors ${newBagIcon === icon ? "bg-accent text-white" : "bg-muted text-muted-foreground"}`}
                        >
                          <BagIcon icon={icon} />
                        </button>
                      ))}
                    </div>
                    <input
                      autoFocus
                      type="text"
                      placeholder="Bag name (e.g. Blue duffel)..."
                      value={newBagName}
                      onChange={(e) => setNewBagName(e.target.value)}
                      onKeyDown={(e) => { if (e.key === "Enter") addBag(); if (e.key === "Escape") setAddingBag(false); }}
                      className="flex-1 min-w-0 bg-transparent text-sm focus:outline-none placeholder:text-muted-foreground"
                    />
                    <button onClick={addBag} className="bg-accent text-accent-foreground px-3 py-2 rounded-lg text-xs font-medium hover:bg-accent/90 transition-colors">
                      Add bag
                    </button>
                    <button onClick={() => setAddingBag(false)} className="text-muted-foreground hover:text-foreground"><X size={15} /></button>
                  </div>
                ) : (
                  <button
                    onClick={() => setAddingBag(true)}
                    className="w-full flex items-center justify-center gap-2 text-muted-foreground hover:text-foreground border border-dashed border-border rounded-xl py-3.5 text-sm transition-colors hover:bg-muted/20"
                  >
                    <Plus size={14} />Add a bag
                  </button>
                )}
              </div>
            )}

            {/* ── By category ── */}
            {view === "category" && (
              <div>
                {CATEGORIES.map((cat) => {
                  const catItems  = filtered(items.filter((i) => i.category === cat.name));
                  const catPacked = catItems.filter((i) => i.packed).length;
                  const catPct    = catItems.length > 0 ? Math.round((catPacked / catItems.length) * 100) : 0;
                  const Icon      = cat.icon;
                  return (
                    <div key={cat.name} className="bg-card border border-border rounded-xl overflow-hidden mb-3">
                      <div className="flex items-center gap-3 px-4 py-3 border-b border-border/60">
                        <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${cat.color}`}>
                          <Icon size={15} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium">{cat.name}</span>
                            {catPct === 100 && catItems.length > 0 && (
                              <span className="text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full font-medium">Packed</span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1">
                            <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
                              <div className="h-full bg-accent rounded-full transition-all duration-500" style={{ width: `${catPct}%` }} />
                            </div>
                            <span className="text-xs text-muted-foreground shrink-0" style={{ fontFamily: "'DM Mono', monospace" }}>
                              {catPacked}/{catItems.length}
                            </span>
                          </div>
                        </div>
                      </div>
                      {catItems.length === 0 ? (
                        <p className="text-xs text-muted-foreground px-4 py-4 italic">No items in this category.</p>
                      ) : (
                        catItems.map((item) => {
                          const assignedBag = bags.find((b) => b.id === item.bagId);
                          return (
                            <div
                              key={item.id}
                              className="flex items-center gap-3 px-4 py-4 border-b border-border/30 last:border-b-0 hover:bg-muted/10 transition-colors cursor-pointer"
                              onClick={() => toggleItem(item.id)}
                            >
                              <button className="shrink-0 text-muted-foreground">
                                {item.packed ? <CheckSquare size={18} className="text-accent" /> : <Square size={18} />}
                              </button>
                              <span className={`flex-1 text-sm ${item.packed ? "line-through text-muted-foreground" : ""}`}>{item.name}</span>
                              {assignedBag && (
                                <span className="flex items-center gap-1 text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded-full shrink-0">
                                  <BagIcon icon={assignedBag.icon} size={11} />
                                  <span className="hidden sm:inline">{assignedBag.name}</span>
                                </span>
                              )}
                            </div>
                          );
                        })
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── All items ── */}
            {view === "list" && (
              <div className="bg-card border border-border rounded-xl overflow-hidden">
                {(["unpacked", "packed"] as const).map((group) => {
                  const groupItems = filtered(items).filter((i) => group === "packed" ? i.packed : !i.packed);
                  if (groupItems.length === 0) return null;
                  return (
                    <div key={group}>
                      <div className="px-4 py-2.5 bg-muted/40 border-b border-border">
                        <span className="text-xs tracking-widest uppercase font-medium text-muted-foreground">
                          {group === "unpacked" ? `To pack — ${groupItems.length}` : `Packed — ${groupItems.length}`}
                        </span>
                      </div>
                      {groupItems.map((item) => {
                        const assignedBag = bags.find((b) => b.id === item.bagId);
                        return (
                          <div
                            key={item.id}
                            className="flex items-center gap-3 px-4 py-4 border-b border-border/40 last:border-b-0 hover:bg-muted/20 transition-colors cursor-pointer"
                            onClick={() => toggleItem(item.id)}
                          >
                            <button className="shrink-0 text-muted-foreground">
                              {item.packed ? <CheckSquare size={18} className="text-accent" /> : <Square size={18} />}
                            </button>
                            <span className={`flex-1 text-sm ${item.packed ? "line-through text-muted-foreground" : ""}`}>{item.name}</span>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <span className="text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded-full hidden sm:inline">
                                {item.category}
                              </span>
                              {assignedBag && (
                                <span className="flex items-center gap-1 text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded-full">
                                  <BagIcon icon={assignedBag.icon} size={11} />
                                  <span className="hidden sm:inline">{assignedBag.name}</span>
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Bottom padding so FAB doesn't cover last item */}
            <div className="h-20 md:hidden" />
          </div>
        </main>
      </div>

      {/* ── Mobile FAB ── */}
      <button
        onClick={() => setShowAdd(true)}
        className="md:hidden fixed bottom-6 right-5 z-30 w-14 h-14 bg-accent text-accent-foreground rounded-full shadow-lg flex items-center justify-center hover:bg-accent/90 transition-colors active:scale-95"
      >
        <Plus size={22} />
      </button>

      {/* ── Overlays ── */}
      {showAdd    && <AddItemSheet bags={bags} onAdd={addItem} onClose={() => setShowAdd(false)} />}
      {showDrawer && <TripsDrawer trips={TRIPS} packed={packed} total={total} onClose={() => setShowDrawer(false)} />}
    </div>
  );
}
