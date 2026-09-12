import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PRODUCT_CATEGORIES = [
  "supplements", "vitamins", "minerals", "adaptogens", "amino_acids",
  "probiotics", "nootropics", "sleep_aids", "energy", "recovery",
  "devices", "lab_tests", "apparel",
];

const HEALTH_GOALS = [
  "energy", "sleep", "focus", "longevity", "athletic_performance",
  "weight_management", "stress_management", "immune_support", "gut_health",
];

const authHeaders = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } });

const emptyProduct = {
  name: "", slug: "", vendor_id: "", category: "supplements", price: "",
  sale_price: "", short_description: "", description: "", image_url: "",
  affiliate_url: "", health_goals: [], benefits: "", sku: "",
  is_featured: false, is_ai_recommended: false,
};

const AdminPanel = () => {
  const navigate = useNavigate();
  const [tab, setTab] = useState("overview");
  const [vendors, setVendors] = useState([]);
  const [products, setProducts] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

  const user = (() => { try { return JSON.parse(localStorage.getItem("user") || "{}"); } catch { return {}; } })();
  const isAdmin = user?.role === "admin";

  useEffect(() => {
    if (!isAdmin) { setLoading(false); return; }
    loadAll();
  }, []); // load once

  const loadAll = async () => {
    setLoading(true);
    try {
      const [v, p, a, o] = await Promise.all([
        axios.get(`${API}/vendors`),
        axios.get(`${API}/products?limit=500`),
        axios.get(`${API}/admin/affiliate/analytics`, authHeaders()),
        axios.get(`${API}/admin/practitioner-orders`, authHeaders()),
      ]);
      setVendors(v.data);
      setProducts(p.data);
      setAnalytics(a.data);
      setOrders(o.data);
    } catch (e) {
      console.error("Admin load error", e);
    } finally {
      setLoading(false);
    }
  };

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(""), 3000); };

  if (!isAdmin) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow p-8 text-center max-w-md">
          <div className="text-5xl mb-4">🔒</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Admin access required</h1>
          <p className="text-gray-600 mb-6">Please sign in with your admin account to manage products, vendors, and affiliate analytics.</p>
          <Link to="/signin" className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-semibold">Sign In</Link>
        </div>
      </div>
    );
  }

  const TABS = [
    { id: "overview", label: "Analytics" },
    { id: "products", label: "Products" },
    { id: "vendors", label: "Vendors & Affiliate" },
    { id: "orders", label: "Practitioner Orders" },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">H</span>
            </div>
            <div>
              <div className="font-bold text-gray-900">Hackster Admin</div>
              <div className="text-xs text-gray-500">Product & affiliate management</div>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button onClick={loadAll} className="text-sm text-gray-500 hover:text-blue-600">↻ Refresh</button>
            <button onClick={() => navigate("/")} className="text-sm text-gray-500 hover:text-blue-600">Back to site</button>
          </div>
        </div>
      </div>

      {msg && (
        <div className="max-w-7xl mx-auto px-6 pt-4">
          <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-2 rounded-lg text-sm">{msg}</div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-6 py-6">
        {/* Tabs */}
        <div className="flex space-x-2 mb-6 border-b border-gray-200">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors ${tab === t.id ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500 hover:text-gray-700"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-20 text-gray-400">Loading…</div>
        ) : (
          <>
            {tab === "overview" && <AnalyticsTab analytics={analytics} />}
            {tab === "products" && <ProductsTab products={products} vendors={vendors} reload={loadAll} flash={flash} />}
            {tab === "vendors" && <VendorsTab vendors={vendors} reload={loadAll} flash={flash} />}
            {tab === "orders" && <OrdersTab orders={orders} reload={loadAll} flash={flash} />}
          </>
        )}
      </div>
    </div>
  );
};

/* ---------------- Analytics ---------------- */
const StatCard = ({ label, value, accent }) => (
  <div className="bg-white rounded-xl border border-gray-200 p-5">
    <div className="text-sm text-gray-500">{label}</div>
    <div className={`text-3xl font-bold mt-1 ${accent || "text-gray-900"}`}>{value}</div>
  </div>
);

const AnalyticsTab = ({ analytics }) => {
  if (!analytics) return <div className="text-gray-400">No data yet.</div>;
  return (
    <div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Clicks" value={analytics.total_clicks} accent="text-blue-600" />
        <StatCard label="Conversions" value={analytics.total_conversions} accent="text-green-600" />
        <StatCard label="Conversion Rate" value={`${analytics.conversion_rate}%`} />
        <StatCard label="Est. Commission" value={`$${analytics.est_commission?.toFixed(2)}`} accent="text-purple-600" />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-bold text-gray-900 mb-3">Clicks by Vendor</h3>
          {analytics.by_vendor?.length ? (
            <table className="w-full text-sm">
              <thead><tr className="text-left text-gray-500"><th className="pb-2">Vendor</th><th className="pb-2">Clicks</th><th className="pb-2">Conv.</th><th className="pb-2">Est. $</th></tr></thead>
              <tbody>
                {analytics.by_vendor.map((v) => (
                  <tr key={v.vendor} className="border-t border-gray-100">
                    <td className="py-2 font-medium text-gray-800">{v.vendor}</td>
                    <td className="py-2">{v.clicks}</td>
                    <td className="py-2">{v.conversions}</td>
                    <td className="py-2">${v.est_commission?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <p className="text-gray-400 text-sm">No clicks yet.</p>}
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-bold text-gray-900 mb-3">Top Products</h3>
          {analytics.top_products?.length ? (
            <ul className="text-sm space-y-2">
              {analytics.top_products.map((p) => (
                <li key={p.product} className="flex justify-between border-t border-gray-100 pt-2">
                  <span className="text-gray-800">{p.product} <span className="text-gray-400">· {p.vendor}</span></span>
                  <span className="font-semibold">{p.clicks}</span>
                </li>
              ))}
            </ul>
          ) : <p className="text-gray-400 text-sm">No clicks yet.</p>}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mt-6">
        <h3 className="font-bold text-gray-900 mb-3">Recent Clicks</h3>
        {analytics.recent_clicks?.length ? (
          <table className="w-full text-sm">
            <thead><tr className="text-left text-gray-500"><th className="pb-2">Product</th><th className="pb-2">Vendor</th><th className="pb-2">Source</th><th className="pb-2">Est. $</th><th className="pb-2">Converted</th></tr></thead>
            <tbody>
              {analytics.recent_clicks.map((c, i) => (
                <tr key={i} className="border-t border-gray-100">
                  <td className="py-2 text-gray-800">{c.product_name}</td>
                  <td className="py-2">{c.vendor_name}</td>
                  <td className="py-2"><span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{c.source}</span></td>
                  <td className="py-2">${(c.est_commission || 0).toFixed(2)}</td>
                  <td className="py-2">{c.converted ? "✅" : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="text-gray-400 text-sm">No clicks yet.</p>}
      </div>
    </div>
  );
};

/* ---------------- Products ---------------- */
const ProductsTab = ({ products, vendors, reload, flash }) => {
  const [editing, setEditing] = useState(null); // product object or null
  const [showForm, setShowForm] = useState(false);

  const startNew = () => { setEditing({ ...emptyProduct }); setShowForm(true); };
  const startEdit = (p) => {
    setEditing({
      ...p,
      benefits: Array.isArray(p.benefits) ? p.benefits.join(", ") : (p.benefits || ""),
      health_goals: p.health_goals || [],
      price: p.price ?? "",
      sale_price: p.sale_price ?? "",
    });
    setShowForm(true);
  };

  const save = async () => {
    const vendor = vendors.find((v) => v.id === editing.vendor_id);
    const payload = {
      ...editing,
      vendor_name: vendor?.name || editing.vendor_name || "",
      price: parseFloat(editing.price) || 0,
      sale_price: editing.sale_price === "" ? null : parseFloat(editing.sale_price),
      benefits: typeof editing.benefits === "string" ? editing.benefits.split(",").map((s) => s.trim()).filter(Boolean) : editing.benefits,
      slug: editing.slug || editing.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, ""),
    };
    try {
      if (editing.id) {
        await axios.put(`${API}/admin/products/${editing.id}`, payload, authHeaders());
        flash("Product updated");
      } else {
        await axios.post(`${API}/admin/products`, payload, authHeaders());
        flash("Product created");
      }
      setShowForm(false); setEditing(null); reload();
    } catch (e) {
      console.error(e);
      alert("Error saving product: " + (e.response?.data?.detail || e.message));
    }
  };

  const remove = async (p) => {
    if (!window.confirm(`Delete "${p.name}"?`)) return;
    try { await axios.delete(`${API}/admin/products/${p.id}`, authHeaders()); flash("Product deleted"); reload(); }
    catch (e) { alert("Error deleting: " + (e.response?.data?.detail || e.message)); }
  };

  const toggleGoal = (g) => {
    const has = editing.health_goals?.includes(g);
    setEditing({ ...editing, health_goals: has ? editing.health_goals.filter((x) => x !== g) : [...(editing.health_goals || []), g] });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">{products.length} Products</h2>
        <button onClick={startNew} className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold text-sm hover:bg-blue-700">+ Add Product</button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500">
            <tr><th className="p-3">Product</th><th className="p-3">Vendor</th><th className="p-3">Price</th><th className="p-3">Affiliate Link</th><th className="p-3"></th></tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id} className="border-t border-gray-100">
                <td className="p-3">
                  <div className="font-medium text-gray-900">{p.name}</div>
                  <div className="text-xs text-gray-400">{p.category}</div>
                </td>
                <td className="p-3 text-gray-700">{p.vendor_name}</td>
                <td className="p-3">${p.price?.toFixed(2)}</td>
                <td className="p-3 max-w-[220px] truncate text-blue-600 text-xs">{p.affiliate_url || <span className="text-gray-300">— none —</span>}</td>
                <td className="p-3 whitespace-nowrap">
                  <button onClick={() => startEdit(p)} className="text-blue-600 hover:underline mr-3">Edit</button>
                  <button onClick={() => remove(p)} className="text-red-500 hover:underline">Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showForm && editing && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b flex items-center justify-between shrink-0">
              <h3 className="font-bold text-gray-900">{editing.id ? "Edit Product" : "New Product"}</h3>
              <button onClick={() => { setShowForm(false); setEditing(null); }} className="text-2xl text-gray-400">×</button>
            </div>
            <div className="p-6 space-y-4 overflow-y-auto">
              <Field label="Name"><input className="inp" value={editing.name} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></Field>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Vendor">
                  <select className="inp" value={editing.vendor_id} onChange={(e) => setEditing({ ...editing, vendor_id: e.target.value })}>
                    <option value="">Select vendor…</option>
                    {vendors.map((v) => <option key={v.id} value={v.id}>{v.name}</option>)}
                  </select>
                </Field>
                <Field label="Category">
                  <select className="inp" value={editing.category} onChange={(e) => setEditing({ ...editing, category: e.target.value })}>
                    {PRODUCT_CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Price ($)"><input type="number" className="inp" value={editing.price} onChange={(e) => setEditing({ ...editing, price: e.target.value })} /></Field>
                <Field label="Sale Price ($, optional)"><input type="number" className="inp" value={editing.sale_price} onChange={(e) => setEditing({ ...editing, sale_price: e.target.value })} /></Field>
              </div>
              <Field label="Affiliate URL (leave blank to auto-generate from vendor pattern)">
                <input className="inp" placeholder="https://vendor.com/product?aff=hackster" value={editing.affiliate_url || ""} onChange={(e) => setEditing({ ...editing, affiliate_url: e.target.value })} />
              </Field>
              <Field label="Image URL"><input className="inp" value={editing.image_url || ""} onChange={(e) => setEditing({ ...editing, image_url: e.target.value })} /></Field>
              <Field label="Short description"><input className="inp" value={editing.short_description || ""} onChange={(e) => setEditing({ ...editing, short_description: e.target.value })} /></Field>
              <Field label="Description"><textarea rows={3} className="inp" value={editing.description || ""} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></Field>
              <Field label="Benefits (comma separated)"><input className="inp" value={editing.benefits} onChange={(e) => setEditing({ ...editing, benefits: e.target.value })} /></Field>
              <Field label="Health goals">
                <div className="flex flex-wrap gap-2">
                  {HEALTH_GOALS.map((g) => (
                    <button key={g} type="button" onClick={() => toggleGoal(g)}
                      className={`px-3 py-1 rounded-full text-xs border ${editing.health_goals?.includes(g) ? "bg-blue-600 text-white border-blue-600" : "bg-white text-gray-600 border-gray-300"}`}>
                      {g.replace(/_/g, " ")}
                    </button>
                  ))}
                </div>
              </Field>
              <div className="flex gap-6">
                <label className="flex items-center space-x-2 text-sm"><input type="checkbox" checked={!!editing.is_featured} onChange={(e) => setEditing({ ...editing, is_featured: e.target.checked })} /><span>Featured</span></label>
                <label className="flex items-center space-x-2 text-sm"><input type="checkbox" checked={!!editing.is_ai_recommended} onChange={(e) => setEditing({ ...editing, is_ai_recommended: e.target.checked })} /><span>AI Recommended</span></label>
              </div>
            </div>
            <div className="px-6 py-4 border-t flex justify-end space-x-3 shrink-0">
              <button onClick={() => { setShowForm(false); setEditing(null); }} className="px-4 py-2 text-gray-500">Cancel</button>
              <button onClick={save} disabled={!editing.name || !editing.vendor_id} className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold disabled:opacity-40">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/* ---------------- Vendors ---------------- */
const VendorsTab = ({ vendors, reload, flash }) => {
  const [editing, setEditing] = useState(null);

  const save = async () => {
    const payload = {
      name: editing.name, slug: editing.slug, description: editing.description || "",
      website: editing.website || "", logo_url: editing.logo_url || "",
      affiliate_url_pattern: editing.affiliate_url_pattern || null,
      commission_rate: parseFloat(editing.commission_rate) || 0,
      fulfillment_type: editing.fulfillment_type || "affiliate",
      network: editing.network || null,
      tracking_param: editing.tracking_param || "aff",
      tracking_value: editing.tracking_value || "hackster",
      subid_param: editing.subid_param || "subId",
      add_to_cart_pattern: editing.add_to_cart_pattern || null,
      status: editing.status || "active",
    };
    try {
      if (editing.id) { await axios.put(`${API}/admin/vendors/${editing.id}`, payload, authHeaders()); flash("Vendor updated"); }
      else { await axios.post(`${API}/admin/vendors`, payload, authHeaders()); flash("Vendor created"); }
      setEditing(null); reload();
    } catch (e) { alert("Error saving vendor: " + (e.response?.data?.detail || e.message)); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-900">{vendors.length} Vendors</h2>
        <button onClick={() => setEditing({ fulfillment_type: "affiliate", tracking_param: "aff", tracking_value: "hackster", subid_param: "subId", commission_rate: 0.1, status: "active" })}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold text-sm hover:bg-blue-700">+ Add Vendor</button>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {vendors.map((v) => (
          <div key={v.id} className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-center justify-between">
              <div className="font-bold text-gray-900">{v.name}</div>
              <span className={`text-xs px-2 py-0.5 rounded-full ${v.fulfillment_type === "practitioner_order" ? "bg-purple-100 text-purple-700" : "bg-blue-100 text-blue-700"}`}>
                {v.fulfillment_type === "practitioner_order" ? "Practitioner order" : "Affiliate"}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-1">Commission {Math.round((v.commission_rate || 0) * 100)}% · tracking: {v.tracking_param}={v.tracking_value}</div>
            <div className="text-xs text-gray-400 mt-1 truncate">{v.affiliate_url_pattern || "no affiliate pattern"}</div>
            <button onClick={() => setEditing({ ...v, commission_rate: v.commission_rate })} className="text-blue-600 text-sm mt-3 hover:underline">Configure</button>
          </div>
        ))}
      </div>

      {editing && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b flex items-center justify-between shrink-0">
              <h3 className="font-bold text-gray-900">{editing.id ? `Configure ${editing.name}` : "New Vendor"}</h3>
              <button onClick={() => setEditing(null)} className="text-2xl text-gray-400">×</button>
            </div>
            <div className="p-6 space-y-4 overflow-y-auto">
              <div className="grid grid-cols-2 gap-4">
                <Field label="Name"><input className="inp" value={editing.name || ""} onChange={(e) => setEditing({ ...editing, name: e.target.value })} /></Field>
                <Field label="Slug"><input className="inp" value={editing.slug || ""} onChange={(e) => setEditing({ ...editing, slug: e.target.value })} /></Field>
              </div>
              <Field label="Website"><input className="inp" value={editing.website || ""} onChange={(e) => setEditing({ ...editing, website: e.target.value })} /></Field>
              <Field label="Fulfillment type">
                <select className="inp" value={editing.fulfillment_type} onChange={(e) => setEditing({ ...editing, fulfillment_type: e.target.value })}>
                  <option value="affiliate">Affiliate (public tracked link)</option>
                  <option value="practitioner_order">Practitioner order (Hackster fulfills)</option>
                </select>
              </Field>
              <Field label="Affiliate URL pattern (use {product_slug})">
                <input className="inp" placeholder="https://vendor.com/products/{product_slug}?aff=hackster" value={editing.affiliate_url_pattern || ""} onChange={(e) => setEditing({ ...editing, affiliate_url_pattern: e.target.value })} />
              </Field>
              <Field label="Multi-item add-to-cart pattern (optional, use {items})">
                <input className="inp" placeholder="https://vendor.com/cart/add?items={items}" value={editing.add_to_cart_pattern || ""} onChange={(e) => setEditing({ ...editing, add_to_cart_pattern: e.target.value })} />
              </Field>
              <div className="grid grid-cols-3 gap-4">
                <Field label="Tracking param"><input className="inp" value={editing.tracking_param || ""} onChange={(e) => setEditing({ ...editing, tracking_param: e.target.value })} /></Field>
                <Field label="Tracking value"><input className="inp" value={editing.tracking_value || ""} onChange={(e) => setEditing({ ...editing, tracking_value: e.target.value })} /></Field>
                <Field label="SubID param"><input className="inp" value={editing.subid_param || ""} onChange={(e) => setEditing({ ...editing, subid_param: e.target.value })} /></Field>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <Field label="Network (optional)"><input className="inp" placeholder="impact / shareasale / direct" value={editing.network || ""} onChange={(e) => setEditing({ ...editing, network: e.target.value })} /></Field>
                <Field label="Commission rate (0–1)"><input type="number" step="0.01" className="inp" value={editing.commission_rate ?? ""} onChange={(e) => setEditing({ ...editing, commission_rate: e.target.value })} /></Field>
              </div>
              <p className="text-xs text-gray-400">Network-agnostic: set the tracking param/value your affiliate network expects. SubID is auto-filled per click for attribution.</p>
            </div>
            <div className="px-6 py-4 border-t flex justify-end space-x-3 shrink-0">
              <button onClick={() => setEditing(null)} className="px-4 py-2 text-gray-500">Cancel</button>
              <button onClick={save} disabled={!editing.name || !editing.slug} className="bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold disabled:opacity-40">Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

/* ---------------- Practitioner Orders ---------------- */
const OrdersTab = ({ orders, reload, flash }) => {
  const updateStatus = async (order, status) => {
    try { await axios.put(`${API}/admin/practitioner-orders/${order.id}`, { status }, authHeaders()); flash("Order updated"); reload(); }
    catch (e) { alert("Error: " + (e.response?.data?.detail || e.message)); }
  };
  const statusColors = { new: "bg-yellow-100 text-yellow-800", contacted: "bg-blue-100 text-blue-800", fulfilled: "bg-green-100 text-green-800", cancelled: "bg-gray-100 text-gray-500" };

  if (!orders.length) return <div className="text-gray-400 py-10 text-center">No practitioner order requests yet.</div>;

  return (
    <div className="space-y-4">
      {orders.map((o) => (
        <div key={o.id} className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="font-bold text-gray-900">{o.customer_name} <span className="text-sm text-gray-400 font-normal">· {o.customer_email}</span></div>
              {o.customer_phone && <div className="text-sm text-gray-500">{o.customer_phone}</div>}
              <div className="text-xs text-gray-400 mt-1">Vendors: {o.vendors?.join(", ")}</div>
            </div>
            <div className="text-right">
              <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[o.status]}`}>{o.status}</span>
              <div className="text-lg font-bold text-gray-900 mt-1">${o.estimated_total?.toFixed(2)}</div>
            </div>
          </div>
          <ul className="text-sm text-gray-600 mt-3 space-y-1">
            {o.items?.map((it, i) => (
              <li key={i} className="flex justify-between"><span>{it.quantity}× {it.product_name} <span className="text-gray-400">({it.vendor_name})</span></span><span>${it.price?.toFixed(2)}</span></li>
            ))}
          </ul>
          {o.notes && <p className="text-sm text-gray-500 mt-2 italic">{`"${o.notes}"`}</p>}
          <div className="mt-3 flex gap-2">
            {["new", "contacted", "fulfilled", "cancelled"].map((s) => (
              <button key={s} onClick={() => updateStatus(o, s)} disabled={o.status === s}
                className={`text-xs px-3 py-1 rounded-full border ${o.status === s ? "bg-gray-100 text-gray-400 border-gray-200" : "border-gray-300 text-gray-600 hover:border-blue-400 hover:text-blue-600"}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const Field = ({ label, children }) => (
  <div>
    <label className="block text-sm font-medium text-gray-600 mb-1">{label}</label>
    {children}
  </div>
);

export default AdminPanel;
