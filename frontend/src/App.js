import { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.exp * 1000 > Date.now()) {
          const userData = JSON.parse(localStorage.getItem('user') || '{}');
          setUser(userData);
        } else {
          logout();
        }
      } catch {
        logout();
      }
    }
  }, [token]);

  const login = (userData, authToken) => {
    setUser(userData);
    setToken(authToken);
    localStorage.setItem('token', authToken);
    localStorage.setItem('user', JSON.stringify(userData));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user,
    isCoach: user?.role === 'coach'
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  const { isAuthenticated, user, logout } = useAuth();
  
  return (
    <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto">
      <Link to="/" className="flex items-center space-x-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">H</span>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center space-x-2">
              <span className="text-2xl font-bold text-gray-900">Hackster.ai</span>
              <span className="bg-blue-100 text-blue-600 px-2 py-1 rounded-full text-xs font-semibold">BETA</span>
            </div>
            <span className="text-xs text-gray-500 -mt-1">Your biohacking buddy</span>
          </div>
        </div>
      </Link>
      <div className="hidden md:flex items-center space-x-8">
        <Link to="/community" className={`transition-colors ${location.pathname === '/community' ? 'text-blue-600 font-semibold' : 'text-gray-700 hover:text-blue-600'}`}>
          Community
        </Link>
        <Link to="/coaches" className={`transition-colors ${location.pathname === '/coaches' ? 'text-blue-600 font-semibold' : 'text-gray-700 hover:text-blue-600'}`}>
          Find a Coach
        </Link>
        <Link to="/get-started" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
          Get Started
        </Link>
        
        {isAuthenticated ? (
          <div className="flex items-center space-x-4">
            <span className="text-gray-700 text-sm">
              Welcome, {user.username}!
              {user.role === 'coach' && (
                <span className="ml-2 px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                  Coach
                </span>
              )}
            </span>
            <button
              onClick={logout}
              className="text-gray-700 hover:text-red-600 transition-colors text-sm"
            >
              Logout
            </button>
          </div>
        ) : (
          <Link to="/login" className="text-gray-700 hover:text-blue-600 transition-colors">
            Login
          </Link>
        )}
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
      color: "blue",
      link: "/get-started"
    },
    {
      id: "stack",
      title: "2. Build Your Hackster Stack",
      subtitle: "Personalized Product Recommendations", 
      description: "Take our smart questionnaire for personalized biohacking recommendations powered by AI.",
      icon: "⚡",
      highlights: [],
      cta: "Start Questionnaire",
      color: "purple",
      link: "/get-started"
    },
    {
      id: "coaching",
      title: "3. Optimize with Coaching",
      subtitle: "AI Coach + Human Experts",
      description: "Get personalized guidance from the Hackster AI coach 24/7, plus connect with certified coaches for advanced results.",
      icon: "🚀",
      highlights: [],
      cta: "Find a Coach",
      color: "blue",
      link: "/coaches"
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
                    <Link 
                      to={feature.link || "#"}
                      className={`w-full ${colorClasses.button} text-white py-3 rounded-xl font-semibold transition-colors shadow-md hover:shadow-lg block text-center`}
                    >
                      {feature.cta}
                    </Link>
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
              <Link 
                to="/community"
                className="bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors text-center"
              >
                Join Community
              </Link>
              <Link 
                to="/coaches"
                className="border-2 border-purple-600 text-purple-600 px-6 py-3 rounded-xl font-semibold hover:bg-purple-600 hover:text-white transition-all text-center"
              >
                Find a Coach
              </Link>
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
              <Link 
                to="/community"
                className="text-purple-600 font-semibold hover:text-purple-700"
              >
                Join Discussion →
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Community Landing Page Component (from LauraZook/Hackster repo)
const CommunityLanding = () => {
  const [showSignUp, setShowSignUp] = useState(false);

  if (showSignUp) {
    return <SignUpForm setShowSignUp={setShowSignUp} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />

      {/* Dynamic Wellness Lifestyle Banner */}
      <div className="relative bg-gradient-to-r from-blue-800 to-purple-600 py-16 overflow-hidden">
        {/* Background Collage */}
        <div className="absolute inset-0 opacity-20">
          <div className="grid grid-cols-6 h-full">
            <div 
              className="bg-cover bg-center"
              style={{
                backgroundImage: "url('https://images.unsplash.com/photo-1506126613408-eca07ce68773?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwxfHxoZWFsdGh5JTIwbGlmZXN0eWxlfGVufDB8fHx8MTc1NDE5MDY5N3ww&ixlib=rb-4.1.0&q=85')"
              }}
            ></div>
            <div 
              className="bg-cover bg-center"
              style={{
                backgroundImage: "url('https://images.unsplash.com/photo-1556911073-a517e752729c?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxoZWFsdGh5JTIwbGlmZXN0eWxlfGVufDB8fHx8MTc1NDE5MDY5N3ww&ixlib=rb-4.1.0&q=85')"
              }}
            ></div>
            <div 
              className="bg-cover bg-center"
              style={{
                backgroundImage: "url('https://images.unsplash.com/photo-1607962837359-5e7e89f86776?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHw0fHxoZWFsdGh5JTIwbGlmZXN0eWxlfGVufDB8fHx8MTc1NDE5MDY5N3ww&ixlib=rb-4.1.0&q=85')"
              }}
            ></div>
            <div 
              className="bg-cover bg-center"
              style={{
                backgroundImage: "url('https://images.pexels.com/photos/1128678/pexels-photo-1128678.jpeg')"
              }}
            ></div>
            <div 
              className="bg-cover bg-center"
              style={{
                backgroundImage: "url('https://images.unsplash.com/photo-1542337010-818168f9bc1f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwxfHx3ZWxsbmVzcyUyMHBlb3BsZXxlbnwwfHx8fDE3NTQxOTA3MDh8MA&ixlib=rb-4.1.0&q=85')"
              }}
            ></div>
            <div 
              className="bg-cover bg-center"
              style={{
                backgroundImage: "url('https://images.unsplash.com/photo-1599948093964-321ae97fe7b4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwyfHx3ZWxsbmVzcyUyMHBlb3BsZXxlbnwwfHx8fDE3NTQxOTA3MDh8MA&ixlib=rb-4.1.0&q=85')"
              }}
            ></div>
          </div>
        </div>
        
        {/* Content Overlay */}
        <div className="relative max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Share Your Journey
          </h1>
          <p className="text-xl text-blue-100 mb-4 max-w-3xl mx-auto">
            Connect with fellow Hacksters! Share your experiences, discoveries, and insights.
          </p>
          <p className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto">
            Join a supportive community of enthusiasts transforming their health daily.
          </p>
          
          {/* Activity Icons */}
          <div className="flex justify-center items-center space-x-8 mb-8 text-white">
            <div className="text-center">
              <div className="text-3xl mb-2">🥤</div>
              <p className="text-sm text-blue-100">Nutrition</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🏃‍♀️</div>
              <p className="text-sm text-blue-100">Exercise</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">🧘‍♀️</div>
              <p className="text-sm text-blue-100">Mindfulness</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">⌚</div>
              <p className="text-sm text-blue-100">Tracking</p>
            </div>
            <div className="text-center">
              <div className="text-3xl mb-2">😴</div>
              <p className="text-sm text-blue-100">Recovery</p>
            </div>
          </div>
          
          <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 max-w-md mx-auto">
            <h3 className="text-xl font-semibold text-white mb-4">Ready to Connect?</h3>
            <p className="text-blue-100 mb-6 text-sm">
              Please sign up to share your biohacking experiences and connect with the Hackster.ai community.
            </p>
            <button
              onClick={() => setShowSignUp(true)}
              className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors w-full"
            >
              Join Community
            </button>
          </div>
        </div>
      </div>
      
      {/* Features Preview */}
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="grid md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-blue-600 text-2xl">💬</span>
            </div>
            <h3 className="text-lg font-semibold mb-2">Share Experiences</h3>
            <p className="text-gray-600 text-sm">Post your biohacking experiments, results, and discoveries with the community.</p>
          </div>
          <div>
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-purple-600 text-2xl">🤝</span>
            </div>
            <h3 className="text-lg font-semibold mb-2">Connect & Learn</h3>
            <p className="text-gray-600 text-sm">Engage with fellow Hacksters, comment on posts, and learn from each others' journey.</p>
          </div>
          <div>
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-blue-600 text-2xl">📈</span>
            </div>
            <h3 className="text-lg font-semibold mb-2">Track Progress</h3>
            <p className="text-gray-600 text-sm">Document your health journey and get feedback from experienced biohackers.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Sign Up Form Component
const SignUpForm = ({ setShowSignUp }) => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // Mock registration - replace with actual API call
    setTimeout(() => {
      setLoading(false);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        setShowSignUp(false);
      }, 2000);
    }, 1000);
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
          <div className="text-green-600 text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome to Hackster!</h2>
          <p className="text-gray-600">Your account has been created successfully.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <Link to="/" className="flex items-center justify-center space-x-3 mb-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">H</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl font-bold text-gray-900">Hackster.ai</span>
                  <span className="bg-blue-100 text-blue-600 px-2 py-1 rounded-full text-xs font-semibold">BETA</span>
                </div>
                <span className="text-xs text-gray-500 -mt-1">Your biohacking buddy</span>
              </div>
            </div>
          </Link>
          <h2 className="text-3xl font-extrabold text-gray-900">
            Join the Community
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            Start your biohacking journey with fellow optimizers
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Choose a username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Create a password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Creating Account...' : 'Join Community'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              onClick={() => setShowSignUp(false)}
              className="text-blue-600 hover:text-blue-500 text-sm"
            >
              ← Back to Community
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// AI Coach Get Started Flow
const GetStartedFlow = () => {
  const [currentStep, setCurrentStep] = useState('welcome');
  const [userResponses, setUserResponses] = useState({
    hasBaselineTesting: null,
    healthGoals: [],
    currentSupplements: [],
    testingPreference: null,
    age: '',
    gender: '',
    activityLevel: ''
  });

  const handleResponse = (key, value) => {
    setUserResponses(prev => ({ ...prev, [key]: value }));
  };

  const nextStep = () => {
    switch(currentStep) {
      case 'welcome':
        setCurrentStep('baseline-check');
        break;
      case 'baseline-check':
        if (userResponses.hasBaselineTesting === false) {
          setCurrentStep('testing-options');
        } else {
          setCurrentStep('questionnaire');
        }
        break;
      case 'testing-options':
        if (userResponses.testingPreference === 'skip') {
          setCurrentStep('questionnaire');
        } else {
          setCurrentStep('testing-recommendations');
        }
        break;
      case 'testing-recommendations':
        setCurrentStep('questionnaire');
        break;
      case 'questionnaire':
        setCurrentStep('recommendations');
        break;
      default:
        break;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <Navigation />
      
      <div className="max-w-4xl mx-auto px-6 py-12">
        {currentStep === 'welcome' && (
          <div className="text-center">
            <div className="mb-8">
              <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <span className="text-white text-3xl">🤖</span>
              </div>
              <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome to Your Hackster AI Coach!</h1>
              <p className="text-xl text-gray-600 mb-8">
                Let's start with understanding where you are today and what goals we'll work on achieving.
              </p>
            </div>
            
            <div className="bg-white rounded-xl p-8 shadow-lg mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">What I'll help you with:</h2>
              <div className="grid md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl mb-3">🎯</div>
                  <h3 className="font-semibold mb-2">Establish Baseline</h3>
                  <p className="text-gray-600 text-sm">Identify the right health tests for your specific goals</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl mb-3">⚡</div>
                  <h3 className="font-semibold mb-2">Build Your Stack</h3>
                  <p className="text-gray-600 text-sm">Get personalized Hackster recommendations</p>
                </div>
                <div className="text-center">
                  <div className="text-3xl mb-3">🚀</div>
                  <h3 className="font-semibold mb-2">Optimize Results</h3>
                  <p className="text-gray-600 text-sm">Connect you with expert live coaches when you're ready</p>
                </div>
              </div>
            </div>

            <button
              onClick={nextStep}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-colors"
            >
              Let's Start! →
            </button>
          </div>
        )}

        {currentStep === 'baseline-check' && (
          <div className="bg-white rounded-xl p-8 shadow-lg">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">First, let's talk about your health data</h2>
            <p className="text-lg text-gray-600 mb-8">
              Understanding your current health markers is crucial for effective biohacking. 
              Have you done any comprehensive health testing in the past 12 months?
            </p>

            <div className="space-y-4">
              <button
                onClick={() => {
                  handleResponse('hasBaselineTesting', true);
                  nextStep();
                }}
                className="w-full p-6 text-left bg-green-50 border-2 border-green-200 rounded-xl hover:bg-green-100 transition-colors"
              >
                <div className="text-xl font-semibold text-green-800 mb-2">✅ Yes, I have recent test results</div>
                <p className="text-green-700">I've done blood work, hormone panels, or other health testing recently</p>
              </button>

              <button
                onClick={() => {
                  handleResponse('hasBaselineTesting', false);
                  nextStep();
                }}
                className="w-full p-6 text-left bg-blue-50 border-2 border-blue-200 rounded-xl hover:bg-blue-100 transition-colors"
              >
                <div className="text-xl font-semibold text-blue-800 mb-2">📋 No, I need to get tested</div>
                <p className="text-blue-700">I haven't done comprehensive health testing recently</p>
              </button>
            </div>
          </div>
        )}

        {currentStep === 'testing-options' && (
          <div className="bg-white rounded-xl p-8 shadow-lg">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Let's get your health baseline established</h2>
            <p className="text-lg text-gray-600 mb-8">
              Getting proper health testing is the foundation of effective biohacking. Would you like to see 
              our recommended testing options, or would you prefer to skip to building your supplement stack?
            </p>

            <div className="space-y-4">
              <button
                onClick={() => {
                  handleResponse('testingPreference', 'show-options');
                  nextStep();
                }}
                className="w-full p-6 text-left bg-emerald-50 border-2 border-emerald-200 rounded-xl hover:bg-emerald-100 transition-colors"
              >
                <div className="text-xl font-semibold text-emerald-800 mb-2">🎯 Show me testing recommendations</div>
                <p className="text-emerald-700">I want to see the best health testing options for my goals</p>
              </button>

              <button
                onClick={() => {
                  handleResponse('testingPreference', 'skip');
                  nextStep();
                }}
                className="w-full p-6 text-left bg-purple-50 border-2 border-purple-200 rounded-xl hover:bg-purple-100 transition-colors"
              >
                <div className="text-xl font-semibold text-purple-800 mb-2">⚡ Skip to supplement recommendations</div>
                <p className="text-purple-700">I'll handle testing later, show me supplements now</p>
              </button>
            </div>
          </div>
        )}

        {currentStep === 'testing-recommendations' && (
          <div className="bg-white rounded-xl p-8 shadow-lg">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Recommended Health Testing</h2>
            <p className="text-lg text-gray-600 mb-8">
              Based on your goals, here are our top recommendations for comprehensive health testing:
            </p>

            <div className="space-y-6 mb-8">
              <div className="border-2 border-blue-200 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-bold text-gray-900">Function Health - Complete Panel</h3>
                  <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">Most Popular</span>
                </div>
                <p className="text-gray-600 mb-4">110+ biomarkers including vitamins, minerals, hormones, and metabolic markers</p>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-blue-600">$499-699</span>
                  <a href="https://functionhealth.com" target="_blank" rel="noopener noreferrer" 
                     className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium">
                    Get Testing →
                  </a>
                </div>
              </div>

              <div className="border-2 border-purple-200 rounded-xl p-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">Thorne - Personalized Testing</h3>
                <p className="text-gray-600 mb-4">Genetic testing + biomarker analysis for personalized supplement recommendations</p>
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-purple-600">$149-299</span>
                  <a href="https://thorne.com" target="_blank" rel="noopener noreferrer" 
                     className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2 rounded-lg font-medium">
                    Get Testing →
                  </a>
                </div>
              </div>
            </div>

            <div className="text-center">
              <button
                onClick={nextStep}
                className="bg-green-600 hover:bg-green-700 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-colors"
              >
                Continue to Questionnaire →
              </button>
            </div>
          </div>
        )}

        {currentStep === 'questionnaire' && (
          <div className="bg-white rounded-xl p-8 shadow-lg">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Smart Health Questionnaire</h2>
            <p className="text-lg text-gray-600 mb-8">
              Let's gather some information to create your personalized Hackster Stack:
            </p>

            <div className="space-y-6">
              <div>
                <label className="block text-lg font-semibold text-gray-700 mb-4">What are your primary health goals? (Select all that apply)</label>
                <div className="grid md:grid-cols-2 gap-3">
                  {['Increase Energy', 'Better Sleep', 'Improve Focus', 'Build Muscle', 'Lose Weight', 'Reduce Stress', 'Boost Immunity', 'Optimize Hormones'].map(goal => (
                    <button
                      key={goal}
                      onClick={() => {
                        const current = userResponses.healthGoals || [];
                        const updated = current.includes(goal) 
                          ? current.filter(g => g !== goal)
                          : [...current, goal];
                        handleResponse('healthGoals', updated);
                      }}
                      className={`p-3 text-left rounded-lg border-2 transition-colors ${
                        (userResponses.healthGoals || []).includes(goal)
                          ? 'bg-blue-100 border-blue-500 text-blue-800'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      {goal}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-lg font-semibold text-gray-700 mb-3">Age Range</label>
                  <select
                    value={userResponses.age}
                    onChange={(e) => handleResponse('age', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select age</option>
                    <option value="18-25">18-25</option>
                    <option value="26-35">26-35</option>
                    <option value="36-45">36-45</option>
                    <option value="46-55">46-55</option>
                    <option value="56-65">56-65</option>
                    <option value="65+">65+</option>
                  </select>
                </div>

                <div>
                  <label className="block text-lg font-semibold text-gray-700 mb-3">Gender</label>
                  <select
                    value={userResponses.gender}
                    onChange={(e) => handleResponse('gender', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-lg font-semibold text-gray-700 mb-3">Activity Level</label>
                  <select
                    value={userResponses.activityLevel}
                    onChange={(e) => handleResponse('activityLevel', e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select level</option>
                    <option value="sedentary">Sedentary</option>
                    <option value="light">Light Activity</option>
                    <option value="moderate">Moderate Activity</option>
                    <option value="active">Very Active</option>
                    <option value="athlete">Athlete</option>
                  </select>
                </div>
              </div>

              <div className="text-center pt-6">
                <button
                  onClick={nextStep}
                  disabled={!userResponses.healthGoals?.length || !userResponses.age || !userResponses.gender || !userResponses.activityLevel}
                  className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-8 py-4 rounded-xl text-lg font-semibold transition-colors"
                >
                  Get My Personalized Stack →
                </button>
              </div>
            </div>
          </div>
        )}

        {currentStep === 'recommendations' && (
          <div className="bg-white rounded-xl p-8 shadow-lg">
            <h2 className="text-3xl font-bold text-gray-900 mb-6">Your Personalized Hackster Stack</h2>
            <p className="text-lg text-gray-600 mb-8">
              Based on your responses, here's your AI-powered supplement and biohacking recommendations:
            </p>

            <div className="space-y-6 mb-8">
              {/* Priority Supplements based on responses */}
              <div className="border-l-4 border-blue-500 pl-6">
                <h3 className="text-xl font-bold text-blue-800 mb-3">🥇 Priority #1: Vitamin D3 + K2</h3>
                <p className="text-gray-600 mb-2">Essential for immune function, bone health, and mood regulation</p>
                <p className="text-sm text-blue-600 font-medium">Recommended: Thorne Vitamin D/K2 Liquid</p>
              </div>

              {userResponses.healthGoals?.includes('Increase Energy') && (
                <div className="border-l-4 border-green-500 pl-6">
                  <h3 className="text-xl font-bold text-green-800 mb-3">⚡ For Energy: Magnesium + B-Complex</h3>
                  <p className="text-gray-600 mb-2">Supports cellular energy production and reduces fatigue</p>
                  <p className="text-sm text-green-600 font-medium">Recommended: Thorne Magnesium Bisglycinate + Basic B Complex</p>
                </div>
              )}

              {userResponses.healthGoals?.includes('Better Sleep') && (
                <div className="border-l-4 border-purple-500 pl-6">
                  <h3 className="text-xl font-bold text-purple-800 mb-3">😴 For Sleep: Magnesium + L-Theanine</h3>
                  <p className="text-gray-600 mb-2">Promotes relaxation and improves sleep quality</p>
                  <p className="text-sm text-purple-600 font-medium">Recommended: Thorne Magnesium Bisglycinate + L-Theanine</p>
                </div>
              )}

              {userResponses.activityLevel === 'athlete' && (
                <div className="border-l-4 border-orange-500 pl-6">
                  <h3 className="text-xl font-bold text-orange-800 mb-3">🏃‍♂️ For Athletes: Essential Amino Acids</h3>
                  <p className="text-gray-600 mb-2">Supports muscle recovery and protein synthesis</p>
                  <p className="text-sm text-orange-600 font-medium">Recommended: Thorne Amino Complex</p>
                </div>
              )}

              <div className="border-l-4 border-gray-500 pl-6">
                <h3 className="text-xl font-bold text-gray-800 mb-3">🆓 Free Biohacks</h3>
                <ul className="space-y-2 text-gray-600">
                  <li>• Morning sunlight exposure (10-30 minutes)</li>
                  <li>• Cold shower finish (30-90 seconds)</li>
                  <li>• Box breathing before bed (4-4-4-4 pattern)</li>
                </ul>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <Link 
                to="/community" 
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-6 py-4 rounded-xl font-semibold text-center transition-colors"
              >
                Join Community to Share Results
              </Link>
              <Link 
                to="/coaches" 
                className="flex-1 border-2 border-purple-600 text-purple-600 hover:bg-purple-600 hover:text-white px-6 py-4 rounded-xl font-semibold text-center transition-colors"
              >
                Find a Coach for Advanced Guidance
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Authentication Selection Page
const AuthSelectionPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navigation />
      
      <div className="sm:mx-auto sm:w-full sm:max-w-2xl">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Join Hackster.ai</h2>
          <p className="text-xl text-gray-600">Choose how you'd like to participate in our biohacking community</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Community Member Card */}
          <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition-shadow">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-blue-600 text-2xl">👥</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Join Community</h3>
              <p className="text-gray-600">Share your biohacking journey, connect with others, and learn from the community</p>
            </div>
            
            <div className="space-y-3 mb-8">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-gray-700">Share experiments and results</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-gray-700">Get personalized AI recommendations</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-gray-700">Access community forum</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-gray-700">Connect with fellow biohackers</span>
              </div>
            </div>

            <Link 
              to="/signup/member"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium text-center block transition-colors"
            >
              Join as Member
            </Link>
          </div>

          {/* Coach Card */}
          <div className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition-shadow border-2 border-purple-200">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-purple-600 text-2xl">🎯</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Become a Coach</h3>
              <p className="text-gray-600">Connect with Hackster members to shape better, healthier futures.</p>
            </div>
            
            <div className="space-y-3 mb-8">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-gray-700">Create professional profile</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-gray-700">Get client inquiries</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-gray-700">Free trial during beta</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-gray-700">$79/year after trial (no commissions!)</span>
              </div>
            </div>

            <Link 
              to="/signup/coach"
              className="w-full bg-purple-600 hover:bg-purple-700 text-white py-3 px-4 rounded-lg font-medium text-center block transition-colors"
            >
              Become a Coach
            </Link>
          </div>
        </div>

        <div className="text-center mt-8">
          <p className="text-gray-600">Already have an account?</p>
          <Link to="/signin" className="text-blue-600 hover:text-blue-700 font-medium">
            Sign in here
          </Link>
        </div>
      </div>
    </div>
  );
};

// Sign In Page (for existing users)
const SignInPage = () => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        login(data.user, data.access_token);
        window.location.href = '/'; // Redirect to home
      } else {
        setError(data.detail || 'Login failed');
      }
    } catch (err) {
      // Mock successful login for demo
      login({ username: formData.email.split('@')[0], email: formData.email, role: 'member' }, 'mock-token');
      window.location.href = '/';
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navigation />
      
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-extrabold text-gray-900">Welcome Back</h2>
          <p className="mt-2 text-sm text-gray-600">Sign in to your Hackster.ai account</p>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link to="/login" className="text-blue-600 hover:text-blue-500">
              Need an account? Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

// Member Registration Page
const MemberSignUpPage = () => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...formData, role: 'member' }),
      });

      const data = await response.json();

      if (response.ok) {
        login(data.user, data.access_token);
        window.location.href = '/community'; // Redirect to community
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      // Mock successful registration for demo
      login({ 
        username: formData.username, 
        email: formData.email, 
        role: 'member' 
      }, 'mock-token');
      window.location.href = '/community';
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navigation />
      
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center mb-6">
            <span className="text-white text-2xl">👥</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Join the Community</h2>
          <p className="mt-2 text-lg text-gray-600">Start your biohacking journey with fellow optimizers</p>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-lg sm:rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Choose a username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Create a password"
              />
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <h3 className="text-blue-800 font-semibold mb-2">🎉 What you'll get:</h3>
              <ul className="text-blue-700 text-sm space-y-1">
                <li>• Access to the community forum</li>
                <li>• AI-powered biohacking recommendations</li>
                <li>• Connect with fellow biohackers</li>
                <li>• Share your experiments and results</li>
              </ul>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Creating Account...' : 'Join Community'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link to="/signin" className="text-blue-600 hover:text-blue-500 text-sm">
              Already have an account? Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

// Coach Registration Page
const CoachSignUpPage = () => {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...formData, role: 'coach' }),
      });

      const data = await response.json();

      if (response.ok) {
        login(data.user, data.access_token);
        window.location.href = '/onboarding/coach'; // Redirect to coach onboarding
      } else {
        setError(data.detail || 'Registration failed');
      }
    } catch (err) {
      // Mock successful registration for demo
      login({ 
        username: formData.username, 
        email: formData.email, 
        role: 'coach' 
      }, 'mock-token');
      window.location.href = '/onboarding/coach';
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <Navigation />
      
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto h-12 w-12 bg-purple-600 rounded-lg flex items-center justify-center mb-6">
            <span className="text-white text-2xl">🎯</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Become a Coach</h2>
          <p className="mt-2 text-lg text-gray-600">Join Hackster.ai's community of wellness professionals</p>
          <p className="mt-1 text-sm text-purple-600 font-medium">FREE 30-day trial • All features included</p>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow-lg sm:rounded-lg sm:px-10">
          <div className="mb-6 p-4 bg-purple-50 rounded-lg">
            <h3 className="text-sm font-semibold text-purple-900 mb-2">Your 30-day FREE trial includes:</h3>
            <ul className="text-sm text-purple-800 space-y-1">
              <li>• Complete professional profile</li>
              <li>• Direct client connections & inquiries</li>
              <li>• Full visibility in our coach directory</li>
              <li>• All premium features unlocked</li>
            </ul>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Professional Email</label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                placeholder="Enter your professional email"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                type="text"
                required
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                placeholder="Choose your username"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                placeholder="Create a secure password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
            >
              {loading ? 'Creating Account...' : 'Start Free Trial'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <Link to="/signin" className="text-purple-600 hover:text-purple-500 text-sm">
              Already have an account? Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

// Coaches Page (adapted from LauraZook/Hackster)
const CoachesPage = () => {
  const [coaches, setCoaches] = useState([]);
  const [loading, setLoading] = useState(false);

  // Mock coaches data
  const mockCoaches = [
    {
      id: 1,
      full_name: "Dr. Sarah Martinez",
      email: "sarah@hackstercoach.com",
      phone: "(555) 123-4567",
      location: "Los Angeles, CA",
      specialties: ["Hormone Optimization", "Gut Health", "Weight Management"],
      bio: "15+ years helping clients optimize health through personalized nutrition and lifestyle interventions. Certified Functional Medicine Practitioner specializing in hormone balance and metabolic health.",
      pricing: "$150-200/session",
      website: "https://sarahmartinez.com",
      profile_image: null,
      years_experience: 15
    },
    {
      id: 2,
      full_name: "Mike Chen",
      email: "mike@hackstercoach.com", 
      phone: "(555) 987-6543",
      location: "Austin, TX",
      specialties: ["Athletic Performance", "Cold Therapy", "Breathwork"],
      bio: "Former professional athlete turned biohacking coach specializing in performance optimization. Certified in Wim Hof Method and advanced breathwork techniques.",
      pricing: "$100-150/session",
      website: "https://mikechen.fitness",
      profile_image: null,
      years_experience: 8
    }
  ];

  useEffect(() => {
    setCoaches(mockCoaches);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Find a Wellness Coach</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Connect with certified health & wellness pros with biohacking expertise to accelerate your Hackster journey today!
          </p>
        </div>

        {/* Become a Coach Section */}
        <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-purple-600 rounded-lg p-8 mb-12 text-center text-white">
          <h2 className="text-xl font-semibold mb-4 leading-relaxed">
            Are you a wellness practitioner who loves transforming lives? Add your professional listing to the Hackster.ai community!
          </h2>
          <p className="mb-6">Share your expertise and help others. Join the Hackster.ai community for free.</p>
          <Link to="/community" className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
            Join Now
          </Link>
        </div>

        {/* Coaches Grid */}
        {coaches.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {coaches.map((coach) => (
              <div key={coach.id} className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow">
                <div className="text-center mb-4">
                  {coach.profile_image ? (
                    <img
                      src={coach.profile_image}
                      alt={coach.full_name}
                      className="w-20 h-20 object-cover rounded-full mx-auto mb-3 border-4 border-blue-100"
                    />
                  ) : (
                    <div className="w-20 h-20 bg-blue-500 rounded-full mx-auto mb-3 flex items-center justify-center">
                      <span className="text-white text-2xl font-bold">
                        {coach.full_name?.charAt(0)?.toUpperCase()}
                      </span>
                    </div>
                  )}
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {coach.full_name}
                  </h3>
                  {coach.location && (
                    <p className="text-sm text-gray-500 mb-2">📍 {coach.location}</p>
                  )}
                  
                  <div className="flex flex-wrap justify-center gap-1 mb-3">
                    {coach.specialties.map((specialty) => (
                      <span
                        key={specialty}
                        className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs"
                      >
                        {specialty}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-sm text-gray-700 mb-2">About</h4>
                    <p className="text-gray-600 text-sm leading-relaxed">{coach.bio}</p>
                  </div>

                  <div>
                    <h4 className="font-semibold text-sm text-gray-700">Services</h4>
                    <p className="text-blue-600 font-semibold text-sm">{coach.pricing}</p>
                  </div>

                  {coach.website && (
                    <div>
                      <h4 className="font-semibold text-sm text-gray-700 mb-2">Website</h4>
                      <a 
                        href={coach.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-700 text-sm flex items-center"
                      >
                        🌐 {coach.website}
                      </a>
                    </div>
                  )}

                  <div className="border-t pt-3">
                    <h4 className="font-semibold text-sm text-gray-700 mb-2">Contact</h4>
                    <div className="space-y-1">
                      <a 
                        href={`mailto:${coach.email}`}
                        className="text-blue-600 hover:text-blue-700 text-sm flex items-center"
                      >
                        📧 {coach.email}
                      </a>
                      {coach.phone && (
                        <a 
                          href={`tel:${coach.phone}`}
                          className="text-blue-600 hover:text-blue-700 text-sm flex items-center"
                        >
                          📞 {coach.phone}
                        </a>
                      )}
                    </div>
                  </div>
                </div>

                <div className="mt-6">
                  <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium transition-colors">
                    📞 Contact Coach
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No coaches yet</h3>
            <p className="text-gray-600 mb-6">Be among the first wellness coaches to join our community!</p>
            <Link to="/community" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium">
              Become the First Coach
            </Link>
          </div>
        )}
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
          <div className="flex items-center justify-center space-x-3 mb-6">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">H</span>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center space-x-2">
                  <span className="text-2xl font-bold">Hackster.ai</span>
                  <span className="bg-blue-100 text-blue-600 px-2 py-1 rounded-full text-xs font-semibold">BETA</span>
                </div>
                <span className="text-xs text-gray-400 -mt-1">Your biohacking buddy</span>
              </div>
            </div>
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

// Coach Onboarding Page
const CoachOnboardingPage = () => {
  const { user, token } = useAuth();
  const [coachProfile, setCoachProfile] = useState({
    full_name: '',
    bio: '',
    specialties: [],
    years_experience: 0,
    location: '',
    website: '',
    phone: '',
    pricing: '',
    profile_image: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const availableSpecialties = [
    'Nutrition', 'Weight Management', 'Hormone Optimization', 
    'Athletic Performance', 'Sleep Optimization', 'Stress Management',
    'Gut Health', 'Cold Therapy', 'Breathwork', 'Longevity',
    'Functional Medicine', 'Biohacking', 'Supplements'
  ];

  const toggleSpecialty = (specialty) => {
    if (coachProfile.specialties.includes(specialty)) {
      setCoachProfile({
        ...coachProfile,
        specialties: coachProfile.specialties.filter(s => s !== specialty)
      });
    } else {
      setCoachProfile({
        ...coachProfile,
        specialties: [...coachProfile.specialties, specialty]
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Mock successful profile creation for demo
      setTimeout(() => {
        setLoading(false);
        alert('🎉 Congratulations! Your coach profile is now live with a 30-day free trial!');
        window.location.href = '/coaches';
      }, 1000);
    } catch (err) {
      setError('Profile creation failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 py-12">
      <Navigation />
      
      <div className="max-w-2xl mx-auto px-4">
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-purple-600 rounded-full flex items-center justify-center mb-6">
            <span className="text-white text-3xl">🎯</span>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Complete Your Coach Profile</h1>
          <p className="text-xl text-gray-600">Let's set up your professional profile to start connecting with clients</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Full Name *</label>
              <input
                type="text"
                required
                value={coachProfile.full_name}
                onChange={(e) => setCoachProfile({ ...coachProfile, full_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Dr. Jane Smith"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Professional Bio *</label>
              <textarea
                required
                rows={4}
                value={coachProfile.bio}
                onChange={(e) => setCoachProfile({ ...coachProfile, bio: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="Tell potential clients about your background, expertise, and approach to wellness coaching..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Your Specialties *</label>
              <div className="grid grid-cols-2 gap-2">
                {availableSpecialties.map(specialty => (
                  <button
                    key={specialty}
                    type="button"
                    onClick={() => toggleSpecialty(specialty)}
                    className={`px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                      coachProfile.specialties.includes(specialty)
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {specialty}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">Select all that apply</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Years of Experience</label>
                <input
                  type="number"
                  value={coachProfile.years_experience}
                  onChange={(e) => setCoachProfile({ ...coachProfile, years_experience: parseInt(e.target.value) || 0 })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  min="0"
                  max="50"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Location *</label>
                <input
                  type="text"
                  required
                  value={coachProfile.location}
                  onChange={(e) => setCoachProfile({ ...coachProfile, location: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="City, Country"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Phone Number</label>
              <input
                type="tel"
                value={coachProfile.phone}
                onChange={(e) => setCoachProfile({ ...coachProfile, phone: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="(555) 123-4567"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Pricing</label>
              <input
                type="text"
                value={coachProfile.pricing}
                onChange={(e) => setCoachProfile({ ...coachProfile, pricing: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="e.g., $150/session, $500/month"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Website (Optional)</label>
              <input
                type="url"
                value={coachProfile.website}
                onChange={(e) => setCoachProfile({ ...coachProfile, website: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="https://www.yoursite.com"
              />
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <h3 className="text-purple-800 font-semibold mb-2">🚀 Ready to Launch Your Profile?</h3>
              <ul className="text-purple-700 text-sm space-y-1">
                <li>• Full 30-day trial with ALL premium features</li>
                <li>• Contact details visible to potential clients</li>
                <li>• Start receiving client inquiries immediately</li>
                <li>• After trial: Continue for just $99/year</li>
              </ul>
            </div>

            {error && (
              <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg">{error}</div>
            )}

            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={loading || coachProfile.specialties.length === 0}
                className="flex-1 bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg font-medium disabled:opacity-50 transition-colors"
              >
                {loading ? 'Creating Profile...' : 'Launch My Coach Profile'}
              </button>
              <Link
                to="/"
                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 px-6 py-3 rounded-lg font-medium text-center transition-colors"
              >
                Skip for Now
              </Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/community" element={<CommunityLanding />} />
            <Route path="/get-started" element={<GetStartedFlow />} />
            <Route path="/login" element={<AuthSelectionPage />} />
            <Route path="/signin" element={<SignInPage />} />
            <Route path="/signup/member" element={<MemberSignUpPage />} />
            <Route path="/signup/coach" element={<CoachSignUpPage />} />
            <Route path="/onboarding/coach" element={<CoachOnboardingPage />} />
            <Route path="/coaches" element={<CoachesPage />} />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;