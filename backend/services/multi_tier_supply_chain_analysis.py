#!/usr/bin/env python3
"""
Multi-Tier Supply Chain Analysis System
Advanced modeling of complex supply chain flows with carbon impact tracking

This system models the complete supply chain journey:
Raw Materials → Components → Sub-Assembly → Final Assembly → Distribution → Customer

Features:
- Multi-tier manufacturing flow tracking
- Supplier network carbon mapping
- Transportation mode optimization
- Just-in-time vs inventory impact analysis
- Supply chain resilience vs carbon trade-offs
"""

import json
import math
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import random

class SupplyTier(Enum):
    RAW_MATERIALS = "raw_materials"          # Tier 3+ suppliers
    COMPONENTS = "components"                # Tier 2 suppliers  
    SUB_ASSEMBLY = "sub_assembly"           # Tier 1 suppliers
    FINAL_ASSEMBLY = "final_assembly"       # OEM/Brand manufacturer
    DISTRIBUTION = "distribution"            # Fulfillment centers
    RETAIL = "retail"                       # Customer delivery

class ManufacturingStrategy(Enum):
    JUST_IN_TIME = "just_in_time"           # Lean, frequent deliveries
    INVENTORY_BUFFER = "inventory_buffer"    # Safety stock, batch deliveries
    HYBRID = "hybrid"                       # Mix of strategies
    DISTRIBUTED = "distributed"             # Regional manufacturing

@dataclass
class SupplyChainNode:
    """Individual node in the supply chain network"""
    id: str
    name: str
    tier: SupplyTier
    location: str
    coordinates: Tuple[float, float]
    specialization: List[str]
    capacity_units_per_day: int
    energy_source: str
    carbon_intensity_kg_per_unit: float
    supplier_network: List[str]  # Upstream suppliers
    lead_time_days: int
    minimum_order_quantity: int

@dataclass
class MaterialFlow:
    """Material flow between supply chain nodes"""
    from_node: str
    to_node: str
    material_type: str
    quantity_per_product: float
    transport_distance_km: float
    transport_mode: str
    transport_frequency_days: int
    packaging_type: str
    carbon_per_kg_km: float

class MultiTierSupplyChainAnalysis:
    """
    Advanced multi-tier supply chain modeling for accurate carbon tracking
    """
    
    def __init__(self):
        print("🏭 Initializing Multi-Tier Supply Chain Analysis...")
        print("⛓️ Building complex supply network models...")
        
        # Carbon intensities by transport mode (gCO2/tonne-km)
        self.transport_carbon_intensity = {
            "air_freight": 1054,
            "sea_freight": 19,
            "rail_freight": 60,
            "truck_diesel": 225,
            "truck_electric": 75,
            "pipeline": 10,
            "courier": 350
        }
        
        # Manufacturing energy intensities by process type (kWh/unit)
        self.manufacturing_energy_intensity = {
            "raw_material_extraction": 15.0,
            "metal_smelting": 45.0,
            "chemical_processing": 25.0,
            "precision_machining": 8.0,
            "electronics_assembly": 3.5,
            "injection_molding": 2.8,
            "packaging": 0.5
        }
        
        # Load supply chain networks
        self.supply_networks = self._build_supply_networks()
        self.material_flows = self._build_material_flows()
        
        print(f"✅ Built {len(self.supply_networks)} supply chain networks")
        print(f"🚛 Mapped {len(self.material_flows)} material flows")
        print("⚡ Multi-tier analysis system ready!")
    
    def _build_supply_networks(self) -> Dict[str, List[SupplyChainNode]]:
        """Build detailed supply chain networks for different product categories"""
        
        networks = {}
        
        # Smartphone Supply Chain Network
        smartphone_network = [
            # Tier 3: Raw Materials
            SupplyChainNode(
                id="rare_earth_china", name="Inner Mongolia Rare Earth", 
                tier=SupplyTier.RAW_MATERIALS, location="Baotou, China",
                coordinates=(40.6562, 109.8403), specialization=["neodymium", "lithium", "cobalt"],
                capacity_units_per_day=50000, energy_source="coal_grid",
                carbon_intensity_kg_per_unit=2.8, supplier_network=[],
                lead_time_days=45, minimum_order_quantity=10000
            ),
            SupplyChainNode(
                id="aluminum_smelter_china", name="Chalco Aluminum Smelter",
                tier=SupplyTier.RAW_MATERIALS, location="Qingdao, China", 
                coordinates=(36.0986, 120.3719), specialization=["aluminum_ingots", "aluminum_alloys"],
                capacity_units_per_day=200000, energy_source="coal_grid",
                carbon_intensity_kg_per_unit=8.2, supplier_network=[],
                lead_time_days=21, minimum_order_quantity=50000
            ),
            
            # Tier 2: Components  
            SupplyChainNode(
                id="processor_taiwan", name="TSMC Semiconductor Fab",
                tier=SupplyTier.COMPONENTS, location="Hsinchu, Taiwan",
                coordinates=(24.8138, 120.9675), specialization=["processors", "memory_chips", "sensors"],
                capacity_units_per_day=100000, energy_source="mixed_grid",
                carbon_intensity_kg_per_unit=12.5, supplier_network=["rare_earth_china"],
                lead_time_days=90, minimum_order_quantity=25000
            ),
            SupplyChainNode(
                id="display_samsung", name="Samsung Display Facility",
                tier=SupplyTier.COMPONENTS, location="Cheonan, South Korea",
                coordinates=(36.8151, 127.1139), specialization=["oled_displays", "touch_sensors", "glass"],
                capacity_units_per_day=75000, energy_source="mixed_grid",
                carbon_intensity_kg_per_unit=4.2, supplier_network=["aluminum_smelter_china"],
                lead_time_days=30, minimum_order_quantity=15000
            ),
            
            # Tier 1: Sub-Assembly
            SupplyChainNode(
                id="pcb_assembly_china", name="Foxconn PCB Assembly",
                tier=SupplyTier.SUB_ASSEMBLY, location="Shenzhen, China",
                coordinates=(22.5431, 114.0579), specialization=["pcb_assembly", "component_integration"],
                capacity_units_per_day=500000, energy_source="renewable_mixed",
                carbon_intensity_kg_per_unit=1.8, supplier_network=["processor_taiwan", "display_samsung"],
                lead_time_days=14, minimum_order_quantity=50000
            ),
            
            # Final Assembly
            SupplyChainNode(
                id="final_assembly_china", name="iPhone Final Assembly",
                tier=SupplyTier.FINAL_ASSEMBLY, location="Zhengzhou, China",
                coordinates=(34.7466, 113.6253), specialization=["final_assembly", "testing", "packaging"],
                capacity_units_per_day=800000, energy_source="renewable_matched",
                carbon_intensity_kg_per_unit=0.6, supplier_network=["pcb_assembly_china"],
                lead_time_days=7, minimum_order_quantity=100000
            )
        ]
        
        networks["smartphone"] = smartphone_network
        
        # Kitchen Appliance Supply Chain Network  
        appliance_network = [
            # Raw Materials
            SupplyChainNode(
                id="steel_mill_germany", name="ThyssenKrupp Steel",
                tier=SupplyTier.RAW_MATERIALS, location="Duisburg, Germany",
                coordinates=(51.4344, 6.7623), specialization=["stainless_steel", "carbon_steel"],
                capacity_units_per_day=80000, energy_source="renewable_partial",
                carbon_intensity_kg_per_unit=1.9, supplier_network=[],
                lead_time_days=28, minimum_order_quantity=20000
            ),
            
            # Components
            SupplyChainNode(
                id="motor_assembly_china", name="Midea Motor Manufacturing",
                tier=SupplyTier.COMPONENTS, location="Foshan, China", 
                coordinates=(23.0218, 113.1064), specialization=["electric_motors", "compressors"],
                capacity_units_per_day=45000, energy_source="grid_standard",
                carbon_intensity_kg_per_unit=3.2, supplier_network=["steel_mill_germany"],
                lead_time_days=35, minimum_order_quantity=5000
            ),
            
            # Final Assembly
            SupplyChainNode(
                id="appliance_assembly_turkey", name="Arçelik Manufacturing",
                tier=SupplyTier.FINAL_ASSEMBLY, location="Istanbul, Turkey",
                coordinates=(41.0082, 28.9784), specialization=["appliance_assembly", "quality_testing"],
                capacity_units_per_day=25000, energy_source="renewable_partial",
                carbon_intensity_kg_per_unit=2.1, supplier_network=["motor_assembly_china"],
                lead_time_days=14, minimum_order_quantity=1000
            )
        ]
        
        networks["kitchen_appliance"] = appliance_network
        
        # Fashion/Textile Supply Chain Network
        fashion_network = [
            # Raw Materials
            SupplyChainNode(
                id="cotton_farm_india", name="Organic Cotton Cooperative",
                tier=SupplyTier.RAW_MATERIALS, location="Gujarat, India",
                coordinates=(23.0225, 72.5714), specialization=["organic_cotton", "conventional_cotton"],
                capacity_units_per_day=15000, energy_source="solar_partial",
                carbon_intensity_kg_per_unit=2.1, supplier_network=[],
                lead_time_days=120, minimum_order_quantity=5000
            ),
            
            # Components  
            SupplyChainNode(
                id="textile_mill_bangladesh", name="Square Textiles Mill",
                tier=SupplyTier.COMPONENTS, location="Dhaka, Bangladesh",
                coordinates=(23.8103, 90.4125), specialization=["fabric_weaving", "dyeing", "finishing"],
                capacity_units_per_day=100000, energy_source="grid_standard",
                carbon_intensity_kg_per_unit=1.8, supplier_network=["cotton_farm_india"],
                lead_time_days=45, minimum_order_quantity=10000
            ),
            
            # Final Assembly
            SupplyChainNode(
                id="garment_factory_vietnam", name="Hansae Garment Factory",
                tier=SupplyTier.FINAL_ASSEMBLY, location="Ho Chi Minh City, Vietnam",
                coordinates=(10.8231, 106.6297), specialization=["cutting", "sewing", "quality_control"],
                capacity_units_per_day=50000, energy_source="renewable_partial",
                carbon_intensity_kg_per_unit=0.4, supplier_network=["textile_mill_bangladesh"],
                lead_time_days=21, minimum_order_quantity=2000
            )
        ]
        
        networks["fashion"] = fashion_network
        
        return networks
    
    def _build_material_flows(self) -> Dict[str, List[MaterialFlow]]:
        """Build material flow networks between supply chain nodes"""
        
        flows = {}
        
        # Smartphone material flows
        smartphone_flows = [
            # Raw materials to components
            MaterialFlow(
                from_node="rare_earth_china", to_node="processor_taiwan",
                material_type="rare_earth_elements", quantity_per_product=0.0034,
                transport_distance_km=1850, transport_mode="air_freight",
                transport_frequency_days=7, packaging_type="specialized_containers",
                carbon_per_kg_km=1.054
            ),
            MaterialFlow(
                from_node="aluminum_smelter_china", to_node="display_samsung", 
                material_type="aluminum_sheets", quantity_per_product=0.045,
                transport_distance_km=945, transport_mode="sea_freight",
                transport_frequency_days=14, packaging_type="palletized",
                carbon_per_kg_km=0.019
            ),
            
            # Components to sub-assembly
            MaterialFlow(
                from_node="processor_taiwan", to_node="pcb_assembly_china",
                material_type="semiconductor_chips", quantity_per_product=0.012,
                transport_distance_km=730, transport_mode="air_freight",
                transport_frequency_days=3, packaging_type="anti_static_trays",
                carbon_per_kg_km=1.054
            ),
            MaterialFlow(
                from_node="display_samsung", to_node="pcb_assembly_china",
                material_type="display_modules", quantity_per_product=0.089,
                transport_distance_km=2050, transport_mode="air_freight",
                transport_frequency_days=7, packaging_type="foam_protection",
                carbon_per_kg_km=1.054
            ),
            
            # Sub-assembly to final assembly
            MaterialFlow(
                from_node="pcb_assembly_china", to_node="final_assembly_china",
                material_type="assembled_pcb", quantity_per_product=0.156,
                transport_distance_km=1200, transport_mode="truck_electric",
                transport_frequency_days=2, packaging_type="standardized_boxes",
                carbon_per_kg_km=0.075
            )
        ]
        
        flows["smartphone"] = smartphone_flows
        
        # Kitchen appliance flows
        appliance_flows = [
            MaterialFlow(
                from_node="steel_mill_germany", to_node="motor_assembly_china",
                material_type="stainless_steel_sheets", quantity_per_product=12.5,
                transport_distance_km=8200, transport_mode="sea_freight",
                transport_frequency_days=28, packaging_type="steel_coils",
                carbon_per_kg_km=0.019
            ),
            MaterialFlow(
                from_node="motor_assembly_china", to_node="appliance_assembly_turkey",
                material_type="electric_motors", quantity_per_product=2.8,
                transport_distance_km=7100, transport_mode="rail_freight",
                transport_frequency_days=21, packaging_type="crated",
                carbon_per_kg_km=0.060
            )
        ]
        
        flows["kitchen_appliance"] = appliance_flows
        
        # Fashion flows
        fashion_flows = [
            MaterialFlow(
                from_node="cotton_farm_india", to_node="textile_mill_bangladesh",
                material_type="raw_cotton_bales", quantity_per_product=0.8,
                transport_distance_km=1650, transport_mode="truck_diesel",
                transport_frequency_days=30, packaging_type="compressed_bales",
                carbon_per_kg_km=0.225
            ),
            MaterialFlow(
                from_node="textile_mill_bangladesh", to_node="garment_factory_vietnam",
                material_type="finished_fabric", quantity_per_product=0.65,
                transport_distance_km=2850, transport_mode="sea_freight",
                transport_frequency_days=21, packaging_type="fabric_rolls",
                carbon_per_kg_km=0.019
            )
        ]
        
        flows["fashion"] = fashion_flows
        
        return flows
    
    def analyze_multi_tier_emissions(self, product_category: str, 
                                   product_weight_kg: float,
                                   manufacturing_strategy: ManufacturingStrategy = ManufacturingStrategy.HYBRID,
                                   demand_volatility: str = "medium") -> Dict[str, Any]:
        """
        Analyze complete multi-tier supply chain emissions
        
        Args:
            product_category: Category of product (smartphone, kitchen_appliance, fashion)
            product_weight_kg: Final product weight
            manufacturing_strategy: JIT vs inventory buffer strategy
            demand_volatility: low, medium, high - affects inventory and transport
            
        Returns:
            Comprehensive multi-tier emissions breakdown
        """
        
        if product_category not in self.supply_networks:
            raise ValueError(f"Product category '{product_category}' not supported")
        
        network = self.supply_networks[product_category]
        flows = self.material_flows[product_category]
        
        # Calculate emissions for each tier
        tier_emissions = {}
        total_emissions = 0
        
        for tier in SupplyTier:
            tier_nodes = [node for node in network if node.tier == tier]
            if tier_nodes:
                tier_emission = self._calculate_tier_emissions(
                    tier_nodes, flows, manufacturing_strategy, demand_volatility
                )
                tier_emissions[tier.value] = tier_emission
                total_emissions += tier_emission["total_co2_g"]
        
        # Calculate transportation emissions between tiers
        transport_emissions = self._calculate_inter_tier_transport(
            flows, product_weight_kg, manufacturing_strategy
        )
        total_emissions += transport_emissions["total_co2_g"]
        
        # Calculate inventory holding emissions
        inventory_emissions = self._calculate_inventory_emissions(
            network, manufacturing_strategy, demand_volatility
        )
        total_emissions += inventory_emissions["total_co2_g"]
        
        # Supply chain optimization analysis
        optimization_opportunities = self._analyze_optimization_opportunities(
            tier_emissions, transport_emissions, inventory_emissions
        )
        
        return {
            "total_multi_tier_co2_g": round(total_emissions, 2),
            "total_multi_tier_co2_kg": round(total_emissions / 1000, 3),
            "tier_breakdown": tier_emissions,
            "transportation_emissions": transport_emissions,
            "inventory_holding_emissions": inventory_emissions,
            "supply_chain_strategy": {
                "manufacturing_strategy": manufacturing_strategy.value,
                "demand_volatility": demand_volatility,
                "supply_chain_complexity": len(network),
                "geographic_distribution": self._calculate_geographic_span(network)
            },
            "optimization_opportunities": optimization_opportunities,
            "supply_chain_intelligence": {
                "tier_analysis": "comprehensive_multi_tier_tracking",
                "transport_optimization": "modal_shift_opportunities_identified",
                "inventory_strategy": "carbon_vs_resilience_tradeoffs_analyzed",
                "supplier_network": "upstream_emissions_fully_tracked"
            }
        }
    
    def _calculate_tier_emissions(self, tier_nodes: List[SupplyChainNode],
                                flows: List[MaterialFlow],
                                manufacturing_strategy: ManufacturingStrategy,
                                demand_volatility: str) -> Dict[str, Any]:
        """Calculate emissions for a specific supply chain tier"""
        
        tier_co2 = 0
        node_emissions = {}
        
        for node in tier_nodes:
            # Manufacturing process emissions
            base_manufacturing_co2 = node.carbon_intensity_kg_per_unit * 1000  # Convert to grams
            
            # Apply strategy multipliers
            strategy_multiplier = self._get_strategy_multiplier(manufacturing_strategy, node.tier)
            manufacturing_co2 = base_manufacturing_co2 * strategy_multiplier
            
            # Apply demand volatility impact
            volatility_multiplier = {"low": 1.0, "medium": 1.15, "high": 1.35}[demand_volatility]
            total_node_co2 = manufacturing_co2 * volatility_multiplier
            
            node_emissions[node.id] = {
                "co2_g": round(total_node_co2, 2),
                "base_carbon_intensity": node.carbon_intensity_kg_per_unit,
                "strategy_multiplier": strategy_multiplier,
                "volatility_multiplier": volatility_multiplier,
                "location": f"{node.location}",
                "energy_source": node.energy_source
            }
            
            tier_co2 += total_node_co2
        
        return {
            "total_co2_g": round(tier_co2, 2),
            "node_emissions": node_emissions,
            "tier_complexity": len(tier_nodes),
            "geographic_spread": self._calculate_tier_geographic_spread(tier_nodes)
        }
    
    def _calculate_inter_tier_transport(self, flows: List[MaterialFlow],
                                      product_weight_kg: float,
                                      manufacturing_strategy: ManufacturingStrategy) -> Dict[str, Any]:
        """Calculate transportation emissions between supply chain tiers"""
        
        transport_co2 = 0
        flow_emissions = {}
        
        for flow in flows:
            # Base transport emissions
            material_weight_kg = flow.quantity_per_product
            distance_km = flow.transport_distance_km
            carbon_per_kg_km = flow.carbon_per_kg_km
            
            base_co2 = material_weight_kg * distance_km * carbon_per_kg_km * 1000  # Convert to grams
            
            # Apply frequency multiplier based on manufacturing strategy
            frequency_multiplier = self._get_transport_frequency_multiplier(
                manufacturing_strategy, flow.transport_frequency_days
            )
            
            total_flow_co2 = base_co2 * frequency_multiplier
            
            flow_emissions[f"{flow.from_node}_{flow.to_node}"] = {
                "co2_g": round(total_flow_co2, 2),
                "material_type": flow.material_type,
                "transport_mode": flow.transport_mode,
                "distance_km": distance_km,
                "frequency_days": flow.transport_frequency_days,
                "frequency_multiplier": frequency_multiplier
            }
            
            transport_co2 += total_flow_co2
        
        return {
            "total_co2_g": round(transport_co2, 2),
            "flow_emissions": flow_emissions,
            "transport_complexity": len(flows),
            "modal_distribution": self._analyze_modal_distribution(flows)
        }
    
    def _calculate_inventory_emissions(self, network: List[SupplyChainNode],
                                     manufacturing_strategy: ManufacturingStrategy,
                                     demand_volatility: str) -> Dict[str, Any]:
        """Calculate emissions from inventory holding across the supply chain"""
        
        inventory_co2 = 0
        tier_inventory = {}
        
        # Inventory holding periods by strategy
        holding_periods = {
            ManufacturingStrategy.JUST_IN_TIME: {"base_days": 3, "volatility_multiplier": 2.5},
            ManufacturingStrategy.INVENTORY_BUFFER: {"base_days": 45, "volatility_multiplier": 1.2},
            ManufacturingStrategy.HYBRID: {"base_days": 15, "volatility_multiplier": 1.6},
            ManufacturingStrategy.DISTRIBUTED: {"base_days": 30, "volatility_multiplier": 1.1}
        }
        
        strategy_config = holding_periods[manufacturing_strategy]
        volatility_multipliers = {"low": 1.0, "medium": 1.25, "high": 1.8}
        
        for node in network:
            # Calculate inventory holding time
            base_holding_days = strategy_config["base_days"]
            strategy_volatility = strategy_config["volatility_multiplier"]
            demand_volatility_mult = volatility_multipliers[demand_volatility]
            
            actual_holding_days = base_holding_days * strategy_volatility * demand_volatility_mult
            
            # Inventory emissions (storage energy + handling)
            daily_inventory_co2_g = 2.5  # gCO2 per day per unit of capacity
            total_inventory_co2 = actual_holding_days * daily_inventory_co2_g
            
            tier_inventory[node.id] = {
                "co2_g": round(total_inventory_co2, 2),
                "holding_days": round(actual_holding_days, 1),
                "tier": node.tier.value,
                "location": node.location
            }
            
            inventory_co2 += total_inventory_co2
        
        return {
            "total_co2_g": round(inventory_co2, 2),
            "tier_inventory": tier_inventory,
            "strategy_impact": manufacturing_strategy.value,
            "volatility_impact": demand_volatility
        }
    
    def _get_strategy_multiplier(self, strategy: ManufacturingStrategy, tier: SupplyTier) -> float:
        """Get carbon multiplier based on manufacturing strategy and tier"""
        
        multipliers = {
            ManufacturingStrategy.JUST_IN_TIME: {
                SupplyTier.RAW_MATERIALS: 1.35,     # More frequent, smaller batches
                SupplyTier.COMPONENTS: 1.25,
                SupplyTier.SUB_ASSEMBLY: 1.15,
                SupplyTier.FINAL_ASSEMBLY: 1.05,
                SupplyTier.DISTRIBUTION: 1.20
            },
            ManufacturingStrategy.INVENTORY_BUFFER: {
                SupplyTier.RAW_MATERIALS: 0.85,     # Larger, efficient batches
                SupplyTier.COMPONENTS: 0.90,
                SupplyTier.SUB_ASSEMBLY: 0.95,
                SupplyTier.FINAL_ASSEMBLY: 1.00,
                SupplyTier.DISTRIBUTION: 0.80
            },
            ManufacturingStrategy.HYBRID: {
                SupplyTier.RAW_MATERIALS: 1.00,     # Balanced approach
                SupplyTier.COMPONENTS: 1.00,
                SupplyTier.SUB_ASSEMBLY: 1.00,
                SupplyTier.FINAL_ASSEMBLY: 1.00,
                SupplyTier.DISTRIBUTION: 1.00
            },
            ManufacturingStrategy.DISTRIBUTED: {
                SupplyTier.RAW_MATERIALS: 1.20,     # Regional complexity
                SupplyTier.COMPONENTS: 1.10,
                SupplyTier.SUB_ASSEMBLY: 0.90,      # Shorter transport
                SupplyTier.FINAL_ASSEMBLY: 0.85,
                SupplyTier.DISTRIBUTION: 0.70
            }
        }
        
        return multipliers.get(strategy, {}).get(tier, 1.0)
    
    def _get_transport_frequency_multiplier(self, strategy: ManufacturingStrategy, 
                                          base_frequency_days: int) -> float:
        """Calculate transport frequency impact on emissions"""
        
        if strategy == ManufacturingStrategy.JUST_IN_TIME:
            # More frequent, smaller shipments
            return min(2.0, 14 / base_frequency_days)
        elif strategy == ManufacturingStrategy.INVENTORY_BUFFER:
            # Less frequent, larger shipments
            return max(0.6, base_frequency_days / 21)
        else:
            return 1.0
    
    def _calculate_geographic_span(self, network: List[SupplyChainNode]) -> Dict[str, Any]:
        """Calculate geographic distribution of supply chain"""
        
        countries = set(node.location.split(", ")[-1] for node in network)
        
        # Calculate approximate supply chain span
        latitudes = [node.coordinates[0] for node in network]
        longitudes = [node.coordinates[1] for node in network]
        
        lat_span = max(latitudes) - min(latitudes)
        lon_span = max(longitudes) - min(longitudes)
        
        # Rough distance calculation
        geographic_span_km = math.sqrt(lat_span**2 + lon_span**2) * 111  # degrees to km
        
        return {
            "countries_involved": len(countries),
            "country_list": sorted(list(countries)),
            "geographic_span_km": round(geographic_span_km, 0),
            "supply_chain_complexity": "global" if len(countries) > 3 else "regional"
        }
    
    def _calculate_tier_geographic_spread(self, tier_nodes: List[SupplyChainNode]) -> float:
        """Calculate geographic spread within a tier"""
        if len(tier_nodes) < 2:
            return 0.0
        
        latitudes = [node.coordinates[0] for node in tier_nodes]
        longitudes = [node.coordinates[1] for node in tier_nodes]
        
        lat_span = max(latitudes) - min(latitudes)
        lon_span = max(longitudes) - min(longitudes)
        
        return math.sqrt(lat_span**2 + lon_span**2) * 111  # Convert to km
    
    def _analyze_modal_distribution(self, flows: List[MaterialFlow]) -> Dict[str, int]:
        """Analyze distribution of transportation modes"""
        
        mode_counts = {}
        for flow in flows:
            mode = flow.transport_mode
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        return mode_counts
    
    def _analyze_optimization_opportunities(self, tier_emissions: Dict,
                                          transport_emissions: Dict,
                                          inventory_emissions: Dict) -> Dict[str, Any]:
        """Analyze supply chain optimization opportunities"""
        
        total_co2 = (
            sum(tier["total_co2_g"] for tier in tier_emissions.values()) +
            transport_emissions["total_co2_g"] +
            inventory_emissions["total_co2_g"]
        )
        
        opportunities = []
        
        # Transport optimization
        if transport_emissions["total_co2_g"] / total_co2 > 0.4:
            opportunities.append({
                "type": "modal_shift",
                "description": "High transport emissions - consider sea/rail freight",
                "potential_reduction_percent": 25,
                "implementation_complexity": "medium"
            })
        
        # Inventory strategy optimization
        if inventory_emissions["total_co2_g"] / total_co2 > 0.15:
            opportunities.append({
                "type": "inventory_optimization", 
                "description": "High inventory emissions - optimize holding periods",
                "potential_reduction_percent": 15,
                "implementation_complexity": "high"
            })
        
        # Regional supplier opportunities
        tier_complexity = sum(tier.get("tier_complexity", 0) for tier in tier_emissions.values())
        if tier_complexity > 8:
            opportunities.append({
                "type": "supplier_regionalization",
                "description": "Complex global network - regionalize key suppliers",
                "potential_reduction_percent": 30,
                "implementation_complexity": "high"
            })
        
        return {
            "total_opportunities": len(opportunities),
            "optimization_recommendations": opportunities,
            "quick_wins": [opp for opp in opportunities if opp["implementation_complexity"] == "low"],
            "strategic_initiatives": [opp for opp in opportunities if opp["implementation_complexity"] == "high"]
        }
    
    def compare_manufacturing_strategies(self, product_category: str,
                                       product_weight_kg: float) -> Dict[str, Any]:
        """Compare carbon impact of different manufacturing strategies"""
        
        strategies = [
            ManufacturingStrategy.JUST_IN_TIME,
            ManufacturingStrategy.INVENTORY_BUFFER,
            ManufacturingStrategy.HYBRID,
            ManufacturingStrategy.DISTRIBUTED
        ]
        
        strategy_comparison = {}
        
        for strategy in strategies:
            emissions = self.analyze_multi_tier_emissions(
                product_category, product_weight_kg, strategy, "medium"
            )
            
            strategy_comparison[strategy.value] = {
                "total_co2_kg": emissions["total_multi_tier_co2_kg"],
                "tier_breakdown": emissions["tier_breakdown"],
                "transport_co2_g": emissions["transportation_emissions"]["total_co2_g"],
                "inventory_co2_g": emissions["inventory_holding_emissions"]["total_co2_g"],
                "optimization_opportunities": len(emissions["optimization_opportunities"]["optimization_recommendations"])
            }
        
        # Find optimal strategy
        optimal_strategy = min(strategy_comparison.keys(),
                             key=lambda s: strategy_comparison[s]["total_co2_kg"])
        
        return {
            "strategy_comparison": strategy_comparison,
            "optimal_strategy": optimal_strategy,
            "carbon_savings_vs_worst": round(
                max(s["total_co2_kg"] for s in strategy_comparison.values()) -
                min(s["total_co2_kg"] for s in strategy_comparison.values()), 3
            ),
            "recommendations": {
                "lowest_carbon": optimal_strategy,
                "business_considerations": self._get_strategy_business_impact(optimal_strategy)
            }
        }
    
    def _get_strategy_business_impact(self, strategy: str) -> Dict[str, str]:
        """Get business implications of manufacturing strategy"""
        
        impacts = {
            "just_in_time": {
                "cost": "Lower inventory costs, higher transport costs",
                "risk": "Higher supply disruption risk",
                "flexibility": "High responsiveness to demand changes"
            },
            "inventory_buffer": {
                "cost": "Higher inventory costs, lower transport costs", 
                "risk": "Lower supply disruption risk",
                "flexibility": "Moderate responsiveness"
            },
            "hybrid": {
                "cost": "Balanced cost structure",
                "risk": "Moderate supply risk",
                "flexibility": "Good balance of efficiency and responsiveness"
            },
            "distributed": {
                "cost": "Higher complexity costs, lower transport costs",
                "risk": "Resilient to regional disruptions",
                "flexibility": "High regional responsiveness"
            }
        }
        
        return impacts.get(strategy, {})

def main():
    """Demonstrate Multi-Tier Supply Chain Analysis"""
    
    print("🏭 MULTI-TIER SUPPLY CHAIN ANALYSIS DEMO")
    print("=" * 80)
    
    # Initialize system
    supply_chain = MultiTierSupplyChainAnalysis()
    
    # Example: iPhone supply chain analysis
    print("\n📱 EXAMPLE: iPhone Supply Chain Multi-Tier Analysis")
    print("-" * 60)
    
    iphone_analysis = supply_chain.analyze_multi_tier_emissions(
        product_category="smartphone",
        product_weight_kg=0.22,
        manufacturing_strategy=ManufacturingStrategy.HYBRID,
        demand_volatility="medium"
    )
    
    print(f"Product: iPhone (0.22 kg)")
    print(f"Strategy: {iphone_analysis['supply_chain_strategy']['manufacturing_strategy']}")
    print(f"Total Multi-Tier CO2: {iphone_analysis['total_multi_tier_co2_kg']:.3f} kg")
    
    print("\nTier Breakdown:")
    for tier_name, tier_data in iphone_analysis["tier_breakdown"].items():
        co2_kg = tier_data["total_co2_g"] / 1000
        print(f"  {tier_name.replace('_', ' ').title()}: {co2_kg:.3f} kg CO2")
    
    print(f"\nTransportation: {iphone_analysis['transportation_emissions']['total_co2_g']/1000:.3f} kg CO2")
    print(f"Inventory Holding: {iphone_analysis['inventory_holding_emissions']['total_co2_g']/1000:.3f} kg CO2")
    
    # Strategy comparison
    print("\n🔄 MANUFACTURING STRATEGY COMPARISON")
    print("-" * 60)
    
    strategy_comparison = supply_chain.compare_manufacturing_strategies(
        "smartphone", 0.22
    )
    
    print("Strategy Carbon Impact:")
    for strategy, data in strategy_comparison["strategy_comparison"].items():
        print(f"  {strategy.replace('_', ' ').title()}: {data['total_co2_kg']:.3f} kg CO2")
    
    print(f"\nOptimal Strategy: {strategy_comparison['optimal_strategy'].replace('_', ' ').title()}")
    print(f"Carbon Savings: {strategy_comparison['carbon_savings_vs_worst']:.3f} kg CO2 vs worst strategy")
    
    print("\n✅ Multi-Tier Supply Chain Analysis Demo Complete!")

if __name__ == "__main__":
    main()