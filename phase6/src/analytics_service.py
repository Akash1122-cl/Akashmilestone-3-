"""
Phase 6 Advanced Analytics Service
Provides trend analysis, predictions, and insights generation
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class TrendData:
    """Trend analysis data structure"""
    product_id: str
    metric_type: str
    time_range: str
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str
    data_points: List[Dict[str, Any]]
    insights: List[str]

@dataclass
class PredictionData:
    """Prediction data structure"""
    product_id: str
    metric_type: str
    predicted_value: float
    confidence_score: float
    prediction_date: datetime
    methodology: str
    factors: List[str]

class AnalyticsService:
    """Advanced analytics service for Phase 6"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.prediction_models = {}
        self.trend_cache = {}
        
    async def generate_trend_analysis(self, product_id: str, time_range: str = "30_days", 
                                    metrics: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive trend analysis for a product"""
        try:
            if metrics is None:
                metrics = ["sentiment", "volume", "rating"]
            
            logger.info(f"Generating trend analysis for {product_id}")
            
            # Parse time range
            end_date = datetime.now()
            start_date = self._parse_time_range(time_range, end_date)
            
            # Generate analysis for each metric
            analyses = {}
            
            for metric in metrics:
                trend_data = await self._analyze_metric_trend(
                    product_id, metric, start_date, end_date
                )
                analyses[metric] = trend_data
            
            # Generate overall insights
            insights = self._generate_trend_insights(analyses)
            
            # Create summary
            summary = {
                "product_id": product_id,
                "time_range": time_range,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "analyses": analyses,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Trend analysis generated for {product_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating trend analysis for {product_id}: {e}")
            raise
    
    async def generate_predictions(self, product_id: str, metric_types: List[str] = None,
                                 prediction_days: int = 7) -> Dict[str, Any]:
        """Generate predictions for specified metrics"""
        try:
            if metric_types is None:
                metric_types = ["sentiment", "volume", "rating"]
            
            logger.info(f"Generating predictions for {product_id}")
            
            predictions = {}
            
            for metric in metric_types:
                prediction = await self._predict_metric(
                    product_id, metric, prediction_days
                )
                predictions[metric] = prediction
            
            # Generate prediction summary
            summary = {
                "product_id": product_id,
                "prediction_days": prediction_days,
                "predictions": predictions,
                "confidence_avg": self._calculate_avg_confidence(predictions),
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Predictions generated for {product_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating predictions for {product_id}: {e}")
            raise
    
    async def compare_products(self, product_ids: List[str], metrics: List[str] = None,
                              time_range: str = "30_days") -> Dict[str, Any]:
        """Compare multiple products across specified metrics"""
        try:
            if metrics is None:
                metrics = ["sentiment", "volume", "rating"]
            
            logger.info(f"Comparing products: {product_ids}")
            
            # Generate analysis for each product
            product_analyses = {}
            
            for product_id in product_ids:
                analysis = await self.generate_trend_analysis(product_id, time_range, metrics)
                product_analyses[product_id] = analysis
            
            # Generate comparison matrix
            comparison = self._generate_comparison_matrix(product_analyses, metrics)
            
            # Generate competitive insights
            insights = self._generate_competitive_insights(comparison)
            
            # Create summary
            summary = {
                "product_ids": product_ids,
                "time_range": time_range,
                "metrics": metrics,
                "comparison": comparison,
                "insights": insights,
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Product comparison completed for {len(product_ids)} products")
            return summary
            
        except Exception as e:
            logger.error(f"Error comparing products: {e}")
            raise
    
    async def _analyze_metric_trend(self, product_id: str, metric: str, 
                                  start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze trend for a specific metric"""
        try:
            # Generate historical data (mock implementation)
            data_points = self._generate_historical_data(product_id, metric, start_date, end_date)
            
            # Calculate trend metrics
            current_value = data_points[-1]["value"] if data_points else 0
            previous_value = data_points[0]["value"] if len(data_points) > 1 else current_value
            
            if previous_value != 0:
                change_percent = ((current_value - previous_value) / previous_value) * 100
            else:
                change_percent = 0
            
            # Determine trend direction
            if change_percent > 5:
                trend_direction = "increasing"
            elif change_percent < -5:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            # Generate insights
            insights = self._generate_metric_insights(metric, current_value, change_percent, trend_direction)
            
            return {
                "metric_type": metric,
                "current_value": current_value,
                "previous_value": previous_value,
                "change_percent": round(change_percent, 2),
                "trend_direction": trend_direction,
                "data_points": data_points,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {metric}: {e}")
            raise
    
    async def _predict_metric(self, product_id: str, metric: str, days: int) -> Dict[str, Any]:
        """Predict future values for a metric"""
        try:
            # Get historical data for prediction
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)  # Use 90 days for prediction
            
            data_points = self._generate_historical_data(product_id, metric, start_date, end_date)
            
            # Simple linear regression prediction (mock implementation)
            values = [point["value"] for point in data_points]
            
            if len(values) < 2:
                predicted_value = values[0] if values else 0
                confidence = 0.5
            else:
                # Simple trend-based prediction
                recent_trend = np.mean(values[-7:]) - np.mean(values[-14:-7]) if len(values) >= 14 else 0
                predicted_value = values[-1] + (recent_trend * days)
                
                # Calculate confidence based on data stability
                volatility = np.std(values[-30:]) / np.mean(values[-30:]) if len(values) >= 30 else 0.5
                confidence = max(0.3, min(0.95, 1.0 - volatility))
            
            prediction_date = end_date + timedelta(days=days)
            
            return {
                "metric_type": metric,
                "predicted_value": round(predicted_value, 2),
                "confidence_score": round(confidence, 2),
                "prediction_date": prediction_date.isoformat(),
                "methodology": "linear_regression",
                "factors": ["historical_trend", "seasonality", "volatility"]
            }
            
        except Exception as e:
            logger.error(f"Error predicting {metric}: {e}")
            raise
    
    def _generate_historical_data(self, product_id: str, metric: str, 
                                start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate mock historical data for analysis"""
        data_points = []
        current_date = start_date
        
        # Base values for different metrics
        base_values = {
            "sentiment": 0.75,
            "volume": 100,
            "rating": 4.2
        }
        
        base_value = base_values.get(metric, 1.0)
        
        while current_date <= end_date:
            # Add some randomness and trend
            days_from_start = (current_date - start_date).days
            trend_factor = 1.0 + (days_from_start * 0.001)  # Slight upward trend
            random_factor = 1.0 + (np.random.random() - 0.5) * 0.2  # ±10% randomness
            
            value = base_value * trend_factor * random_factor
            
            # Ensure values stay in reasonable ranges
            if metric == "sentiment":
                value = max(0.0, min(1.0, value))
            elif metric == "rating":
                value = max(1.0, min(5.0, value))
            elif metric == "volume":
                value = max(10, value)
            
            data_points.append({
                "date": current_date.isoformat(),
                "value": round(value, 2)
            })
            
            current_date += timedelta(days=1)
        
        return data_points
    
    def _generate_trend_insights(self, analyses: Dict[str, Any]) -> List[str]:
        """Generate insights from trend analyses"""
        insights = []
        
        for metric, analysis in analyses.items():
            change = analysis["change_percent"]
            direction = analysis["trend_direction"]
            
            if metric == "sentiment":
                if direction == "increasing":
                    insights.append(f"Customer sentiment is improving by {change:.1f}%")
                elif direction == "decreasing":
                    insights.append(f"Customer sentiment is declining by {abs(change):.1f}% - requires attention")
            
            elif metric == "volume":
                if direction == "increasing":
                    insights.append(f"Review volume is growing by {change:.1f}% - increasing engagement")
                elif direction == "decreasing":
                    insights.append(f"Review volume is decreasing by {abs(change):.1f}% - investigate cause")
            
            elif metric == "rating":
                if direction == "increasing":
                    insights.append(f"Product rating is improving by {change:.1f}%")
                elif direction == "decreasing":
                    insights.append(f"Product rating is declining by {abs(change):.1f}% - quality concerns")
        
        # Cross-metric insights
        sentiment_dir = analyses.get("sentiment", {}).get("trend_direction", "stable")
        volume_dir = analyses.get("volume", {}).get("trend_direction", "stable")
        
        if sentiment_dir == "increasing" and volume_dir == "increasing":
            insights.append("Positive trend: both sentiment and volume are increasing")
        elif sentiment_dir == "decreasing" and volume_dir == "increasing":
            insights.append("Warning: volume increasing but sentiment declining")
        
        return insights
    
    def _generate_metric_insights(self, metric: str, current: float, 
                                change: float, direction: str) -> List[str]:
        """Generate insights for a specific metric"""
        insights = []
        
        if metric == "sentiment":
            if current > 0.8:
                insights.append("Excellent sentiment score - customers very satisfied")
            elif current < 0.5:
                insights.append("Low sentiment score - requires immediate attention")
            
            if direction == "increasing":
                insights.append("Sentiment trending upward - recent improvements working")
            elif direction == "decreasing":
                insights.append("Sentiment trending downward - investigate recent changes")
        
        elif metric == "volume":
            if change > 20:
                insights.append("Significant increase in review volume")
            elif change < -20:
                insights.append("Significant decrease in review volume")
        
        elif metric == "rating":
            if current > 4.5:
                insights.append("Excellent rating - customers highly satisfied")
            elif current < 3.5:
                insights.append("Low rating - quality issues need addressing")
        
        return insights
    
    def _generate_comparison_matrix(self, analyses: Dict[str, Dict[str, Any]], 
                                  metrics: List[str]) -> Dict[str, Any]:
        """Generate comparison matrix for products"""
        comparison = {}
        
        for metric in metrics:
            comparison[metric] = {}
            
            for product_id, analysis in analyses.items():
                if metric in analysis["analyses"]:
                    metric_data = analysis["analyses"][metric]
                    comparison[metric][product_id] = {
                        "value": metric_data["current_value"],
                        "change": metric_data["change_percent"],
                        "direction": metric_data["trend_direction"]
                    }
        
        return comparison
    
    def _generate_competitive_insights(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate competitive insights from comparison"""
        insights = []
        
        for metric, product_data in comparison.items():
            if len(product_data) < 2:
                continue
            
            # Find best and worst performers
            values = {pid: data["value"] for pid, data in product_data.items()}
            
            if metric == "sentiment" or metric == "rating":
                best_product = max(values, key=values.get)
                worst_product = min(values, key=values.get)
                
                insights.append(f"{metric}: {best_product} leading with {values[best_product]:.2f}")
                insights.append(f"{metric}: {worst_product} trailing with {values[worst_product]:.2f}")
            
            elif metric == "volume":
                highest_product = max(values, key=values.get)
                insights.append(f"Review volume: {highest_product} has highest engagement ({values[highest_product]:.0f})")
        
        return insights
    
    def _calculate_avg_confidence(self, predictions: Dict[str, Any]) -> float:
        """Calculate average confidence score across predictions"""
        if not predictions:
            return 0.0
        
        confidences = [pred.get("confidence_score", 0.0) for pred in predictions.values()]
        return round(np.mean(confidences), 2)
    
    def _parse_time_range(self, time_range: str, end_date: datetime) -> datetime:
        """Parse time range string and return start date"""
        if time_range == "7_days":
            return end_date - timedelta(days=7)
        elif time_range == "30_days":
            return end_date - timedelta(days=30)
        elif time_range == "90_days":
            return end_date - timedelta(days=90)
        elif time_range == "1_year":
            return end_date - timedelta(days=365)
        else:
            # Default to 30 days
            return end_date - timedelta(days=30)

# Factory function
def create_analytics_service(config: Dict[str, Any]) -> AnalyticsService:
    """Create analytics service instance"""
    return AnalyticsService(config)
