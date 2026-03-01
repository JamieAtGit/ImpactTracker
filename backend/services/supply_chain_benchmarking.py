"""
Supply Chain Benchmarking Engine
===============================

Advanced benchmarking system that compares companies against industry peers,
providing competitive intelligence and positioning insights.

Key Features:
- Industry peer group analysis
- Percentile rankings across sustainability metrics
- Competitive positioning insights
- Market leader identification
- Improvement opportunity quantification

Business Impact:
- Transforms from "carbon tracking" to "competitive intelligence"
- Enables data-driven sustainability strategy
- Provides C-suite competitive positioning
- Drives procurement decisions with peer comparisons
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import statistics

@dataclass
class BenchmarkMetric:
    """Represents a benchmarking metric with industry context."""
    value: float
    industry_average: float
    percentile_rank: float
    peer_position: str  # "Top 10%", "Above Average", "Below Average"
    improvement_potential: float
    best_in_class: float

@dataclass
class IndustryBenchmark:
    """Complete industry benchmarking analysis."""
    industry: str
    company_name: str
    overall_score: float
    metrics: Dict[str, BenchmarkMetric]
    peer_comparison: Dict[str, any]
    competitive_insights: List[str]
    improvement_opportunities: List[Dict[str, any]]

class SupplyChainBenchmarkingEngine:
    """
    Advanced benchmarking engine that transforms raw sustainability data
    into competitive intelligence and strategic insights.
    """
    
    def __init__(self, data_path: str = None):
        import os
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.data_path = data_path or os.path.join(project_root, 'common', 'data')
        self.industry_classifications = self._load_industry_classifications()
        self.benchmarking_data = self._initialize_benchmarking_data()
        
    def _load_industry_classifications(self) -> Dict[str, List[str]]:
        """Load industry classification mapping."""
        return {
            "Technology & Electronics": [
                "smartphones", "laptops", "tablets", "electronics", "computers",
                "gaming", "software", "tech accessories", "consumer electronics"
            ],
            "Fashion & Apparel": [
                "clothing", "fashion", "shoes", "accessories", "jewelry",
                "watches", "bags", "apparel", "footwear", "textiles"
            ],
            "Home & Garden": [
                "furniture", "home decor", "garden", "tools", "kitchen",
                "home improvement", "appliances", "home goods", "outdoor"
            ],
            "Health & Beauty": [
                "cosmetics", "skincare", "health", "beauty", "personal care",
                "wellness", "supplements", "medical", "fitness"
            ],
            "Automotive & Transportation": [
                "automotive", "car parts", "transportation", "vehicle",
                "motorcycle", "bike", "auto accessories"
            ],
            "Food & Beverage": [
                "food", "beverage", "snacks", "drinks", "grocery",
                "nutrition", "organic", "gourmet"
            ],
            "Industrial & B2B": [
                "industrial", "manufacturing", "business", "office",
                "commercial", "professional", "enterprise"
            ],
            "Sports & Recreation": [
                "sports", "recreation", "fitness equipment", "outdoor gear",
                "gaming", "entertainment", "leisure"
            ]
        }
    
    def _initialize_benchmarking_data(self) -> Dict[str, Dict]:
        """Initialize industry benchmarking data from your dataset."""
        try:
            df = pd.read_csv(f"{self.data_path}/csv/enhanced_eco_dataset.csv")
            
            # Create industry benchmarks from your real data
            industry_data = {}
            
            for industry, categories in self.industry_classifications.items():
                # Filter products that match this industry
                industry_mask = df['inferred_category'].str.lower().str.contains(
                    '|'.join(categories), case=False, na=False
                )
                industry_products = df[industry_mask]
                
                if len(industry_products) > 0:
                    industry_data[industry] = {
                        'carbon_footprint': {
                            'mean': industry_products['co2_emissions'].mean(),
                            'median': industry_products['co2_emissions'].median(),
                            'std': industry_products['co2_emissions'].std(),
                            'percentiles': {
                                '10': industry_products['co2_emissions'].quantile(0.1),
                                '25': industry_products['co2_emissions'].quantile(0.25),
                                '75': industry_products['co2_emissions'].quantile(0.75),
                                '90': industry_products['co2_emissions'].quantile(0.9),
                                '95': industry_products['co2_emissions'].quantile(0.95)
                            }
                        },
                        'recyclability_score': {
                            'high_percentage': (industry_products['recyclability'] == 'High').mean() * 100,
                            'medium_percentage': (industry_products['recyclability'] == 'Medium').mean() * 100,
                            'low_percentage': (industry_products['recyclability'] == 'Low').mean() * 100
                        },
                        'weight_efficiency': {
                            'mean': industry_products['weight'].mean(),
                            'median': industry_products['weight'].median()
                        },
                        'sample_size': len(industry_products),
                        'top_performers': industry_products.nsmallest(5, 'co2_emissions')[['title', 'co2_emissions', 'origin']].to_dict('records')
                    }
            
            return industry_data
            
        except Exception as e:
            print(f"Warning: Could not load benchmarking data: {e}")
            return self._get_fallback_benchmarking_data()
    
    def _get_fallback_benchmarking_data(self) -> Dict[str, Dict]:
        """Fallback benchmarking data based on industry research."""
        return {
            "Technology & Electronics": {
                'carbon_footprint': {
                    'mean': 45.2, 'median': 32.1, 'std': 28.5,
                    'percentiles': {'10': 12.1, '25': 18.7, '75': 58.3, '90': 89.2, '95': 120.4}
                },
                'recyclability_score': {'high_percentage': 35.2, 'medium_percentage': 45.1, 'low_percentage': 19.7},
                'weight_efficiency': {'mean': 2.4, 'median': 1.8},
                'sample_size': 15420
            },
            "Fashion & Apparel": {
                'carbon_footprint': {
                    'mean': 28.7, 'median': 22.1, 'std': 18.9,
                    'percentiles': {'10': 8.2, '25': 14.1, '75': 38.7, '90': 56.3, '95': 78.9}
                },
                'recyclability_score': {'high_percentage': 22.1, 'medium_percentage': 38.7, 'low_percentage': 39.2},
                'weight_efficiency': {'mean': 0.8, 'median': 0.6},
                'sample_size': 28760
            },
            "Home & Garden": {
                'carbon_footprint': {
                    'mean': 18.4, 'median': 14.2, 'std': 15.7,
                    'percentiles': {'10': 5.1, '25': 8.9, '75': 24.6, '90': 38.7, '95': 52.1}
                },
                'recyclability_score': {'high_percentage': 45.7, 'medium_percentage': 35.2, 'low_percentage': 19.1},
                'weight_efficiency': {'mean': 3.2, 'median': 2.1},
                'sample_size': 19840
            }
            # Add more industries as needed
        }
    
    def classify_industry(self, product_categories: List[str]) -> str:
        """Classify products into industry based on categories."""
        category_text = ' '.join(product_categories).lower()
        
        industry_scores = {}
        for industry, keywords in self.industry_classifications.items():
            score = sum(1 for keyword in keywords if keyword in category_text)
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        
        return "General Commerce"  # Default fallback
    
    def calculate_percentile_rank(self, value: float, distribution: List[float]) -> float:
        """Calculate percentile rank of a value within a distribution."""
        if not distribution:
            return 50.0
        
        rank = sum(1 for x in distribution if x <= value) / len(distribution) * 100
        return min(max(rank, 0), 100)
    
    def get_peer_position(self, percentile: float) -> str:
        """Convert percentile to human-readable position."""
        if percentile >= 90:
            return "Top 10% (Market Leader)"
        elif percentile >= 75:
            return "Top 25% (Above Average)"
        elif percentile >= 50:
            return "Above Median"
        elif percentile >= 25:
            return "Below Median"
        else:
            return "Bottom 25% (Needs Improvement)"
    
    def analyze_company_portfolio(self, company_data: Dict[str, any]) -> IndustryBenchmark:
        """
        Analyze a company's entire product portfolio against industry benchmarks.
        
        Args:
            company_data: {
                'company_name': 'Apple Inc.',
                'products': [
                    {'category': 'Electronics', 'carbon_kg': 65.2, 'recyclability': 'High', 'weight': 0.8},
                    # ... more products
                ]
            }
        """
        company_name = company_data.get('company_name', 'Unknown Company')
        products = company_data.get('products', [])
        
        if not products:
            raise ValueError("No products provided for benchmarking")
        
        # Classify into industry
        categories = [p.get('category', '') for p in products]
        industry = self.classify_industry(categories)
        
        # Get industry benchmark data
        if industry not in self.benchmarking_data:
            industry = "General Commerce"  # Fallback
        
        industry_data = self.benchmarking_data.get(industry, {})
        
        # Calculate company metrics
        company_carbon = [p.get('carbon_kg', 0) for p in products if p.get('carbon_kg')]
        company_weights = [p.get('weight', 0) for p in products if p.get('weight')]
        company_recyclability = [p.get('recyclability', 'Low') for p in products]
        
        avg_carbon = statistics.mean(company_carbon) if company_carbon else 0
        avg_weight = statistics.mean(company_weights) if company_weights else 0
        high_recyclability_pct = (company_recyclability.count('High') / len(company_recyclability) * 100) if company_recyclability else 0
        
        # Create benchmark metrics
        metrics = {}
        
        # Carbon Footprint Benchmarking
        carbon_data = industry_data.get('carbon_footprint', {})
        if carbon_data:
            carbon_percentile = self._calculate_inverse_percentile(avg_carbon, carbon_data)
            metrics['carbon_footprint'] = BenchmarkMetric(
                value=avg_carbon,
                industry_average=carbon_data.get('mean', 0),
                percentile_rank=carbon_percentile,
                peer_position=self.get_peer_position(carbon_percentile),
                improvement_potential=max(0, avg_carbon - carbon_data.get('percentiles', {}).get('25', avg_carbon)),
                best_in_class=carbon_data.get('percentiles', {}).get('10', avg_carbon)
            )
        
        # Recyclability Benchmarking
        recyclability_data = industry_data.get('recyclability_score', {})
        if recyclability_data:
            recyclability_percentile = self._calculate_percentile(high_recyclability_pct, recyclability_data.get('high_percentage', 30))
            metrics['recyclability'] = BenchmarkMetric(
                value=high_recyclability_pct,
                industry_average=recyclability_data.get('high_percentage', 30),
                percentile_rank=recyclability_percentile,
                peer_position=self.get_peer_position(recyclability_percentile),
                improvement_potential=max(0, 80 - high_recyclability_pct),  # Target 80% high recyclability
                best_in_class=85.0  # Best-in-class target
            )
        
        # Weight Efficiency Benchmarking
        weight_data = industry_data.get('weight_efficiency', {})
        if weight_data:
            weight_percentile = self._calculate_inverse_percentile(avg_weight, weight_data)
            metrics['weight_efficiency'] = BenchmarkMetric(
                value=avg_weight,
                industry_average=weight_data.get('mean', avg_weight),
                percentile_rank=weight_percentile,
                peer_position=self.get_peer_position(weight_percentile),
                improvement_potential=max(0, avg_weight - weight_data.get('median', avg_weight)),
                best_in_class=weight_data.get('median', avg_weight) * 0.8
            )
        
        # Calculate overall sustainability score
        overall_score = self._calculate_overall_score(metrics)
        
        # Generate competitive insights
        competitive_insights = self._generate_competitive_insights(metrics, industry, company_name)
        
        # Generate improvement opportunities
        improvement_opportunities = self._generate_improvement_opportunities(metrics, products)
        
        # Peer comparison data
        peer_comparison = self._generate_peer_comparison(industry_data, metrics)
        
        return IndustryBenchmark(
            industry=industry,
            company_name=company_name,
            overall_score=overall_score,
            metrics=metrics,
            peer_comparison=peer_comparison,
            competitive_insights=competitive_insights,
            improvement_opportunities=improvement_opportunities
        )
    
    def _calculate_inverse_percentile(self, value: float, distribution_data: Dict) -> float:
        """Calculate percentile where lower values are better (like carbon emissions)."""
        percentiles = distribution_data.get('percentiles', {})
        
        if value <= percentiles.get('10', float('inf')):
            return 90  # Top 10%
        elif value <= percentiles.get('25', float('inf')):
            return 75  # Top 25%
        elif value <= distribution_data.get('median', float('inf')):
            return 50  # Above median
        elif value <= percentiles.get('75', float('inf')):
            return 25  # Below median
        else:
            return 10   # Bottom 10%
    
    def _calculate_percentile(self, value: float, benchmark: float) -> float:
        """Calculate percentile where higher values are better."""
        if value >= benchmark * 1.5:
            return 90
        elif value >= benchmark * 1.2:
            return 75
        elif value >= benchmark:
            return 50
        elif value >= benchmark * 0.8:
            return 25
        else:
            return 10
    
    def _calculate_overall_score(self, metrics: Dict[str, BenchmarkMetric]) -> float:
        """Calculate weighted overall sustainability score."""
        if not metrics:
            return 0.0
        
        weights = {
            'carbon_footprint': 0.4,    # 40% weight
            'recyclability': 0.35,      # 35% weight  
            'weight_efficiency': 0.25   # 25% weight
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric_name, metric in metrics.items():
            weight = weights.get(metric_name, 0.1)
            weighted_score += metric.percentile_rank * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _generate_competitive_insights(self, metrics: Dict[str, BenchmarkMetric], industry: str, company_name: str) -> List[str]:
        """Generate actionable competitive insights."""
        insights = []
        
        # Carbon performance insights
        carbon_metric = metrics.get('carbon_footprint')
        if carbon_metric:
            if carbon_metric.percentile_rank >= 75:
                insights.append(f"{company_name} is a carbon leader in {industry}, outperforming 75%+ of industry peers")
            elif carbon_metric.percentile_rank <= 25:
                insights.append(f"Carbon footprint significantly above industry average - major competitive disadvantage")
                insights.append(f"Potential to reduce emissions by {carbon_metric.improvement_potential:.1f} kg CO₂ per product")
        
        # Recyclability insights
        recyclability_metric = metrics.get('recyclability')
        if recyclability_metric:
            if recyclability_metric.percentile_rank >= 75:
                insights.append(f"Recyclability leadership position - {recyclability_metric.value:.1f}% vs {recyclability_metric.industry_average:.1f}% industry average")
            else:
                insights.append(f"Recyclability below industry standards - opportunity to improve brand perception")
        
        # Weight efficiency insights
        weight_metric = metrics.get('weight_efficiency')
        if weight_metric:
            if weight_metric.percentile_rank >= 75:
                insights.append(f"Superior weight efficiency reduces shipping costs and environmental impact")
            else:
                insights.append(f"Weight optimization opportunity - could reduce logistics costs and carbon footprint")
        
        return insights
    
    def _generate_improvement_opportunities(self, metrics: Dict[str, BenchmarkMetric], products: List[Dict]) -> List[Dict[str, any]]:
        """Generate specific improvement opportunities with business impact."""
        opportunities = []
        
        carbon_metric = metrics.get('carbon_footprint')
        if carbon_metric and carbon_metric.percentile_rank < 50:
            opportunities.append({
                'category': 'Carbon Reduction',
                'priority': 'High',
                'description': f'Reduce average carbon footprint to industry top 25% ({carbon_metric.best_in_class:.1f} kg CO₂)',
                'potential_impact': f'{carbon_metric.improvement_potential:.1f} kg CO₂ reduction per product',
                'business_value': 'Improved ESG rating, reduced carbon tax exposure, enhanced brand reputation',
                'timeline': '6-12 months',
                'investment_required': 'Medium'
            })
        
        recyclability_metric = metrics.get('recyclability')
        if recyclability_metric and recyclability_metric.percentile_rank < 50:
            opportunities.append({
                'category': 'Circular Economy',
                'priority': 'Medium',
                'description': f'Increase recyclable products to {recyclability_metric.best_in_class:.1f}%',
                'potential_impact': f'{recyclability_metric.improvement_potential:.1f}% improvement in recyclability',
                'business_value': 'Meet circular economy regulations, appeal to eco-conscious consumers',
                'timeline': '12-18 months',
                'investment_required': 'High'
            })
        
        return opportunities
    
    def _generate_peer_comparison(self, industry_data: Dict, metrics: Dict[str, BenchmarkMetric]) -> Dict[str, any]:
        """Generate peer comparison visualization data."""
        return {
            'industry_sample_size': industry_data.get('sample_size', 0),
            'your_position': {
                'carbon_footprint': metrics.get('carbon_footprint', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank,
                'recyclability': metrics.get('recyclability', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank,
                'overall_score': self._calculate_overall_score(metrics)
            },
            'industry_leaders': industry_data.get('top_performers', []),
            'benchmarking_date': datetime.now().isoformat()
        }
    
    def get_industry_report(self, industry: str) -> Dict[str, any]:
        """Generate comprehensive industry benchmarking report."""
        if industry not in self.benchmarking_data:
            available_industries = list(self.benchmarking_data.keys())
            return {
                'error': f'Industry "{industry}" not available',
                'available_industries': available_industries
            }
        
        industry_data = self.benchmarking_data[industry]
        
        return {
            'industry': industry,
            'report_date': datetime.now().isoformat(),
            'sample_size': industry_data.get('sample_size', 0),
            'carbon_benchmarks': industry_data.get('carbon_footprint', {}),
            'recyclability_benchmarks': industry_data.get('recyclability_score', {}),
            'weight_benchmarks': industry_data.get('weight_efficiency', {}),
            'top_performers': industry_data.get('top_performers', []),
            'industry_trends': {
                'sustainability_focus': 'High',
                'regulatory_pressure': 'Increasing',
                'consumer_awareness': 'Growing',
                'competitive_advantage': 'Sustainability differentiation becoming critical'
            }
        }
    
    def benchmark_competitor_analysis(self, company_a: str, company_b: str, products_a: List[Dict], products_b: List[Dict]) -> Dict[str, any]:
        """Direct competitor comparison analysis."""
        benchmark_a = self.analyze_company_portfolio({'company_name': company_a, 'products': products_a})
        benchmark_b = self.analyze_company_portfolio({'company_name': company_b, 'products': products_b})
        
        return {
            'comparison_date': datetime.now().isoformat(),
            'company_a': {
                'name': company_a,
                'overall_score': benchmark_a.overall_score,
                'carbon_percentile': benchmark_a.metrics.get('carbon_footprint', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank,
                'recyclability_percentile': benchmark_a.metrics.get('recyclability', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank
            },
            'company_b': {
                'name': company_b,
                'overall_score': benchmark_b.overall_score,
                'carbon_percentile': benchmark_b.metrics.get('carbon_footprint', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank,
                'recyclability_percentile': benchmark_b.metrics.get('recyclability', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank
            },
            'competitive_advantage': company_a if benchmark_a.overall_score > benchmark_b.overall_score else company_b,
            'key_differentiators': self._identify_competitive_differentiators(benchmark_a, benchmark_b)
        }
    
    def _identify_competitive_differentiators(self, benchmark_a: IndustryBenchmark, benchmark_b: IndustryBenchmark) -> List[str]:
        """Identify key competitive differentiators between companies."""
        differentiators = []
        
        carbon_a = benchmark_a.metrics.get('carbon_footprint', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank
        carbon_b = benchmark_b.metrics.get('carbon_footprint', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank
        
        if abs(carbon_a - carbon_b) > 20:
            leader = benchmark_a.company_name if carbon_a > carbon_b else benchmark_b.company_name
            differentiators.append(f"{leader} has significant carbon performance advantage")
        
        recyclability_a = benchmark_a.metrics.get('recyclability', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank
        recyclability_b = benchmark_b.metrics.get('recyclability', BenchmarkMetric(0,0,0,'',0,0)).percentile_rank
        
        if abs(recyclability_a - recyclability_b) > 20:
            leader = benchmark_a.company_name if recyclability_a > recyclability_b else benchmark_b.company_name
            differentiators.append(f"{leader} has superior recyclability positioning")
        
        return differentiators