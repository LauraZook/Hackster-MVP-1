import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Hero Section Component
const HeroSection = () => {
  return (
    <div className="bg-gradient-to-br from-emerald-50 via-blue-50 to-purple-50 min-h-screen">
      {/* Navigation */}
      <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">H</span>
          </div>
          <span className="text-2xl font-bold text-gray-900">Hackster</span>
        </div>
        <div className="hidden md:flex items-center space-x-8">
          <a href="#baseline" className="text-gray-700 hover:text-emerald-600 transition-colors">Baseline</a>
          <a href="#stack" className="text-gray-700 hover:text-emerald-600 transition-colors">Stack</a>
          <a href="#coaching" className="text-gray-700 hover:text-emerald-600 transition-colors">Coaching</a>
          <a href="#community" className="text-gray-700 hover:text-emerald-600 transition-colors">Community</a>
          <button className="bg-emerald-600 text-white px-6 py-2 rounded-lg hover:bg-emerald-700 transition-colors">
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Content */}
      <div className="max-w-7xl mx-auto px-6 pt-20 pb-32">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight">
            Optimize Your Health with
            <span className="text-emerald-600 block">Biohacking Excellence</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-12 leading-relaxed">
            Establish your baseline, build your personalized Hackster stack, and optimize 
            with world-class coaching for a healthier + happier you.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="bg-emerald-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-emerald-700 transition-all shadow-lg hover:shadow-xl">
              Start Your Health Journey
            </button>
            <button className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl text-lg font-semibold hover:border-emerald-600 hover:text-emerald-600 transition-all">
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
      color: "emerald"
    },
    {
      id: "stack",
      title: "2. Build Your Hackster Stack",
      subtitle: "Personalized Product Recommendations",
      description: "Answer our smart questionnaire to get personalized biohacking recommendations tailored to your unique health goals and needs.",
      icon: "⚡",
      highlights: [
        "Thorne & Apex Energetics supplements",
        "Oura Ring & health devices",
        "Free biohacking protocols",
        "Age & goal-specific stacks"
      ],
      cta: "Build My Stack",
      color: "blue"
    },
    {
      id: "coaching",
      title: "3. Optimize with Coaching",
      subtitle: "AI Coach + Human Experts",
      description: "Get personalized guidance from our F.R.E.E.D.O.M method AI coach and connect with certified human coaches for advanced optimization.",
      icon: "🚀",
      highlights: [],
      cta: "Start Coaching",
      color: "purple"
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
          {features.map((feature, index) => (
            <div key={feature.id} className="group hover:scale-105 transition-all duration-300">
              <div className={`bg-gradient-to-br from-${feature.color}-50 to-${feature.color}-100 rounded-2xl p-8 h-full border border-${feature.color}-200 shadow-lg hover:shadow-xl transition-all`}>
                <div className="text-center mb-6">
                  <div className="text-4xl mb-4">{feature.icon}</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                  <p className={`text-${feature.color}-600 font-semibold mb-4`}>{feature.subtitle}</p>
                  <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                </div>

                {feature.highlights.length > 0 && (
                  <div className="space-y-3 mb-8">
                    {feature.highlights.map((highlight, idx) => (
                      <div key={idx} className="flex items-center space-x-3">
                        <div className={`w-2 h-2 bg-${feature.color}-500 rounded-full`}></div>
                        <span className="text-gray-700">{highlight}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className={feature.highlights.length === 0 ? "mt-8" : ""}>
                  <button className={`w-full bg-${feature.color}-600 text-white py-3 rounded-xl font-semibold hover:bg-${feature.color}-700 transition-colors shadow-md hover:shadow-lg`}>
                    {feature.cta}
                  </button>
                </div>
              </div>
            </div>
          ))}
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
                  <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                    <span className="text-emerald-600 font-bold text-sm">#{supplement.priority}</span>
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">{supplement.name}</h3>
                </div>
              </div>
              <p className="text-gray-600 mb-4">{supplement.description}</p>
              <div className="flex flex-wrap gap-2">
                {supplement.brands.map((brand) => (
                  <span key={brand} className="bg-emerald-100 text-emerald-700 px-3 py-1 rounded-full text-sm font-medium">
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

// Community and Coaching Section
const CommunityCoaching = () => {
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
                <div className="text-3xl font-bold text-emerald-600 mb-2">1,000+</div>
                <div className="text-gray-600">Active Members</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-2">50+</div>
                <div className="text-gray-600">Certified Coaches</div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4">
              <button className="bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors">
                Join Community
              </button>
              <button className="border-2 border-purple-600 text-purple-600 px-6 py-3 rounded-xl font-semibold hover:bg-purple-600 hover:text-white transition-all">
                Find a Coach
              </button>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-3">F.R.E.E.D.O.M Method AI Coach</h3>
              <p className="text-gray-600 mb-4">Get 24/7 personalized biohacking guidance powered by our proprietary F.R.E.E.D.O.M methodology.</p>
              <button className="text-emerald-600 font-semibold hover:text-emerald-700">Try AI Coach →</button>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Coach Directory</h3>
              <p className="text-gray-600 mb-4">Connect with certified nutritionists, fitness coaches, and wellness experts in your area.</p>
              <button className="text-blue-600 font-semibold hover:text-blue-700">Browse Coaches →</button>
            </div>

            <div className="bg-white rounded-xl p-6 shadow-lg">
              <h3 className="text-lg font-bold text-gray-900 mb-3">Community Forum</h3>
              <p className="text-gray-600 mb-4">Share your results, get support, and learn from thousands of fellow biohackers.</p>
              <button className="text-purple-600 font-semibold hover:text-purple-700">Join Discussion →</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

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
            <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
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