import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  
  return (
    <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto">
      <Link to="/" className="flex items-center space-x-2">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-lg">H</span>
        </div>
        <span className="text-2xl font-bold text-gray-900">Hackster</span>
      </Link>
      <div className="hidden md:flex items-center space-x-8">
        <a href="#baseline" className="text-gray-700 hover:text-blue-600 transition-colors">Baseline</a>
        <a href="#stack" className="text-gray-700 hover:text-blue-600 transition-colors">Stack</a>
        <a href="#coaching" className="text-gray-700 hover:text-blue-600 transition-colors">Coaching</a>
        <Link to="/community" className={`transition-colors ${location.pathname === '/community' ? 'text-blue-600 font-semibold' : 'text-gray-700 hover:text-blue-600'}`}>
          Community
        </Link>
        <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
          Get Started
        </button>
      </div>
    </nav>
  );
};

// Hero Section Component
const HeroSection = () => {
  return (
    <div className="bg-gradient-to-br from-blue-50 to-purple-50 min-h-screen">
      <Navigation />

      {/* Hero Content */}
      <div className="max-w-7xl mx-auto px-6 pt-20 pb-32">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight">
            Optimize Your Health with
            <span className="text-blue-600 block">Biohacking Excellence</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-12 leading-relaxed">
            Establish your baseline, build your personalized Hackster stack, and optimize 
            with world-class coaching for a healthier + happier you.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="bg-blue-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl">
              Start Your Health Journey
            </button>
            <button className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl text-lg font-semibold hover:border-purple-600 hover:text-purple-600 transition-all">
              Watch Demo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Three Core Features Section
const CoreFeatures = () => {
  const features = [
    {
      id: "baseline",
      title: "1. Establish Your Baseline",
      subtitle: "Comprehensive Health Panels",
      description: "Get recommended health tests to identify deficiencies and establish your starting point for optimal health and vitality.",
      icon: "🎯",
      highlights: [],
      cta: "Get My Biomarkers",
      color: "blue"
    },
    {
      id: "stack",
      title: "2. Build Your Hackster Stack",
      subtitle: "Personalized Product Recommendations",
      description: "Take our smart questionnaire for personalized biohacking recommendations powered by AI.",
      icon: "⚡",
      highlights: [],
      cta: "Start Questionnaire",
      color: "purple"
    },
    {
      id: "coaching",
      title: "3. Optimize with Coaching",
      subtitle: "AI Coach + Human Experts",
      description: "Get personalized guidance from the Hackster AI coach 24/7, plus connect with certified coaches for advanced results.",
      icon: "🚀",
      highlights: [],
      cta: "Find a Coach",
      color: "blue"
    }
  ];

  return (
    <div className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Your Path to Optimal Health
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Follow our proven 3-step process to transform your health, increase energy, 
            and extend your healthspan with precision biohacking.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            // Define color classes explicitly to ensure Tailwind includes them
            const getColorClasses = (color) => {
              switch(color) {
                case 'blue':
                  return {
                    background: 'bg-gradient-to-br from-blue-50 to-blue-100',
                    border: 'border-blue-200',
                    text: 'text-blue-600',
                    button: 'bg-blue-600 hover:bg-blue-700',
                    dot: 'bg-blue-500'
                  };
                case 'purple':
                  return {
                    background: 'bg-gradient-to-br from-purple-50 to-purple-100',
                    border: 'border-purple-200',
                    text: 'text-purple-600',
                    button: 'bg-purple-600 hover:bg-purple-700',
                    dot: 'bg-purple-500'
                  };
                default:
                  return {
                    background: 'bg-gradient-to-br from-gray-50 to-gray-100',
                    border: 'border-gray-200',
                    text: 'text-gray-600',
                    button: 'bg-gray-600 hover:bg-gray-700',
                    dot: 'bg-gray-500'
                  };
              }
            };
            
            const colorClasses = getColorClasses(feature.color);
            
            return (
              <div key={feature.id} className="group hover:scale-105 transition-all duration-300">
                <div className={`${colorClasses.background} rounded-2xl p-8 h-full border ${colorClasses.border} shadow-lg hover:shadow-xl transition-all`}>
                  <div className="text-center mb-6">
                    <div className="text-4xl mb-4">{feature.icon}</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                    <p className={`${colorClasses.text} font-semibold mb-4`}>{feature.subtitle}</p>
                    <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                  </div>

                  {feature.highlights.length > 0 && (
                    <div className="space-y-3 mb-8">
                      {feature.highlights.map((highlight, idx) => (
                        <div key={idx} className="flex items-center space-x-3">
                          <div className={`w-2 h-2 ${colorClasses.dot} rounded-full`}></div>
                          <span className="text-gray-700">{highlight}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className={feature.highlights.length === 0 ? "mt-8" : ""}>
                    <button className={`w-full ${colorClasses.button} text-white py-3 rounded-xl font-semibold transition-colors shadow-md hover:shadow-lg`}>
                      {feature.cta}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// Priority Supplements Section
const PrioritySupplements = () => {
  const supplements = [
    { name: "Vitamin D3", priority: 1, description: "Essential for immune function and bone health", brands: ["Thorne", "Standard Process"] },
    { name: "Vitamin A", priority: 2, description: "Critical for vision and immune system", brands: ["Thorne", "Apex Energetics"] },
    { name: "Vitamin K2", priority: 3, description: "Bone health and cardiovascular support", brands: ["Thorne", "Standard Process"] },
    { name: "Magnesium", priority: 4, description: "300+ enzymatic reactions, sleep, and recovery", brands: ["Thorne", "Apex Energetics"] },
    { name: "Amino Acids", priority: 5, description: "Building blocks for muscle and neurotransmitters", brands: ["Thorne", "Standard Process"] },
    { name: "Multivitamin", priority: 6, description: "Foundation for nutritional gaps", brands: ["Thorne", "Apex Energetics"] }
  ];

  return (
    <div className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Supplement Stacks
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Learn science-backed supplement recommendations featuring premium brands like Thorne, 
            Apex Energetics and Standard Process for foundational health/wellness.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {supplements.map((supplement) => (
            <div key={supplement.name} className="bg-white rounded-xl p-6 shadow-lg hover:shadow-xl transition-all border">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-bold text-sm">#{supplement.priority}</span>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">{supplement.name}</h3>
                </div>
              </div>
              <p className="text-gray-600 mb-4">{supplement.description}</p>
              <div className="flex flex-wrap gap-2">
                {supplement.brands.map((brand) => (
                  <span key={brand} className="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-sm font-medium">
                    {brand}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Community Platform Component
const CommunityPlatform = () => {
  const [activeView, setActiveView] = useState('overview');
  const [posts, setPosts] = useState([]);
  const [newPost, setNewPost] = useState({ 
    title: '', 
    content: '', 
    category: 'general',
    image_url: '',
    youtube_url: ''
  });
  const [loading, setLoading] = useState(false);
  const [showNewPostForm, setShowNewPostForm] = useState(false);

  // Mock data for demo purposes
  const mockPosts = [
    {
      id: 1,
      username: "BiohackerPro",
      title: "My 30-Day Cold Exposure Journey",
      content: "Started with 30-second cold showers and worked up to 3-minute ice baths. The mental clarity and energy boost has been incredible. Here's what I learned...",
      category: "Recovery",
      created_at: "2024-12-28",
      upvotes: 24,
      downvotes: 2,
      reaction_counts: { tried_this: 8, helpful: 12, results: 5 },
      user_level: "contributor"
    },
    {
      id: 2,
      username: "OptimizeDaily",
      title: "Vitamin D3 + K2 Protocol Results",
      content: "After 3 months on this protocol, my energy levels have improved significantly. Blood work shows optimal vitamin D levels for the first time in years.",
      category: "Supplements",
      created_at: "2024-12-27",
      upvotes: 18,
      downvotes: 1,
      reaction_counts: { helpful: 15, on_point: 7, results: 9 },
      user_level: "hackster_pro"
    }
  ];

  const getUserLevel = (level) => {
    switch(level) {
      case 'hackster_pro': return { icon: '🟡', text: 'Hackster Pro', color: 'text-yellow-600 bg-yellow-100' };
      case 'contributor': return { icon: '🔵', text: 'Contributor', color: 'text-blue-600 bg-blue-100' };
      default: return null;
    }
  };

  const createPost = async (e) => {
    e.preventDefault();
    // Mock post creation
    const newPostData = {
      id: Date.now(),
      username: "You",
      ...newPost,
      created_at: new Date().toISOString().split('T')[0],
      upvotes: 0,
      downvotes: 0,
      reaction_counts: {},
      user_level: "member"
    };
    setPosts([newPostData, ...posts]);
    setNewPost({ title: '', content: '', category: 'general', image_url: '', youtube_url: '' });
    setShowNewPostForm(false);
  };

  if (activeView === 'forum') {
    return (
      <div className="py-20 bg-gradient-to-br from-blue-50 to-purple-50 min-h-screen">
        <div className="max-w-4xl mx-auto px-6">
          {/* Header */}
          <div className="text-center mb-8">
            <button 
              onClick={() => setActiveView('overview')}
              className="text-blue-600 hover:text-blue-700 mb-4 flex items-center mx-auto"
            >
              ← Back to Community Overview
            </button>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Community Forum</h1>
            <p className="text-xl text-gray-600">Share your biohacking journey and connect with fellow optimizers</p>
          </div>

          {/* New Post Button */}
          <div className="mb-8 flex justify-between items-center">
            <button
              onClick={() => setShowNewPostForm(!showNewPostForm)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium flex items-center space-x-2"
            >
              <span>📝</span>
              <span>Share Your Biohack</span>
            </button>
          </div>

          {/* New Post Form */}
          {showNewPostForm && (
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <form onSubmit={createPost} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <input
                    type="text"
                    required
                    value={newPost.title}
                    onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                    placeholder="What's your biohacking discovery?"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    value={newPost.category}
                    onChange={(e) => setNewPost({ ...newPost, category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="general">General</option>
                    <option value="nutrition">Nutrition</option>
                    <option value="supplements">Supplements</option>
                    <option value="recovery">Recovery</option>
                    <option value="sleep">Sleep</option>
                    <option value="technology">Technology</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Content</label>
                  <textarea
                    required
                    rows={4}
                    value={newPost.content}
                    onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                    placeholder="Share your experience, results, and insights..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div className="flex space-x-4">
                  <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium">
                    Post
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowNewPostForm(false)}
                    className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-6 py-2 rounded-lg font-medium"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Posts */}
          <div className="space-y-6">
            {mockPosts.map((post) => (
              <div key={post.id} className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold">{post.username.charAt(0).toUpperCase()}</span>
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-semibold text-gray-900">{post.username}</h3>
                        {(() => {
                          const levelInfo = getUserLevel(post.user_level);
                          return levelInfo ? (
                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${levelInfo.color} flex items-center space-x-1`}>
                              <span>{levelInfo.icon}</span>
                              <span>{levelInfo.text}</span>
                            </span>
                          ) : null;
                        })()}
                      </div>
                      <p className="text-sm text-gray-500">{new Date(post.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm">{post.category}</span>
                </div>

                <h2 className="text-xl font-semibold text-gray-900 mb-3">{post.title}</h2>
                <p className="text-gray-700 mb-4">{post.content}</p>

                {/* Engagement Section */}
                <div className="border-t pt-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex items-center space-x-1">
                        <button className="p-2 rounded-lg text-gray-500 hover:text-blue-600 hover:bg-blue-50">⬆️</button>
                        <span className="font-semibold text-gray-700">{post.upvotes - post.downvotes}</span>
                        <button className="p-2 rounded-lg text-gray-500 hover:text-red-600 hover:bg-red-50">⬇️</button>
                      </div>
                      <button className="flex items-center space-x-2 text-gray-500 hover:text-blue-600 p-2 rounded-lg hover:bg-blue-50">
                        <span>💬</span>
                        <span>Comment</span>
                      </button>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {[
                        { type: 'tried_this', emoji: '🔥', count: post.reaction_counts.tried_this || 0 },
                        { type: 'helpful', emoji: '💡', count: post.reaction_counts.helpful || 0 },
                        { type: 'results', emoji: '📊', count: post.reaction_counts.results || 0 }
                      ].map((reaction) => (
                        reaction.count > 0 && (
                          <span key={reaction.type} className="flex items-center space-x-1 bg-gray-100 px-2 py-1 rounded-full text-sm">
                            <span>{reaction.emoji}</span>
                            <span>{reaction.count}</span>
                          </span>
                        )
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="py-20 bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              Community & Expert Coaching
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Connect with like-minded biohackers, chat with our AI coach 24/7 plus get personalized 
              guidance from certified coaches for optimal results.
            </p>

            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">1,000+</div>
                <div className="text-gray-600">Active Members</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-2">50+</div>
                <div className="text-gray-600">Certified Coaches</div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <button 
                onClick={() => setActiveView('forum')}
                className="bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
              >
                Join Community
              </button>
              <button className="border-2 border-purple-600 text-purple-600 px-6 py-3 rounded-xl font-semibold hover:bg-purple-600 hover:text-white transition-all">
                Find a Coach
              </button>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Hackster AI Coach</h3>
              <p className="text-gray-600 mb-4">Get 24/7 personalized biohacking guidance with the Hackster AI Coach using our proprietary F.R.E.E.D.O.M. method.</p>
              <button className="text-blue-600 font-semibold hover:text-blue-700">Try AI Coach →</button>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Coach Directory</h3>
              <p className="text-gray-600 mb-4">Connect with certified nutritionists, fitness coaches, and wellness experts in your area.</p>
              <button className="text-blue-600 font-semibold hover:text-blue-700">Browse Coaches →</button>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Community Forum</h3>
              <p className="text-gray-600 mb-4">Share your results, get support, and learn from thousands of fellow biohackers.</p>
              <button 
                onClick={() => setActiveView('forum')}
                className="text-purple-600 font-semibold hover:text-purple-700"
              >
                Join Discussion →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Alias for backward compatibility
const CommunityCoaching = CommunityPlatform;

// Main Home Component
const Home = () => {
  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log("Backend connected:", response.data.message);
    } catch (e) {
      console.error("Backend connection error:", e);
    }
  };

  useEffect(() => {
    helloWorldApi();
  }, []);

  return (
    <div className="min-h-screen">
      <HeroSection />
      <CoreFeatures />
      <PrioritySupplements />
      <CommunityCoaching />
      
      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="flex items-center justify-center space-x-2 mb-6">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">H</span>
            </div>
            <span className="text-2xl font-bold">Hackster</span>
          </div>
          <p className="text-gray-400 mb-8">
            Empowering your biohacking journey with science-backed solutions and expert guidance.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center space-x-8">
            <a href="#" className="text-gray-400 hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="text-gray-400 hover:text-white transition-colors">Terms of Service</a>
            <a href="#" className="text-gray-400 hover:text-white transition-colors">Contact Us</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;