import { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CATEGORY_LABELS = {
  frequency_healing: "Frequency Healing",
  detox: "Detox",
  nutrition: "Nutrition",
  mindfulness: "Mindfulness",
  sleep: "Sleep",
  supplements: "Supplements",
  movement: "Movement",
  general: "General",
};

// Extract a YouTube embed URL from common link formats (watch?v=, youtu.be/, /embed/, /shorts/)
const getYouTubeEmbed = (url) => {
  if (!url) return null;
  const patterns = [
    /(?:youtube\.com\/watch\?v=)([\w-]{11})/,
    /(?:youtu\.be\/)([\w-]{11})/,
    /(?:youtube\.com\/embed\/)([\w-]{11})/,
    /(?:youtube\.com\/shorts\/)([\w-]{11})/,
  ];
  for (const p of patterns) {
    const m = url.match(p);
    if (m) return `https://www.youtube.com/embed/${m[1]}`;
  }
  return null;
};

/**
 * LibraryPage — public education content library.
 * Props: NavigationComponent (the shared nav) passed from App so styling stays consistent.
 */
const LibraryPage = ({ NavigationComponent }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");
  const [active, setActive] = useState(null); // selected article for reading

  useEffect(() => { fetchContent(); }, [category]); // refetch on category change

  const fetchContent = async () => {
    setLoading(true);
    try {
      const params = {};
      if (category) params.category = category;
      if (search) params.search = search;
      const res = await axios.get(`${API}/content`, { params });
      setItems(res.data);
    } catch (e) {
      console.error("content fetch error", e);
    } finally {
      setLoading(false);
    }
  };

  const categories = Array.from(new Set(items.map((i) => i.category)));

  return (
    <div className="min-h-screen bg-gray-50">
      {NavigationComponent && <NavigationComponent />}

      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-14">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <div className="text-4xl mb-3">🌿</div>
          <h1 className="text-4xl font-bold mb-3">The Hackster Library</h1>
          <p className="text-emerald-100 text-lg max-w-2xl mx-auto">
            Learn the natural modalities behind lasting wellness — frequency healing, detox, sleep, mindfulness and more. No hype, no dependency, just knowledge to keep you free.
          </p>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          <form onSubmit={(e) => { e.preventDefault(); fetchContent(); }} className="flex-1 min-w-[220px]">
            <input
              className="w-full border border-gray-300 rounded-lg px-4 py-2"
              placeholder="Search the library…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>
          <button onClick={() => setCategory("")} className={`px-3 py-1.5 rounded-full text-sm border ${category === "" ? "bg-emerald-600 text-white border-emerald-600" : "bg-white text-gray-600 border-gray-300"}`}>All</button>
          {categories.map((c) => (
            <button key={c} onClick={() => setCategory(c)} className={`px-3 py-1.5 rounded-full text-sm border ${category === c ? "bg-emerald-600 text-white border-emerald-600" : "bg-white text-gray-600 border-gray-300"}`}>
              {CATEGORY_LABELS[c] || c}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="text-center py-16 text-gray-400">Loading…</div>
        ) : items.length === 0 ? (
          <div className="text-center py-16 text-gray-400">No articles found.</div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {items.map((it) => (
              <button key={it.id} onClick={() => setActive(it)} className="text-left bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
                {it.image_url && (
                  <div className="h-40 bg-gray-100 overflow-hidden">
                    <img src={it.image_url} alt={it.title} className="w-full h-full object-cover" />
                  </div>
                )}
                <div className="p-5">
                  <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">{CATEGORY_LABELS[it.category] || it.category}</span>
                  {getYouTubeEmbed(it.media_url) && <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full ml-1">▶ Video</span>}
                  <h3 className="font-bold text-gray-900 mt-2">{it.title}</h3>
                  <p className="text-sm text-gray-600 mt-1 line-clamp-3">{it.summary}</p>
                  <span className="text-emerald-600 text-sm font-medium mt-3 inline-block">Read →</span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Reading modal */}
      {active && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setActive(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 border-b flex items-center justify-between shrink-0">
              <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">{CATEGORY_LABELS[active.category] || active.category}</span>
              <button onClick={() => setActive(null)} className="text-2xl text-gray-400">×</button>
            </div>
            <div className="p-6 overflow-y-auto">
              {getYouTubeEmbed(active.media_url) ? (
                <div className="relative w-full mb-4" style={{ paddingBottom: "56.25%" }}>
                  <iframe
                    className="absolute inset-0 w-full h-full rounded-xl"
                    src={getYouTubeEmbed(active.media_url)}
                    title={active.title}
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              ) : active.image_url ? (
                <img src={active.image_url} alt={active.title} className="w-full h-52 object-cover rounded-xl mb-4" />
              ) : null}
              <h2 className="text-2xl font-bold text-gray-900 mb-3">{active.title}</h2>
              <div className="text-gray-700 whitespace-pre-line leading-relaxed">{active.body || active.summary}</div>
              {active.media_url && !getYouTubeEmbed(active.media_url) && (
                <a href={active.media_url} target="_blank" rel="noopener noreferrer" className="text-emerald-600 text-sm mt-4 inline-block mr-4">Watch / Listen ↗</a>
              )}
              {active.source_url && (
                <a href={active.source_url} target="_blank" rel="noopener noreferrer" className="text-emerald-600 text-sm mt-4 inline-block">Source ↗</a>
              )}
              {active.tags?.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-5">
                  {active.tags.map((t) => <span key={t} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">#{t}</span>)}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LibraryPage;
