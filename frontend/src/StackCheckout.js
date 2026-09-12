import { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * StackCheckout — the "review your stack & buy in one click" flow.
 *
 * Props:
 *  - items: array of { product_id, product_name, vendor_name, price, image_url }
 *  - onClose: () => void
 *  - user: optional current user object (for practitioner order prefill)
 *  - source: string source tag for click attribution (default "stack")
 */
const StackCheckout = ({ items = [], onClose, user = null, source = "stack" }) => {
  // Track which items the user accepts (default: all accepted)
  const [accepted, setAccepted] = useState(() => {
    const map = {};
    items.forEach((it, idx) => { map[it.product_id || idx] = true; });
    return map;
  });
  const [step, setStep] = useState("review"); // review | plan | practitioner | done
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [openedVendors, setOpenedVendors] = useState({});
  const [practitionerForm, setPractitionerForm] = useState({
    customer_name: user?.username || "",
    customer_email: user?.email || "",
    customer_phone: "",
    notes: "",
  });
  const [practitionerSubmitted, setPractitionerSubmitted] = useState(false);

  useEffect(() => {
    const map = {};
    items.forEach((it, idx) => { map[it.product_id || idx] = true; });
    setAccepted(map);
  }, [items]);

  const toggle = (key) => setAccepted((prev) => ({ ...prev, [key]: !prev[key] }));

  const selectedItems = items.filter((it, idx) => accepted[it.product_id || idx]);
  const selectedTotal = selectedItems.reduce((s, it) => s + (it.price || 0), 0);

  const buildCheckout = async () => {
    if (selectedItems.length === 0) return;
    setLoading(true);
    try {
      const payload = {
        items: selectedItems.map((it) => ({ product_id: it.product_id, quantity: 1 })),
        source,
        user_id: user?.id || null,
      };
      const res = await axios.post(`${API}/stack/checkout`, payload);
      setPlan(res.data);
      setStep("plan");
    } catch (e) {
      console.error("Checkout error", e);
      alert("We couldn't build your checkout right now. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const openVendor = (group) => {
    const url = group.checkout_url || group.add_to_cart_url;
    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
      setOpenedVendors((prev) => ({ ...prev, [group.vendor_id]: true }));
    }
  };

  const affiliateGroups = plan?.vendor_groups?.filter((g) => !g.requires_practitioner_order) || [];
  const practitionerGroups = plan?.vendor_groups?.filter((g) => g.requires_practitioner_order) || [];

  const submitPractitionerOrder = async () => {
    setLoading(true);
    try {
      const practitionerItems = [];
      practitionerGroups.forEach((g) => g.items.forEach((it) => {
        practitionerItems.push({ product_id: it.product_id, quantity: it.quantity });
      }));
      await axios.post(`${API}/practitioner-orders`, {
        ...practitionerForm,
        items: practitionerItems,
        user_id: user?.id || null,
      });
      setPractitionerSubmitted(true);
    } catch (e) {
      console.error("Practitioner order error", e);
      alert("We couldn't submit your practitioner order request. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">Buy Your Stack</h2>
            <p className="text-blue-100 text-sm">One click — we group your items by vendor</p>
          </div>
          <button onClick={onClose} className="text-white/80 hover:text-white text-2xl leading-none">×</button>
        </div>

        <div className="p-6 overflow-y-auto">
          {/* STEP 1 — REVIEW / ACCEPT */}
          {step === "review" && (
            <div>
              <p className="text-gray-600 mb-4">Check the items you’d like to purchase. We’ll route each to the right vendor.</p>
              <div className="space-y-3">
                {items.map((it, idx) => {
                  const key = it.product_id || idx;
                  return (
                    <label key={key} className={`flex items-center space-x-3 p-3 rounded-xl border cursor-pointer transition-colors ${accepted[key] ? "border-blue-400 bg-blue-50" : "border-gray-200 bg-white"}`}>
                      <input type="checkbox" checked={!!accepted[key]} onChange={() => toggle(key)} className="w-5 h-5 accent-blue-600" />
                      {it.image_url && (
                        <div className="w-12 h-12 bg-gray-100 rounded-lg overflow-hidden flex items-center justify-center">
                          <img src={it.image_url} alt={it.product_name} className="w-full h-full object-contain" />
                        </div>
                      )}
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{it.product_name}</div>
                        <div className="text-sm text-gray-500">{it.vendor_name}</div>
                      </div>
                      <div className="font-bold text-gray-900">${(it.price || 0).toFixed(2)}</div>
                    </label>
                  );
                })}
              </div>
              <div className="mt-5 flex items-center justify-between">
                <div className="text-gray-700">
                  <span className="text-sm">{selectedItems.length} selected</span>
                  <span className="ml-3 text-lg font-bold">${selectedTotal.toFixed(2)}</span>
                </div>
                <button
                  onClick={buildCheckout}
                  disabled={selectedItems.length === 0 || loading}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-xl font-semibold hover:opacity-90 disabled:opacity-40"
                >
                  {loading ? "Preparing..." : "Continue to Checkout →"}
                </button>
              </div>
            </div>
          )}

          {/* STEP 2 — GROUPED VENDOR PLAN */}
          {step === "plan" && plan && (
            <div>
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4">
                <p className="text-sm text-blue-900">
                  Your stack spans <strong>{plan.vendor_count} vendor{plan.vendor_count !== 1 ? "s" : ""}</strong>.
                  Complete each vendor’s cart below — we’ve pre-tracked every link.
                </p>
              </div>

              {affiliateGroups.length > 0 && (
                <div className="space-y-4">
                  {affiliateGroups.map((g, i) => (
                    <div key={g.vendor_id} className="border border-gray-200 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs flex items-center justify-center font-bold">{i + 1}</span>
                          <span className="font-bold text-gray-900">{g.vendor_name}</span>
                          {openedVendors[g.vendor_id] && <span className="text-green-600 text-sm">✓ opened</span>}
                        </div>
                        <span className="font-semibold text-gray-700">${g.subtotal.toFixed(2)}</span>
                      </div>
                      <ul className="text-sm text-gray-600 mb-3 space-y-1">
                        {g.items.map((it) => (
                          <li key={it.product_id} className="flex justify-between">
                            <span>{it.quantity}× {it.name}</span>
                            <span>${it.line_total.toFixed(2)}</span>
                          </li>
                        ))}
                      </ul>
                      <button
                        onClick={() => openVendor(g)}
                        className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700"
                      >
                        {g.add_to_cart_url ? `Add all to ${g.vendor_name} cart →` : `Shop ${g.vendor_name} →`}
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {practitionerGroups.length > 0 && (
                <div className="mt-5 border-2 border-purple-200 rounded-xl p-4 bg-purple-50">
                  <h3 className="font-bold text-purple-900 mb-1">Practitioner-ordered items</h3>
                  <p className="text-sm text-purple-800 mb-3">
                    {practitionerGroups.map((g) => g.vendor_name).join(", ")} products are ordered through your
                    Hackster practitioner. Request them and we’ll handle fulfillment.
                  </p>
                  <ul className="text-sm text-purple-900 mb-3 space-y-1">
                    {practitionerGroups.map((g) => g.items.map((it) => (
                      <li key={it.product_id} className="flex justify-between">
                        <span>{it.quantity}× {it.name} <span className="text-purple-500">({g.vendor_name})</span></span>
                        <span>${it.line_total.toFixed(2)}</span>
                      </li>
                    )))}
                  </ul>
                  <button onClick={() => setStep("practitioner")} className="w-full bg-purple-600 text-white py-2.5 rounded-lg font-semibold hover:bg-purple-700">
                    Request practitioner order →
                  </button>
                </div>
              )}

              <p className="text-xs text-gray-400 mt-5 leading-relaxed">
                Disclosure: Hackster.ai may earn a commission from affiliate links at no extra cost to you.
                We only recommend products we believe support your health goals.
              </p>

              <div className="mt-4 flex justify-between">
                <button onClick={() => setStep("review")} className="text-gray-500 hover:text-gray-700 text-sm">← Back</button>
                <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-sm">Done</button>
              </div>
            </div>
          )}

          {/* STEP 3 — PRACTITIONER ORDER FORM */}
          {step === "practitioner" && (
            <div>
              {!practitionerSubmitted ? (
                <div>
                  <h3 className="font-bold text-gray-900 mb-1">Practitioner Order Request</h3>
                  <p className="text-sm text-gray-600 mb-4">Share your details and we’ll reach out to arrange your practitioner-ordered products.</p>
                  <div className="space-y-3">
                    <input className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="Full name"
                      value={practitionerForm.customer_name} onChange={(e) => setPractitionerForm({ ...practitionerForm, customer_name: e.target.value })} />
                    <input className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="Email"
                      value={practitionerForm.customer_email} onChange={(e) => setPractitionerForm({ ...practitionerForm, customer_email: e.target.value })} />
                    <input className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="Phone (optional)"
                      value={practitionerForm.customer_phone} onChange={(e) => setPractitionerForm({ ...practitionerForm, customer_phone: e.target.value })} />
                    <textarea className="w-full border border-gray-300 rounded-lg px-3 py-2" placeholder="Notes (optional)" rows={3}
                      value={practitionerForm.notes} onChange={(e) => setPractitionerForm({ ...practitionerForm, notes: e.target.value })} />
                  </div>
                  <div className="mt-4 flex justify-between">
                    <button onClick={() => setStep("plan")} className="text-gray-500 hover:text-gray-700 text-sm">← Back</button>
                    <button
                      onClick={submitPractitionerOrder}
                      disabled={loading || !practitionerForm.customer_name || !practitionerForm.customer_email}
                      className="bg-purple-600 text-white px-6 py-2.5 rounded-lg font-semibold hover:bg-purple-700 disabled:opacity-40"
                    >
                      {loading ? "Submitting..." : "Submit request"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="text-center py-6">
                  <div className="text-5xl mb-3">🌿</div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">Request received!</h3>
                  <p className="text-gray-600 mb-5">Thank you — we’ll be in touch soon to arrange your practitioner-ordered products.</p>
                  <button onClick={onClose} className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2.5 rounded-lg font-semibold">Done</button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StackCheckout;
