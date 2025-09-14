import React, { useState } from 'react';
import { Bot, GitBranch, Search, Zap, CheckCircle, ArrowRight, Github, Code, Users, Sparkles } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';

interface LandingPageProps {
  onAnalyze: (url: string) => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onAnalyze }) => {
  const [githubUrl, setGithubUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = () => {
    if (githubUrl.trim()) {
      setIsAnalyzing(true);
      onAnalyze(githubUrl);
    }
  };

  const features = [
    {
      icon: <Bot className="w-6 h-6" />,
      title: "AI-Powered Analysis",
      description: "Multiple specialized AI agents analyze your codebase simultaneously for comprehensive insights."
    },
    {
      icon: <Search className="w-6 h-6" />,
      title: "Code Quality Review",
      description: "Get detailed code quality assessments with actionable recommendations for improvement."
    },
    {
      icon: <GitBranch className="w-6 h-6" />,
      title: "Architecture Analysis",
      description: "Understand your project structure, dependencies, and architectural patterns."
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Performance Insights",
      description: "Identify performance bottlenecks and get suggestions for optimization."
    }
  ];

  const agentTypes = [
    {
      name: "Research Agent",
      description: "Analyzes documentation, dependencies, and technology stack",
      color: "bg-blue-500"
    },
    {
      name: "Code Review Agent", 
      description: "Performs deep code quality analysis and security scanning",
      color: "bg-green-500"
    },
    {
      name: "QA Agent",
      description: "Evaluates testing coverage and suggests improvements", 
      color: "bg-purple-500"
    },
    {
      name: "Repository Analyzer",
      description: "Examines project structure and architectural patterns",
      color: "bg-orange-500"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              OpenSource Sensei
            </h1>
          </div>
          <nav className="hidden md:flex items-center space-x-6">
            <a href="#features" className="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">
              Features
            </a>
            <a href="#how-it-works" className="text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white">
              How it Works
            </a>
            <Button variant="outline">Get Started</Button>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="container mx-auto text-center">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-5xl md:text-6xl font-bold text-slate-900 dark:text-white mb-6">
              AI-Powered Open Source
              <span className="text-primary block">Project Analysis</span>
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 mb-10 max-w-2xl mx-auto">
              Transform your open source projects with comprehensive AI analysis. Get insights on code quality, 
              architecture, performance, and maintainability from our specialized agent team.
            </p>
            
            {/* GitHub URL Input */}
            <div className="max-w-2xl mx-auto mb-12">
              <Card className="p-6">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="flex-1">
                    <Input
                      type="url"
                      placeholder="https://github.com/username/repository"
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                      className="h-12 text-base"
                    />
                  </div>
                  <Button 
                    onClick={handleAnalyze}
                    disabled={!githubUrl.trim() || isAnalyzing}
                    className="h-12 px-8"
                    size="lg"
                  >
                    {isAnalyzing ? (
                      <>
                        <Bot className="w-5 h-5 mr-2 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <Search className="w-5 h-5 mr-2" />
                        Analyze Repository
                      </>
                    )}
                  </Button>
                </div>
                <p className="text-sm text-slate-500 mt-3 text-left">
                  Enter any public GitHub repository URL to get started with AI-powered analysis
                </p>
              </Card>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl mx-auto">
              <div className="text-center">
                <div className="text-3xl font-bold text-primary mb-2">4</div>
                <div className="text-slate-600 dark:text-slate-300">AI Agents</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-primary mb-2">100+</div>
                <div className="text-slate-600 dark:text-slate-300">Code Patterns</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-primary mb-2">24/7</div>
                <div className="text-slate-600 dark:text-slate-300">Analysis Ready</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 bg-white dark:bg-slate-800">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
              Comprehensive Analysis Features
            </h3>
            <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
              Our AI agents work together to provide deep insights into your codebase
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="p-6 hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <div className="text-primary">{feature.icon}</div>
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works - Agent Workflow */}
      <section id="how-it-works" className="py-20 px-4">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
              Meet Our AI Agent Team
            </h3>
            <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto">
              Each specialized agent brings unique expertise to analyze different aspects of your project
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {agentTypes.map((agent, index) => (
              <Card key={index} className="p-6 text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className={`w-16 h-16 ${agent.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                    <Bot className="w-8 h-8 text-white" />
                  </div>
                  <CardTitle className="text-lg">{agent.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>{agent.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Workflow Steps */}
          <div className="mt-16">
            <div className="flex flex-col md:flex-row items-center justify-center space-y-8 md:space-y-0 md:space-x-8">
              <div className="flex flex-col items-center text-center">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mb-4">
                  <Github className="w-6 h-6 text-white" />
                </div>
                <h4 className="font-semibold mb-2">1. Submit Repository</h4>
                <p className="text-sm text-slate-600 dark:text-slate-300">Enter your GitHub repository URL</p>
              </div>
              
              <ArrowRight className="w-6 h-6 text-slate-400 hidden md:block" />
              
              <div className="flex flex-col items-center text-center">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mb-4">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <h4 className="font-semibold mb-2">2. AI Analysis</h4>
                <p className="text-sm text-slate-600 dark:text-slate-300">Our agents analyze your codebase</p>
              </div>
              
              <ArrowRight className="w-6 h-6 text-slate-400 hidden md:block" />
              
              <div className="flex flex-col items-center text-center">
                <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mb-4">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <h4 className="font-semibold mb-2">3. Get Insights</h4>
                <p className="text-sm text-slate-600 dark:text-slate-300">Receive comprehensive analysis results</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-primary">
        <div className="container mx-auto text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to Improve Your Open Source Project?
          </h3>
          <p className="text-xl text-primary-foreground/80 mb-8 max-w-2xl mx-auto">
            Get started with AI-powered analysis and take your project to the next level
          </p>
          <Button size="lg" variant="secondary" className="text-lg px-8 py-3">
            <Github className="w-5 h-5 mr-2" />
            Analyze Your Repository
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 bg-slate-900 text-white">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <h4 className="text-xl font-bold">OpenSource Sensei</h4>
          </div>
          <p className="text-slate-400 mb-4">
            Empowering open source projects with AI-driven insights and analysis
          </p>
          <div className="flex justify-center space-x-6 text-sm text-slate-400">
            <span>© 2025 OpenSource Sensei</span>
            <span>•</span>
            <a href="#" className="hover:text-white">Privacy</a>
            <span>•</span>
            <a href="#" className="hover:text-white">Terms</a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;