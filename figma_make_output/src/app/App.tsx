import { useState } from "react";
import {
  CheckSquare, Square, Plus, ChevronRight, MapPin, Calendar,
  Search, X, Luggage, Backpack, ShoppingBag, Trash2,
  ChevronDown, ChevronUp, Shirt, Zap, BookOpen, Package,
  Menu, Bell,
} from "lucide-react";

// ─── Theme tokens ─────────────────────────────────────────────────────────────
const C = {
  bg:           "#fefcf5",
  card:         "#fffef9",
  sidebar:      "#fdf6e3",
  sidebarAccent:"#f5e9c4",
  sidebarText:  "#1a1a2e",
  sidebarMuted: "#8a825e",
  sidebarBorder:"rgba(26,26,46,0.08)",
  ink:          "#1a1a2e",
  muted:        "#8a825e",
  accent:       "#d4920a",
  accentFg:     "#ffffff",
  border:       "rgba(26,26,46,0.1)",
  inputBg:      "#f0e8d5",
  progressBg:   "#f0e4b8",
  ok:           "#2e7d4f",
  okBg:         "#dcfce7",
  warn:         "#b07d18",
  pill:         "#fef3c7",
  pillInk:      "#92400e",
};

const heading = "'Fraunces', Georgia, serif";
const body    = "'Inter', sans-serif";
const mono    = "'DM Mono', monospace";

// ─── Types ────────────────────────────────────────────────────────────────────
type Bag  = { id: number; name: string; icon: "luggage"|"backpack"|"tote" };
type Item = { id: number; name: string; packed: boolean; category: string; bagId: number|null };
type Trip = { id: number; name: string; destination: string; date: string };

const CATEGORIES = [
  { name: "Clothing",    icon: Shirt,    bg: "#fef3c7", fg: "#92400e" },
  { name: "Electronics", icon: Zap,      bg: "#fde8d0", fg: "#7c3a1a" },
  { name: "Documents",   icon: BookOpen, bg: "#dcfce7", fg: "#166534" },
  { name: "Gear",        icon: Package,  bg: "#fce7f3", fg: "#831843" },
];

const BAG_COLORS = [
  { bg: "#fef3c7", fg: "#92400e" },
  { bg: "#fde8d0", fg: "#7c3a1a" },
  { bg: "#dcfce7", fg: "#166534" },
  { bg: "#fce7f3", fg: "#831843" },
];

const TRIPS: Trip[] = [
  { id: 1, name: "Lisbon & Porto",    destination: "Portugal", date: "Jul 12 – Jul 26" },
  { id: 2, name: "Dolomites Weekend", destination: "Italy",    date: "Aug 3 – Aug 6" },
  { id: 3, name: "Tokyo Photo Trip",  destination: "Japan",    date: "Sep 18 – Oct 2" },
];

const INIT_BAGS: Bag[] = [
  { id: 1, name: "Large suitcase", icon: "luggage" },
  { id: 2, name: "Carry-on",       icon: "luggage" },
  { id: 3, name: "Day pack",       icon: "backpack" },
  { id: 4, name: "Personal tote",  icon: "tote" },
];

const INIT_ITEMS: Item[] = [
  { id: 1,  name: "Merino wool t-shirts (3)",    packed: true,  category: "Clothing",     bagId: 1 },
  { id: 2,  name: "Linen trousers",              packed: true,  category: "Clothing",     bagId: 1 },
  { id: 3,  name: "Light rain jacket",           packed: false, category: "Clothing",     bagId: 1 },
  { id: 4,  name: "Walking sandals",             packed: false, category: "Clothing",     bagId: 1 },
  { id: 5,  name: "Passport & copies",           packed: true,  category: "Documents",    bagId: 2 },
  { id: 6,  name: "Travel insurance docs",       packed: true,  category: "Documents",    bagId: 2 },
  { id: 7,  name: "International plug adapter",  packed: false, category: "Electronics",  bagId: 2 },
  { id: 8,  name: "USB-C charging cables",       packed: true,  category: "Electronics",  bagId: 2 },
  { id: 9,  name: "Noise-cancelling headphones", packed: false, category: "Electronics",  bagId: 3 },
  { id: 10, name: "Portable battery pack",       packed: true,  category: "Electronics",  bagId: 3 },
  { id: 11, name: "Microfiber towel",            packed: true,  category: "Gear",         bagId: 3 },
  { id: 12, name: "Sunscreen SPF 50",            packed: false, category: "Gear",         bagId: 3 },
  { id: 13, name: "Sunglasses",                  packed: false, category: "Gear",         bagId: 4 },
  { id: 14, name: "Water bottle",               packed: true,  category: "Gear",         bagId: null },
  { id: 15, name: "Phrase book",                packed: false, category: "Documents",    bagId: null },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function BagIcon({ icon, size = 15 }: { icon: Bag["icon"]; size?: number }) {
  if (icon === "backpack") return <Backpack size={size} />;
  if (icon === "tote")     return <ShoppingBag size={size} />;
  return <Luggage size={size} />;
}

// ─── Bag card ────────────────────────────────────────────────────────────────
function BagCard({ bag, items, color, onToggleAll, onDelete }: {
  bag: Bag; items: Item[];
  color: { bg: string; fg: string };
  onToggleAll: (p: boolean) => void;
  onDelete: () => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  const packed = items.filter(i => i.packed).length;
  const pct    = items.length > 0 ? Math.round((packed / items.length) * 100) : 0;

  return (
    <div style={{
      background: C.card, border: `1px solid ${C.border}`,
      borderRadius: 14, overflow: "hidden", marginBottom: 12,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", borderBottom: collapsed ? "none" : `1px solid ${C.border}` }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: color.bg, color: color.fg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <BagIcon icon={bag.icon} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: C.ink, fontFamily: heading }}>{bag.name}</span>
            {pct === 100 && items.length > 0 && (
              <span style={{ fontSize: 11, background: C.okBg, color: C.ok, padding: "1px 8px", borderRadius: 99, fontWeight: 600 }}>Packed ✓</span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
            <div style={{ flex: 1, height: 4, background: C.progressBg, borderRadius: 99, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${pct}%`, background: C.accent, borderRadius: 99, transition: "width 0.4s" }} />
            </div>
            <span style={{ fontSize: 11, color: C.muted, fontFamily: mono, flexShrink: 0 }}>{packed}/{items.length}</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 2, flexShrink: 0 }}>
          {items.length > 0 && (
            <button onClick={() => onToggleAll(packed < items.length)}
              style={{ fontSize: 11, color: C.muted, padding: "4px 8px", borderRadius: 6, border: "none", background: "transparent", cursor: "pointer" }}>
              {packed < items.length ? "Pack all" : "Unpack all"}
            </button>
          )}
          <button onClick={onDelete} style={{ padding: 6, borderRadius: 6, border: "none", background: "transparent", cursor: "pointer", color: C.muted }}>
            <Trash2 size={13} />
          </button>
          <button onClick={() => setCollapsed(v => !v)} style={{ padding: 6, borderRadius: 6, border: "none", background: "transparent", cursor: "pointer", color: C.muted }}>
            {collapsed ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
          </button>
        </div>
      </div>
      {!collapsed && (
        <div>
          {items.length === 0
            ? <p style={{ fontSize: 13, color: C.muted, padding: "14px 16px", margin: 0, fontStyle: "italic" }}>No items yet.</p>
            : items.map((item, i) => (
              <div key={item.id} style={{
                display: "flex", alignItems: "center", gap: 10, padding: "11px 16px",
                borderBottom: i < items.length - 1 ? `1px solid ${C.border}` : "none",
                background: "transparent",
              }}>
                <span style={{ fontSize: 13, color: item.packed ? C.muted : C.ink, textDecoration: item.packed ? "line-through" : "none", flex: 1 }}>
                  {item.name}
                </span>
                <span style={{ fontSize: 11, color: C.muted }}>{item.category}</span>
              </div>
            ))
          }
        </div>
      )}
    </div>
  );
}

// ─── Main ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [items, setItems]   = useState<Item[]>(INIT_ITEMS);
  const [bags, setBags]     = useState<Bag[]>(INIT_BAGS);
  const [view, setView]     = useState<"bags"|"category"|"list">("bags");
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd]     = useState(false);
  const [showDrawer, setShowDrawer] = useState(false);
  const [newName, setNewName]       = useState("");
  const [newBag, setNewBag]         = useState<number|null>(1);
  const [newCat, setNewCat]         = useState("Clothing");

  const toggle       = (id: number) => setItems(p => p.map(i => i.id === id ? { ...i, packed: !i.packed } : i));
  const toggleAllBag = (bagId: number, packed: boolean) => setItems(p => p.map(i => i.bagId === bagId ? { ...i, packed } : i));
  const deleteBag    = (bagId: number) => { setBags(p => p.filter(b => b.id !== bagId)); setItems(p => p.map(i => i.bagId === bagId ? { ...i, bagId: null } : i)); };
  const addItem      = () => {
    if (!newName.trim()) return;
    setItems(p => [...p, { id: Date.now(), name: newName.trim(), packed: false, category: newCat, bagId: newBag }]);
    setNewName(""); setShowAdd(false);
  };

  const packed   = items.filter(i => i.packed).length;
  const total    = items.length;
  const progress = total > 0 ? Math.round((packed / total) * 100) : 0;
  const unbagged = items.filter(i => i.bagId === null);

  const q = search.toLowerCase();
  const filtered = (list: Item[]) => q ? list.filter(i => i.name.toLowerCase().includes(q)) : list;

  return (
    <div style={{ minHeight: "100vh", background: C.bg, display: "flex", fontFamily: body, color: C.ink }}>

      {/* ── Desktop sidebar ── */}
      <aside style={{
        width: 256, flexShrink: 0, background: C.sidebar, display: "flex",
        flexDirection: "column", borderRight: `1px solid ${C.sidebarBorder}`,
      }} className="hidden md:flex">
        {/* Wordmark */}
        <div style={{ padding: "24px 20px 20px", borderBottom: `1px solid ${C.sidebarBorder}` }}>
          <div style={{ fontFamily: heading, fontSize: 22, fontWeight: 600, color: C.sidebarText, letterSpacing: "0" }}>
            packwell<span style={{ color: C.accent }}>.</span>
          </div>
          <div style={{ fontSize: 10, color: C.sidebarMuted, letterSpacing: "0.1em", textTransform: "uppercase", marginTop: 3 }}>
            travel inventory
          </div>
        </div>

        {/* Trips */}
        <div style={{ flex: 1, padding: "16px 12px", overflowY: "auto" }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: C.sidebarMuted, letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 8, padding: "0 8px" }}>
            Trips
          </div>
          {TRIPS.map((trip, i) => {
            const tPacked = i === 0 ? packed : 0;
            const tTotal  = i === 0 ? total : [9, 18][i - 1] ?? 0;
            const tPct    = tTotal > 0 ? Math.round((tPacked / tTotal) * 100) : 0;
            const active  = i === 0;
            return (
              <div key={trip.id} style={{
                padding: "10px 12px", borderRadius: 10, marginBottom: 4,
                background: active ? C.sidebarAccent : "transparent",
                cursor: "pointer",
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: C.sidebarText, fontFamily: heading }}>{trip.name}</span>
                  {active && <ChevronRight size={14} color={C.accent} />}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 3 }}>
                  <MapPin size={10} color={C.sidebarMuted} />
                  <span style={{ fontSize: 11, color: C.sidebarMuted }}>{trip.destination}</span>
                </div>
                <div style={{ marginTop: 6 }}>
                  <div style={{ height: 3, background: "rgba(255,255,255,0.12)", borderRadius: 99, overflow: "hidden" }}>
                    <div style={{ height: "100%", width: `${tPct}%`, background: C.accent, borderRadius: 99 }} />
                  </div>
                  <span style={{ fontSize: 10, color: C.sidebarMuted, marginTop: 3, display: "block" }}>{tPacked}/{tTotal} packed</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer nav */}
        <div style={{ padding: "12px", borderTop: `1px solid ${C.sidebarBorder}` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 12px", borderRadius: 10, cursor: "pointer" }}>
            <div style={{ width: 30, height: 30, borderRadius: "50%", background: C.accent, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 13, fontWeight: 700 }}>L</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: C.sidebarText }}>Luna Sofia</div>
              <div style={{ fontSize: 11, color: C.sidebarMuted }}>3 active trips</div>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Mobile drawer ── */}
      {showDrawer && (
        <>
          <div onClick={() => setShowDrawer(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 40 }} />
          <div style={{ position: "fixed", top: 0, left: 0, bottom: 0, width: 272, background: C.sidebar, zIndex: 50, display: "flex", flexDirection: "column", padding: "20px 12px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20, padding: "0 8px" }}>
              <div style={{ fontFamily: heading, fontSize: 20, fontWeight: 800, color: C.sidebarText }}>packwell<span style={{ color: C.accent }}>.</span></div>
              <button onClick={() => setShowDrawer(false)} style={{ background: "none", border: "none", color: C.sidebarMuted, cursor: "pointer" }}><X size={18} /></button>
            </div>
            {TRIPS.map((trip, i) => (
              <div key={trip.id} style={{ padding: "10px 12px", borderRadius: 10, marginBottom: 4, background: i === 0 ? C.sidebarAccent : "transparent" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.sidebarText, fontFamily: heading }}>{trip.name}</div>
                <div style={{ fontSize: 11, color: C.sidebarMuted, marginTop: 2 }}>{trip.destination} · {trip.date}</div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* ── Main ── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Mobile top bar */}
        <header style={{ background: C.bg, borderBottom: `1px solid ${C.border}`, padding: "12px 16px", display: "flex", alignItems: "center", justifyContent: "space-between" }} className="md:hidden">
          <button onClick={() => setShowDrawer(true)} style={{ background: "none", border: "none", color: C.muted, cursor: "pointer" }}><Menu size={20} /></button>
          <span style={{ fontFamily: heading, fontSize: 18, fontWeight: 800, color: C.ink }}>packwell<span style={{ color: C.accent }}>.</span></span>
          <button onClick={() => setSearch(s => s === "__open__" ? "" : "__open__")} style={{ background: "none", border: "none", color: C.muted, cursor: "pointer" }}><Search size={18} /></button>
        </header>

        <main style={{ flex: 1, overflowY: "auto" }}>
          {/* Trip header */}
          <div style={{ padding: "28px 32px 24px", borderBottom: `1px solid ${C.border}` }} className="px-4 md:px-8 pt-6 md:pt-8">
            <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
              <div>
                <h1 style={{ fontFamily: heading, fontSize: 28, fontWeight: 600, color: C.ink, margin: 0, letterSpacing: "0" }}>
                  Lisbon & Porto
                </h1>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 6 }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 13, color: C.muted }}>
                    <MapPin size={13} color={C.muted} />Portugal
                  </span>
                  <span style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 13, color: C.muted }}>
                    <Calendar size={13} color={C.muted} />Jul 12 – Jul 26, 2026
                  </span>
                </div>
              </div>
              <button
                onClick={() => setShowAdd(true)}
                style={{ display: "flex", alignItems: "center", gap: 6, background: C.accent, color: C.accentFg, border: "none", borderRadius: 10, padding: "9px 18px", fontSize: 14, fontWeight: 700, fontFamily: heading, cursor: "pointer", flexShrink: 0 }}
              >
                <Plus size={15} />Add item
              </button>
            </div>

            {/* Progress */}
            <div style={{ marginTop: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: C.muted, letterSpacing: "0.08em", textTransform: "uppercase" }}>Overall progress</span>
                <span style={{ fontSize: 13, color: C.ink, fontFamily: mono }}>{packed}/{total} items</span>
              </div>
              <div style={{ height: 8, background: C.progressBg, borderRadius: 99, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${progress}%`, background: C.accent, borderRadius: 99, transition: "width 0.5s" }} />
              </div>
              <p style={{ fontSize: 12, color: C.muted, marginTop: 6 }}>{progress}% complete — {total - packed} items still to pack</p>
            </div>
          </div>

          <div style={{ padding: "20px 32px" }} className="px-4 md:px-8">

            {/* Bag summary chips */}
            <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4, marginBottom: 20, scrollbarWidth: "none" }}>
              {bags.map((bag, idx) => {
                const bi  = items.filter(i => i.bagId === bag.id);
                const bp  = bi.filter(i => i.packed).length;
                const col = BAG_COLORS[idx % BAG_COLORS.length];
                return (
                  <div key={bag.id} style={{
                    display: "flex", alignItems: "center", gap: 8, padding: "7px 12px",
                    background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, flexShrink: 0,
                  }}>
                    <div style={{ width: 22, height: 22, borderRadius: 6, background: col.bg, color: col.fg, display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <BagIcon icon={bag.icon} size={12} />
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 600, color: C.ink }}>{bag.name}</span>
                    <span style={{ fontSize: 11, color: C.muted, fontFamily: mono }}>{bp}/{bi.length}</span>
                    {bp === bi.length && bi.length > 0 && <span style={{ color: C.ok, fontSize: 12 }}>✓</span>}
                  </div>
                );
              })}
              {unbagged.length > 0 && (
                <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", border: `1px dashed ${C.border}`, borderRadius: 10, flexShrink: 0 }}>
                  <X size={12} color={C.muted} />
                  <span style={{ fontSize: 12, color: C.muted }}>{unbagged.length} unbagged</span>
                </div>
              )}
            </div>

            {/* View toggle + search */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
              <div style={{ display: "flex", background: C.inputBg, borderRadius: 10, padding: 3 }}>
                {(["bags", "category", "list"] as const).map(v => (
                  <button key={v} onClick={() => setView(v)} style={{
                    padding: "7px 14px", borderRadius: 8, border: "none", cursor: "pointer",
                    background: view === v ? C.card : "transparent",
                    color: view === v ? C.ink : C.muted,
                    fontFamily: heading, fontSize: 13, fontWeight: view === v ? 700 : 500,
                    boxShadow: view === v ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                    transition: "all 0.15s",
                  }}>
                    {v === "bags" ? "By bag" : v === "category" ? "By category" : "All items"}
                  </button>
                ))}
              </div>
              <div style={{ position: "relative" }} className="hidden md:block">
                <Search size={13} style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", color: C.muted }} />
                <input
                  value={search} onChange={e => setSearch(e.target.value)}
                  placeholder="Search items…"
                  style={{ paddingLeft: 30, paddingRight: 28, paddingTop: 8, paddingBottom: 8, border: `1px solid ${C.border}`, borderRadius: 8, background: C.card, fontSize: 13, color: C.ink, outline: "none", width: 200, fontFamily: body }}
                />
                {search && <button onClick={() => setSearch("")} style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: C.muted }}><X size={13} /></button>}
              </div>
            </div>

            {/* ── By bag ── */}
            {view === "bags" && (
              <div>
                {bags.map((bag, idx) => (
                  <BagCard
                    key={bag.id} bag={bag}
                    items={filtered(items.filter(i => i.bagId === bag.id))}
                    color={BAG_COLORS[idx % BAG_COLORS.length]}
                    onToggleAll={p => toggleAllBag(bag.id, p)}
                    onDelete={() => deleteBag(bag.id)}
                  />
                ))}
                {filtered(unbagged).length > 0 && (
                  <div style={{ background: C.card, border: `1px dashed ${C.border}`, borderRadius: 14, overflow: "hidden", marginBottom: 12 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", borderBottom: `1px solid ${C.border}` }}>
                      <div style={{ width: 36, height: 36, borderRadius: 10, background: C.inputBg, display: "flex", alignItems: "center", justifyContent: "center" }}><X size={14} color={C.muted} /></div>
                      <span style={{ fontSize: 14, fontWeight: 600, color: C.muted, fontFamily: heading }}>Unbagged</span>
                      <span style={{ marginLeft: "auto", fontSize: 11, color: C.muted, fontFamily: mono }}>{filtered(unbagged).filter(i => i.packed).length}/{filtered(unbagged).length}</span>
                    </div>
                    {filtered(unbagged).map((item, i) => (
                      <div key={item.id} onClick={() => toggle(item.id)} style={{
                        display: "flex", alignItems: "center", gap: 10, padding: "11px 16px",
                        borderBottom: i < filtered(unbagged).length - 1 ? `1px solid ${C.border}` : "none", cursor: "pointer",
                      }}>
                        {item.packed ? <CheckSquare size={16} color={C.accent} /> : <Square size={16} color={C.muted} />}
                        <span style={{ fontSize: 13, color: item.packed ? C.muted : C.ink, textDecoration: item.packed ? "line-through" : "none" }}>{item.name}</span>
                      </div>
                    ))}
                  </div>
                )}
                <button style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 6, padding: "12px", border: `1px dashed ${C.border}`, borderRadius: 14, background: "transparent", color: C.muted, fontSize: 13, fontFamily: heading, cursor: "pointer" }}>
                  <Plus size={14} />Add a bag
                </button>
              </div>
            )}

            {/* ── By category ── */}
            {view === "category" && (
              <div>
                {CATEGORIES.map(cat => {
                  const catItems  = filtered(items.filter(i => i.category === cat.name));
                  const catPacked = catItems.filter(i => i.packed).length;
                  const catPct    = catItems.length > 0 ? Math.round((catPacked / catItems.length) * 100) : 0;
                  const Icon      = cat.icon;
                  return (
                    <div key={cat.name} style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden", marginBottom: 12 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", borderBottom: `1px solid ${C.border}` }}>
                        <div style={{ width: 36, height: 36, borderRadius: 10, background: cat.bg, color: cat.fg, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                          <Icon size={15} />
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <span style={{ fontSize: 14, fontWeight: 600, color: C.ink, fontFamily: heading }}>{cat.name}</span>
                            {catPct === 100 && catItems.length > 0 && <span style={{ fontSize: 11, background: C.okBg, color: C.ok, padding: "1px 8px", borderRadius: 99, fontWeight: 600 }}>Packed ✓</span>}
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 4 }}>
                            <div style={{ flex: 1, height: 4, background: C.progressBg, borderRadius: 99, overflow: "hidden" }}>
                              <div style={{ height: "100%", width: `${catPct}%`, background: C.accent, borderRadius: 99 }} />
                            </div>
                            <span style={{ fontSize: 11, color: C.muted, fontFamily: mono }}>{catPacked}/{catItems.length}</span>
                          </div>
                        </div>
                      </div>
                      {catItems.map((item, i) => {
                        const bag = bags.find(b => b.id === item.bagId);
                        return (
                          <div key={item.id} onClick={() => toggle(item.id)} style={{
                            display: "flex", alignItems: "center", gap: 10, padding: "11px 16px",
                            borderBottom: i < catItems.length - 1 ? `1px solid ${C.border}` : "none", cursor: "pointer",
                          }}>
                            {item.packed ? <CheckSquare size={16} color={C.accent} /> : <Square size={16} color={C.muted} />}
                            <span style={{ flex: 1, fontSize: 13, color: item.packed ? C.muted : C.ink, textDecoration: item.packed ? "line-through" : "none" }}>{item.name}</span>
                            {bag && (
                              <span style={{ fontSize: 11, padding: "2px 8px", background: C.pill, color: C.pillInk, borderRadius: 99 }}>
                                {bag.name}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}

            {/* ── All items ── */}
            {view === "list" && (
              <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: 14, overflow: "hidden" }}>
                {(["unpacked", "packed"] as const).map(group => {
                  const groupItems = filtered(items).filter(i => group === "packed" ? i.packed : !i.packed);
                  if (groupItems.length === 0) return null;
                  return (
                    <div key={group}>
                      <div style={{ padding: "8px 16px", background: C.inputBg, borderBottom: `1px solid ${C.border}` }}>
                        <span style={{ fontSize: 10, fontWeight: 700, color: C.muted, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                          {group === "unpacked" ? `To pack — ${groupItems.length}` : `Packed — ${groupItems.length}`}
                        </span>
                      </div>
                      {groupItems.map((item, i) => {
                        const bag = bags.find(b => b.id === item.bagId);
                        return (
                          <div key={item.id} onClick={() => toggle(item.id)} style={{
                            display: "flex", alignItems: "center", gap: 10, padding: "12px 16px",
                            borderBottom: i < groupItems.length - 1 ? `1px solid ${C.border}` : "none", cursor: "pointer",
                          }}>
                            {item.packed ? <CheckSquare size={16} color={C.accent} /> : <Square size={16} color={C.muted} />}
                            <span style={{ flex: 1, fontSize: 13, color: item.packed ? C.muted : C.ink, textDecoration: item.packed ? "line-through" : "none" }}>{item.name}</span>
                            <div style={{ display: "flex", gap: 6 }}>
                              <span style={{ fontSize: 11, padding: "2px 8px", background: C.inputBg, color: C.muted, borderRadius: 99 }}>{item.category}</span>
                              {bag && <span style={{ fontSize: 11, padding: "2px 8px", background: C.pill, color: C.pillInk, borderRadius: 99 }}>{bag.name}</span>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}

            <div style={{ height: 80 }} className="md:hidden" />
          </div>
        </main>
      </div>

      {/* ── Mobile FAB ── */}
      <button
        onClick={() => setShowAdd(true)}
        style={{ position: "fixed", bottom: 24, right: 20, width: 56, height: 56, borderRadius: "50%", background: C.accent, color: "#fff", border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 16px rgba(212,146,10,0.45)", zIndex: 30 }}
        className="md:hidden"
      >
        <Plus size={22} />
      </button>

      {/* ── Add item sheet ── */}
      {showAdd && (
        <>
          <div onClick={() => setShowAdd(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.3)", backdropFilter: "blur(2px)", zIndex: 40 }} />
          <div style={{ position: "fixed", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 50, padding: 20 }}>
            <div style={{ background: C.card, borderRadius: 20, width: "100%", maxWidth: 440, padding: 24, boxShadow: "0 20px 60px rgba(0,0,0,0.2)" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
                <h2 style={{ fontFamily: heading, fontSize: 18, fontWeight: 800, color: C.ink, margin: 0 }}>Add item</h2>
                <button onClick={() => setShowAdd(false)} style={{ background: "none", border: "none", cursor: "pointer", color: C.muted }}><X size={18} /></button>
              </div>
              <input
                autoFocus value={newName} onChange={e => setNewName(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter") addItem(); if (e.key === "Escape") setShowAdd(false); }}
                placeholder="Item name…"
                style={{ width: "100%", padding: "12px 14px", border: `1px solid ${C.border}`, borderRadius: 10, background: C.inputBg, fontSize: 14, color: C.ink, outline: "none", marginBottom: 14, boxSizing: "border-box", fontFamily: body }}
              />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: "uppercase", letterSpacing: "0.07em", display: "block", marginBottom: 6 }}>Category</label>
                  <select value={newCat} onChange={e => setNewCat(e.target.value)} style={{ width: "100%", padding: "9px 12px", border: `1px solid ${C.border}`, borderRadius: 8, background: C.inputBg, fontSize: 13, color: C.ink, outline: "none", fontFamily: body }}>
                    {CATEGORIES.map(c => <option key={c.name}>{c.name}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 700, color: C.muted, textTransform: "uppercase", letterSpacing: "0.07em", display: "block", marginBottom: 6 }}>Bag</label>
                  <select value={newBag ?? ""} onChange={e => setNewBag(e.target.value ? Number(e.target.value) : null)} style={{ width: "100%", padding: "9px 12px", border: `1px solid ${C.border}`, borderRadius: 8, background: C.inputBg, fontSize: 13, color: C.ink, outline: "none", fontFamily: body }}>
                    <option value="">No bag</option>
                    {bags.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                  </select>
                </div>
              </div>
              <button onClick={addItem} style={{ width: "100%", padding: "13px", background: C.accent, color: C.accentFg, border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700, fontFamily: heading, cursor: "pointer" }}>
                Add to list
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
