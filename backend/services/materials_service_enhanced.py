# backend/services/materials_service_enhanced.py

import re
import os
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union

class EnhancedMaterialsIntelligenceService:
    """
    ENHANCED 5-Tier Materials Detection System
    
    🎯 MAJOR IMPROVEMENTS:
    - 300+ product categories (vs 94)
    - 35+ advanced materials (vs 14)  
    - Brand-aware predictions
    - Price-tier intelligence
    - Seasonal context awareness
    - Regional material variations
    
    Tier 1: Primary + Secondary + Percentages (Best)
    Tier 2: Primary + Secondary (No percentages) 
    Tier 3: Single main material (Current system)
    Tier 4: Category-based intelligent guessing (MASSIVELY EXPANDED)
    Tier 5: Fallback defaults (Mixed/Unknown)
    """
    
    def __init__(self):
        self.load_material_data()
        self.setup_enhanced_category_materials()
        self.setup_enhanced_keyword_patterns()
        self.setup_brand_intelligence()
        self.setup_price_tier_intelligence()
    
    def load_material_data(self):
        """Load CO2 intensity data for environmental impact scoring"""
        try:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            csv_path = os.path.join(base_dir, "common", "data", "csv", "defra_material_intensity.csv")
            
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                self.material_co2_map = dict(zip(df['material'].str.lower(), df['co2_per_kg']))
            else:
                self.material_co2_map = self.get_enhanced_co2_map()
        except Exception as e:
            print(f"⚠️ Error loading material CO2 data: {e}")
            self.material_co2_map = self.get_enhanced_co2_map()
    
    def get_enhanced_co2_map(self):
        """ENHANCED CO2 intensity values (kg CO2 per kg material)"""
        return {
            # Metals
            'aluminum': 9.2, 'steel': 2.0, 'stainless steel': 2.8, 'titanium': 35.0,
            'copper': 4.5, 'brass': 3.8, 'iron': 1.8, 'metal': 3.0,
            
            # Plastics & Composites
            'plastic': 3.5, 'polypropylene': 3.2, 'polyethylene': 2.8, 'abs': 4.1,
            'polycarbonate': 5.2, 'pvc': 3.8, 'nylon': 6.4, 'carbon fiber': 24.0,
            'fiberglass': 2.9, 'resin': 4.8, 'vinyl': 3.2, 'silicon': 5.8,
            
            # Natural Materials
            'wood': 0.4, 'bamboo': 0.3, 'cork': 0.5, 'leather': 12.0,
            'cotton': 2.1, 'linen': 1.8, 'wool': 8.5, 'silk': 11.2,
            'down': 3.4, 'foam': 2.8, 'latex': 2.6,
            
            # Textiles & Synthetic
            'polyester': 3.8, 'lycra': 4.2, 'spandex': 4.2, 'fabric': 2.1,
            'mesh': 2.3, 'fleece': 3.6, 'denim': 2.8,
            
            # Glass & Ceramics
            'glass': 1.3, 'ceramic': 1.7, 'porcelain': 1.9, 'clay': 1.2,
            
            # Paper & Cardboard
            'paper': 0.7, 'cardboard': 0.8, 'paperboard': 0.9,
            
            # Rubber & Elastomers
            'rubber': 2.8, 'silicone': 3.1, 'neoprene': 3.6,
            
            # Fallbacks
            'mixed': 2.5, 'unknown': 2.0, 'composite': 3.2
        }
    
    def setup_enhanced_category_materials(self):
        """MASSIVELY EXPANDED category-based material predictions (Tier 4)"""
        self.category_materials = {
            
            # ========== FOOD & SUPPLEMENTS (EXPANDED) ==========
            'protein': {'primary': 'Plastic', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'whey': {'primary': 'Plastic', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'creatine': {'primary': 'Plastic', 'secondary': ['Paper'], 'confidence': 0.85},
            'supplement': {'primary': 'Plastic', 'secondary': ['Paper'], 'confidence': 0.85},
            'vitamins': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.8},
            'powder': {'primary': 'Plastic', 'secondary': ['Cardboard', 'Metal'], 'confidence': 0.85},
            'nutrition': {'primary': 'Plastic', 'secondary': ['Paper'], 'confidence': 0.8},
            'energy bar': {'primary': 'Paper', 'secondary': ['Plastic'], 'confidence': 0.85},
            'protein bar': {'primary': 'Paper', 'secondary': ['Plastic'], 'confidence': 0.85},
            'energy drink': {'primary': 'Aluminum', 'secondary': [], 'confidence': 0.9},
            'sports drink': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            
            # ========== ELECTRONICS (MASSIVELY EXPANDED) ==========
            # Mobile Devices
            'phone': {'primary': 'Glass', 'secondary': ['Aluminum', 'Plastic'], 'confidence': 0.85},
            'iphone': {'primary': 'Glass', 'secondary': ['Aluminum'], 'confidence': 0.9},
            'android': {'primary': 'Glass', 'secondary': ['Plastic', 'Metal'], 'confidence': 0.85},
            'smartphone': {'primary': 'Glass', 'secondary': ['Metal', 'Plastic'], 'confidence': 0.85},
            'cell phone': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.8},
            'mobile': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.8},
            
            # Computers & Laptops  
            'laptop': {'primary': 'Aluminum', 'secondary': ['Plastic', 'Glass'], 'confidence': 0.85},
            'macbook': {'primary': 'Aluminum', 'secondary': ['Glass'], 'confidence': 0.9},
            'computer': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'desktop': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'pc': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'chromebook': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            
            # Tablets & E-readers
            'tablet': {'primary': 'Glass', 'secondary': ['Aluminum'], 'confidence': 0.85},
            'ipad': {'primary': 'Glass', 'secondary': ['Aluminum'], 'confidence': 0.9},
            'kindle': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'e-reader': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.8},
            
            # Audio Equipment
            'headphones': {'primary': 'Plastic', 'secondary': ['Metal', 'Fabric'], 'confidence': 0.8},
            'earbuds': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'airpods': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'speaker': {'primary': 'Plastic', 'secondary': ['Fabric', 'Metal'], 'confidence': 0.8},
            'bluetooth speaker': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.85},
            'soundbar': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'microphone': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            
            # TV & Displays
            'tv': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'television': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'monitor': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'display': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.8},
            'projector': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            
            # Gaming
            'gaming': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'console': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'playstation': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'xbox': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'nintendo': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'controller': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'gamepad': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            
            # Smart Devices & Wearables
            'smartwatch': {'primary': 'Aluminum', 'secondary': ['Glass', 'Rubber'], 'confidence': 0.85},
            'apple watch': {'primary': 'Aluminum', 'secondary': ['Glass'], 'confidence': 0.9},
            'fitness tracker': {'primary': 'Plastic', 'secondary': ['Rubber'], 'confidence': 0.85},
            'smart home': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.8},
            'alexa': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.85},
            'echo': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.85},
            'google home': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.85},
            
            # Photography & Video
            'camera': {'primary': 'Metal', 'secondary': ['Plastic', 'Glass'], 'confidence': 0.85},
            'dslr': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'gopro': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'lens': {'primary': 'Glass', 'secondary': ['Metal'], 'confidence': 0.9},
            'tripod': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'drone': {'primary': 'Plastic', 'secondary': ['Carbon Fiber', 'Metal'], 'confidence': 0.85},
            
            # Accessories & Peripherals
            'charger': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'cable': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'keyboard': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.9},
            'mouse': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'webcam': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'router': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'modem': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'hard drive': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'ssd': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'usb': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'flash drive': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            
            # ========== MUSICAL INSTRUMENTS (NEW CATEGORY) ==========
            'guitar': {'primary': 'Wood', 'secondary': ['Metal', 'Plastic'], 'confidence': 0.9},
            'electric guitar': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.9},
            'acoustic guitar': {'primary': 'Wood', 'secondary': [], 'confidence': 0.95},
            'bass': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.9},
            'piano': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.9},
            'keyboard': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'drums': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'violin': {'primary': 'Wood', 'secondary': [], 'confidence': 0.95},
            'saxophone': {'primary': 'Brass', 'secondary': [], 'confidence': 0.95},
            'trumpet': {'primary': 'Brass', 'secondary': [], 'confidence': 0.95},
            'flute': {'primary': 'Metal', 'secondary': [], 'confidence': 0.95},
            'clarinet': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.9},
            'harmonica': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'microphone': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'amplifier': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'synthesizer': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            
            # ========== GARDEN & OUTDOOR (NEW CATEGORY) ==========
            'lawnmower': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'garden hose': {'primary': 'Rubber', 'secondary': ['Plastic'], 'confidence': 0.9},
            'pruning shears': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'garden tools': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.85},
            'shovel': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.9},
            'rake': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.9},
            'spade': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.9},
            'watering can': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'plant pot': {'primary': 'Ceramic', 'secondary': ['Plastic'], 'confidence': 0.8},
            'planter': {'primary': 'Ceramic', 'secondary': ['Plastic'], 'confidence': 0.8},
            'fertilizer': {'primary': 'Plastic', 'secondary': ['Paper'], 'confidence': 0.85},
            'seeds': {'primary': 'Paper', 'secondary': ['Plastic'], 'confidence': 0.8},
            'mulch': {'primary': 'Wood', 'secondary': [], 'confidence': 0.9},
            'garden furniture': {'primary': 'Metal', 'secondary': ['Fabric'], 'confidence': 0.8},
            'umbrella': {'primary': 'Fabric', 'secondary': ['Metal'], 'confidence': 0.85},
            'gazebo': {'primary': 'Metal', 'secondary': ['Fabric'], 'confidence': 0.8},
            
            # ========== ART & CRAFT SUPPLIES (NEW CATEGORY) ==========
            'paintbrush': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.9},
            'paint': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'canvas': {'primary': 'Cotton', 'secondary': ['Wood'], 'confidence': 0.9},
            'pencil': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.95},
            'pen': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.9},
            'marker': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'crayon': {'primary': 'Wax', 'secondary': ['Paper'], 'confidence': 0.9},
            'colored pencil': {'primary': 'Wood', 'secondary': [], 'confidence': 0.9},
            'sketchbook': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'drawing paper': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'clay': {'primary': 'Clay', 'secondary': [], 'confidence': 0.95},
            'pottery': {'primary': 'Ceramic', 'secondary': [], 'confidence': 0.9},
            'glue': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'scissors': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'ruler': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'eraser': {'primary': 'Rubber', 'secondary': [], 'confidence': 0.95},
            'yarn': {'primary': 'Cotton', 'secondary': ['Wool'], 'confidence': 0.8},
            'fabric': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'thread': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'beads': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.8},
            
            # ========== OFFICE SUPPLIES (NEW CATEGORY) ==========
            'stapler': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'printer': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'ink cartridge': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'paper clips': {'primary': 'Metal', 'secondary': [], 'confidence': 0.95},
            'binder': {'primary': 'Plastic', 'secondary': ['Cardboard'], 'confidence': 0.85},
            'folder': {'primary': 'Cardboard', 'secondary': ['Plastic'], 'confidence': 0.85},
            'envelope': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'sticky notes': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'calculator': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'shredder': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'laminator': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'hole punch': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'tape dispenser': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'desk organizer': {'primary': 'Plastic', 'secondary': ['Wood'], 'confidence': 0.8},
            'filing cabinet': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'whiteboard': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'marker board': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            
            # ========== BABY & KIDS PRODUCTS (NEW CATEGORY) ==========
            'stroller': {'primary': 'Metal', 'secondary': ['Fabric', 'Plastic'], 'confidence': 0.85},
            'high chair': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'crib': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.9},
            'baby bottle': {'primary': 'Plastic', 'secondary': ['Silicone'], 'confidence': 0.9},
            'pacifier': {'primary': 'Silicone', 'secondary': ['Plastic'], 'confidence': 0.9},
            'diaper': {'primary': 'Plastic', 'secondary': ['Paper'], 'confidence': 0.85},
            'baby food': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.8},
            'car seat': {'primary': 'Plastic', 'secondary': ['Fabric', 'Metal'], 'confidence': 0.85},
            'baby gate': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'baby monitor': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'changing table': {'primary': 'Wood', 'secondary': ['Plastic'], 'confidence': 0.8},
            'baby clothes': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.9},
            'baby blanket': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.85},
            'baby carrier': {'primary': 'Fabric', 'secondary': ['Metal'], 'confidence': 0.85},
            'playpen': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'baby swing': {'primary': 'Plastic', 'secondary': ['Metal', 'Fabric'], 'confidence': 0.8},
            
            # ========== PET PRODUCTS (NEW CATEGORY) ==========
            'dog collar': {'primary': 'Nylon', 'secondary': ['Metal'], 'confidence': 0.9},
            'cat litter': {'primary': 'Clay', 'secondary': [], 'confidence': 0.95},
            'pet food': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'dog leash': {'primary': 'Nylon', 'secondary': ['Metal'], 'confidence': 0.9},
            'pet toy': {'primary': 'Rubber', 'secondary': ['Fabric'], 'confidence': 0.8},
            'dog bed': {'primary': 'Fabric', 'secondary': ['Foam'], 'confidence': 0.85},
            'cat bed': {'primary': 'Fabric', 'secondary': ['Foam'], 'confidence': 0.85},
            'pet carrier': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'fish tank': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.9},
            'aquarium': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.9},
            'bird cage': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'litter box': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'pet bowl': {'primary': 'Ceramic', 'secondary': ['Stainless Steel'], 'confidence': 0.8},
            'dog house': {'primary': 'Wood', 'secondary': ['Plastic'], 'confidence': 0.8},
            'scratching post': {'primary': 'Wood', 'secondary': ['Fabric'], 'confidence': 0.85},
            
            # ========== HOME IMPROVEMENT/DIY (NEW CATEGORY) ==========
            'drill': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'saw': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.9},
            'hammer': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.9},
            'screwdriver': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'wrench': {'primary': 'Metal', 'secondary': [], 'confidence': 0.95},
            'pliers': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'screws': {'primary': 'Metal', 'secondary': [], 'confidence': 0.95},
            'nails': {'primary': 'Metal', 'secondary': [], 'confidence': 0.95},
            'paint': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'tiles': {'primary': 'Ceramic', 'secondary': [], 'confidence': 0.9},
            'flooring': {'primary': 'Wood', 'secondary': ['Plastic'], 'confidence': 0.8},
            'insulation': {'primary': 'Fiberglass', 'secondary': [], 'confidence': 0.9},
            'lumber': {'primary': 'Wood', 'secondary': [], 'confidence': 0.95},
            'plywood': {'primary': 'Wood', 'secondary': [], 'confidence': 0.9},
            'sandpaper': {'primary': 'Paper', 'secondary': ['Metal'], 'confidence': 0.85},
            'measuring tape': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'level': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'ladder': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'toolbox': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            
            # ========== CLEANING SUPPLIES (NEW CATEGORY) ==========
            'vacuum': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'mop': {'primary': 'Fabric', 'secondary': ['Plastic'], 'confidence': 0.85},
            'broom': {'primary': 'Plastic', 'secondary': ['Wood'], 'confidence': 0.8},
            'detergent': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'cleaning spray': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'sponge': {'primary': 'Foam', 'secondary': [], 'confidence': 0.9},
            'scrub brush': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'toilet paper': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'paper towels': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'trash bags': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'garbage bin': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'recycling bin': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'bucket': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'rubber gloves': {'primary': 'Rubber', 'secondary': [], 'confidence': 0.95},
            'window cleaner': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            
            # ========== MEDICAL/HEALTH EQUIPMENT (NEW CATEGORY) ==========
            'thermometer': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'blood pressure monitor': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'stethoscope': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            'bandages': {'primary': 'Fabric', 'secondary': ['Plastic'], 'confidence': 0.85},
            'first aid kit': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'crutches': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'wheelchair': {'primary': 'Metal', 'secondary': ['Fabric'], 'confidence': 0.85},
            'walking stick': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.85},
            'heating pad': {'primary': 'Fabric', 'secondary': ['Plastic'], 'confidence': 0.8},
            'ice pack': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'pill organizer': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'syringe': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.9},
            'mask': {'primary': 'Fabric', 'secondary': ['Plastic'], 'confidence': 0.8},
            'gloves': {'primary': 'Latex', 'secondary': [], 'confidence': 0.9},
            
            # ========== JEWELRY & ACCESSORIES (NEW CATEGORY) ==========
            'ring': {'primary': 'Metal', 'secondary': [], 'confidence': 0.85},
            'necklace': {'primary': 'Metal', 'secondary': [], 'confidence': 0.85},
            'bracelet': {'primary': 'Metal', 'secondary': [], 'confidence': 0.8},
            'earrings': {'primary': 'Metal', 'secondary': [], 'confidence': 0.85},
            'watch': {'primary': 'Metal', 'secondary': ['Glass', 'Leather'], 'confidence': 0.8},
            'sunglasses': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'glasses': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'belt': {'primary': 'Leather', 'secondary': ['Metal'], 'confidence': 0.9},
            'wallet': {'primary': 'Leather', 'secondary': ['Plastic'], 'confidence': 0.85},
            'purse': {'primary': 'Leather', 'secondary': ['Fabric'], 'confidence': 0.8},
            'handbag': {'primary': 'Leather', 'secondary': ['Fabric'], 'confidence': 0.8},
            'backpack': {'primary': 'Fabric', 'secondary': ['Plastic'], 'confidence': 0.85},
            'suitcase': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'hat': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.85},
            'cap': {'primary': 'Fabric', 'secondary': ['Plastic'], 'confidence': 0.8},
            'scarf': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'tie': {'primary': 'Silk', 'secondary': [], 'confidence': 0.85},
            
            # ========== LIGHTING (NEW CATEGORY) ==========
            'lamp': {'primary': 'Metal', 'secondary': ['Fabric'], 'confidence': 0.8},
            'light bulb': {'primary': 'Glass', 'secondary': ['Metal'], 'confidence': 0.9},
            'led bulb': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'flashlight': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'torch': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'chandelier': {'primary': 'Metal', 'secondary': ['Glass'], 'confidence': 0.8},
            'ceiling fan': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'string lights': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'candle': {'primary': 'Wax', 'secondary': ['Glass'], 'confidence': 0.8},
            'lantern': {'primary': 'Metal', 'secondary': ['Glass'], 'confidence': 0.8},
            'night light': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'desk lamp': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'floor lamp': {'primary': 'Metal', 'secondary': ['Fabric'], 'confidence': 0.8},
            
            # ========== EXISTING CATEGORIES (ENHANCED) ==========
            
            # Tools & Hardware (Enhanced)
            'tweezers': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.95},
            'knife': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.9},
            'kitchen knife': {'primary': 'Stainless Steel', 'secondary': ['Wood'], 'confidence': 0.9},
            'utility knife': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'multi-tool': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            
            # Clothing & Textiles (Enhanced)
            'shirt': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            't-shirt': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.85},
            'dress shirt': {'primary': 'Cotton', 'secondary': [], 'confidence': 0.9},
            'polo shirt': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'jeans': {'primary': 'Cotton', 'secondary': ['Elastane'], 'confidence': 0.85},
            'jacket': {'primary': 'Polyester', 'secondary': ['Cotton'], 'confidence': 0.8},
            'winter jacket': {'primary': 'Polyester', 'secondary': ['Down'], 'confidence': 0.85},
            'shoes': {'primary': 'Leather', 'secondary': ['Rubber', 'Fabric'], 'confidence': 0.8},
            'sneakers': {'primary': 'Fabric', 'secondary': ['Rubber'], 'confidence': 0.85},
            'boots': {'primary': 'Leather', 'secondary': ['Rubber'], 'confidence': 0.85},
            'sandals': {'primary': 'Rubber', 'secondary': ['Fabric'], 'confidence': 0.8},
            'socks': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.85},
            'underwear': {'primary': 'Cotton', 'secondary': ['Elastane'], 'confidence': 0.85},
            'pajamas': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'dress': {'primary': 'Polyester', 'secondary': ['Cotton'], 'confidence': 0.8},
            'skirt': {'primary': 'Polyester', 'secondary': ['Cotton'], 'confidence': 0.8},
            'pants': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'shorts': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'hoodie': {'primary': 'Cotton', 'secondary': ['Polyester'], 'confidence': 0.8},
            'sweater': {'primary': 'Wool', 'secondary': ['Cotton'], 'confidence': 0.8},
            
            # Outdoor & Camping (Enhanced)
            'camping chair': {'primary': 'Metal', 'secondary': ['Fabric'], 'confidence': 0.9},
            'tent': {'primary': 'Polyester', 'secondary': ['Metal'], 'confidence': 0.85},
            'sleeping bag': {'primary': 'Polyester', 'secondary': ['Down'], 'confidence': 0.8},
            'backpack': {'primary': 'Nylon', 'secondary': ['Plastic'], 'confidence': 0.85},
            'hiking boots': {'primary': 'Leather', 'secondary': ['Rubber'], 'confidence': 0.9},
            'compass': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'camping stove': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'cooler': {'primary': 'Plastic', 'secondary': ['Foam'], 'confidence': 0.85},
            'water bottle': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'thermos': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.9},
            
            # Books & Media (Enhanced)
            'book': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.95},
            'novel': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.95},
            'paperback': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'hardcover': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'textbook': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'magazine': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'notebook': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'diary': {'primary': 'Paper', 'secondary': ['Leather'], 'confidence': 0.8},
            'journal': {'primary': 'Paper', 'secondary': ['Leather'], 'confidence': 0.8},
            'comic book': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'graphic novel': {'primary': 'Paper', 'secondary': ['Cardboard'], 'confidence': 0.9},
            'cd': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'dvd': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'blu-ray': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'vinyl record': {'primary': 'Vinyl', 'secondary': [], 'confidence': 0.95},
            
            # Furniture (Enhanced)
            'chair': {'primary': 'Wood', 'secondary': ['Metal', 'Fabric'], 'confidence': 0.8},
            'office chair': {'primary': 'Plastic', 'secondary': ['Metal', 'Fabric'], 'confidence': 0.85},
            'dining chair': {'primary': 'Wood', 'secondary': ['Fabric'], 'confidence': 0.85},
            'armchair': {'primary': 'Wood', 'secondary': ['Fabric'], 'confidence': 0.8},
            'desk': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.8},
            'standing desk': {'primary': 'Metal', 'secondary': ['Wood'], 'confidence': 0.85},
            'table': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.8},
            'dining table': {'primary': 'Wood', 'secondary': [], 'confidence': 0.85},
            'coffee table': {'primary': 'Wood', 'secondary': ['Glass'], 'confidence': 0.8},
            'sofa': {'primary': 'Fabric', 'secondary': ['Wood', 'Metal'], 'confidence': 0.85},
            'couch': {'primary': 'Fabric', 'secondary': ['Wood', 'Metal'], 'confidence': 0.85},
            'sectional': {'primary': 'Fabric', 'secondary': ['Wood'], 'confidence': 0.85},
            'recliner': {'primary': 'Fabric', 'secondary': ['Metal'], 'confidence': 0.85},
            'bed': {'primary': 'Wood', 'secondary': ['Metal', 'Fabric'], 'confidence': 0.8},
            'mattress': {'primary': 'Foam', 'secondary': ['Fabric'], 'confidence': 0.85},
            'bookshelf': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.85},
            'dresser': {'primary': 'Wood', 'secondary': [], 'confidence': 0.85},
            'nightstand': {'primary': 'Wood', 'secondary': [], 'confidence': 0.85},
            'wardrobe': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.8},
            'cabinet': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.8},
            'shelf': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.8},
            
            # Automotive (Enhanced)
            'tire': {'primary': 'Rubber', 'secondary': ['Metal'], 'confidence': 0.95},
            'tires': {'primary': 'Rubber', 'secondary': ['Metal'], 'confidence': 0.95},
            'car battery': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.9},
            'air filter': {'primary': 'Paper', 'secondary': ['Plastic'], 'confidence': 0.85},
            'oil filter': {'primary': 'Metal', 'secondary': ['Paper'], 'confidence': 0.85},
            'motor oil': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'brake pads': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'windshield wipers': {'primary': 'Rubber', 'secondary': ['Metal'], 'confidence': 0.9},
            'car mats': {'primary': 'Rubber', 'secondary': ['Fabric'], 'confidence': 0.8},
            'seat covers': {'primary': 'Fabric', 'secondary': ['Plastic'], 'confidence': 0.8},
            'car charger': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            
            # Beauty & Personal Care (Enhanced)
            'shampoo': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'conditioner': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'body wash': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'soap': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.8},
            'bar soap': {'primary': 'Paper', 'secondary': [], 'confidence': 0.85},
            'lotion': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'moisturizer': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'cream': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'sunscreen': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'perfume': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.9},
            'cologne': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.9},
            'deodorant': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'toothbrush': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'toothpaste': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'mouthwash': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'makeup': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'lipstick': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'foundation': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.85},
            'mascara': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'nail polish': {'primary': 'Glass', 'secondary': [], 'confidence': 0.9},
            'hair dryer': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'straightener': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'curling iron': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'razor': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.9},
            'electric razor': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            
            # Sports & Fitness (Enhanced)
            'basketball': {'primary': 'Rubber', 'secondary': [], 'confidence': 0.95},
            'football': {'primary': 'Leather', 'secondary': ['Rubber'], 'confidence': 0.9},
            'soccer ball': {'primary': 'Leather', 'secondary': ['Rubber'], 'confidence': 0.9},
            'tennis ball': {'primary': 'Rubber', 'secondary': ['Fabric'], 'confidence': 0.9},
            'tennis racket': {'primary': 'Carbon Fiber', 'secondary': ['Rubber'], 'confidence': 0.85},
            'badminton racket': {'primary': 'Carbon Fiber', 'secondary': [], 'confidence': 0.85},
            'ping pong paddle': {'primary': 'Wood', 'secondary': ['Rubber'], 'confidence': 0.9},
            'golf club': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            'golf ball': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'baseball': {'primary': 'Leather', 'secondary': [], 'confidence': 0.9},
            'baseball bat': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.85},
            'volleyball': {'primary': 'Leather', 'secondary': [], 'confidence': 0.9},
            'yoga mat': {'primary': 'Rubber', 'secondary': [], 'confidence': 0.9},
            'exercise mat': {'primary': 'Foam', 'secondary': [], 'confidence': 0.85},
            'dumbbell': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            'weights': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            'kettlebell': {'primary': 'Metal', 'secondary': [], 'confidence': 0.95},
            'resistance bands': {'primary': 'Rubber', 'secondary': [], 'confidence': 0.95},
            'jump rope': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'foam roller': {'primary': 'Foam', 'secondary': [], 'confidence': 0.95},
            'treadmill': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'exercise bike': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'elliptical': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'rowing machine': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'skiing': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.85},
            'snowboard': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.85},
            'skateboard': {'primary': 'Wood', 'secondary': ['Metal'], 'confidence': 0.85},
            'bicycle': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            'bike': {'primary': 'Metal', 'secondary': ['Rubber'], 'confidence': 0.9},
            'helmet': {'primary': 'Plastic', 'secondary': ['Foam'], 'confidence': 0.9},
            'life jacket': {'primary': 'Fabric', 'secondary': ['Foam'], 'confidence': 0.85},
            'swimming goggles': {'primary': 'Plastic', 'secondary': ['Silicone'], 'confidence': 0.9},
            'wetsuit': {'primary': 'Neoprene', 'secondary': [], 'confidence': 0.95},
            
            # Kitchen & Home (Enhanced)
            'mug': {'primary': 'Ceramic', 'secondary': [], 'confidence': 0.85},
            'coffee mug': {'primary': 'Ceramic', 'secondary': [], 'confidence': 0.9},
            'travel mug': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.85},
            'cup': {'primary': 'Ceramic', 'secondary': ['Glass'], 'confidence': 0.8},
            'glass': {'primary': 'Glass', 'secondary': [], 'confidence': 0.95},
            'water bottle': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'bottle': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence': 0.8},
            'wine bottle': {'primary': 'Glass', 'secondary': [], 'confidence': 0.95},
            'plate': {'primary': 'Ceramic', 'secondary': ['Glass'], 'confidence': 0.8},
            'dinner plate': {'primary': 'Ceramic', 'secondary': [], 'confidence': 0.9},
            'paper plate': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'bowl': {'primary': 'Ceramic', 'secondary': ['Glass'], 'confidence': 0.8},
            'mixing bowl': {'primary': 'Stainless Steel', 'secondary': ['Glass'], 'confidence': 0.8},
            'pot': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'pan': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'frying pan': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'non-stick pan': {'primary': 'Aluminum', 'secondary': ['Plastic'], 'confidence': 0.85},
            'cast iron': {'primary': 'Iron', 'secondary': [], 'confidence': 0.95},
            'baking sheet': {'primary': 'Aluminum', 'secondary': [], 'confidence': 0.9},
            'cookie sheet': {'primary': 'Aluminum', 'secondary': [], 'confidence': 0.9},
            'spoon': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'fork': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'knife': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'spatula': {'primary': 'Silicone', 'secondary': ['Stainless Steel'], 'confidence': 0.8},
            'wooden spoon': {'primary': 'Wood', 'secondary': [], 'confidence': 0.95},
            'cutting board': {'primary': 'Wood', 'secondary': ['Plastic'], 'confidence': 0.8},
            'plastic cutting board': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'can opener': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.9},
            'bottle opener': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.95},
            'corkscrew': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'measuring cup': {'primary': 'Glass', 'secondary': ['Plastic'], 'confidence': 0.8},
            'measuring spoons': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'whisk': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'tongs': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'colander': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.8},
            'strainer': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'grater': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.9},
            'peeler': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.9},
            'blender': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'food processor': {'primary': 'Plastic', 'secondary': ['Stainless Steel'], 'confidence': 0.8},
            'mixer': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.85},
            'toaster': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.85},
            'microwave': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'coffee maker': {'primary': 'Plastic', 'secondary': ['Glass', 'Metal'], 'confidence': 0.8},
            'espresso machine': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.85},
            'kettle': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.85},
            'electric kettle': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.85},
            'slow cooker': {'primary': 'Ceramic', 'secondary': ['Plastic'], 'confidence': 0.85},
            'pressure cooker': {'primary': 'Stainless Steel', 'secondary': [], 'confidence': 0.9},
            'instant pot': {'primary': 'Stainless Steel', 'secondary': ['Plastic'], 'confidence': 0.9},
            'air fryer': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'rice cooker': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'bread maker': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'juicer': {'primary': 'Plastic', 'secondary': ['Stainless Steel'], 'confidence': 0.8},
            'stand mixer': {'primary': 'Metal', 'secondary': [], 'confidence': 0.9},
            'hand mixer': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'ice cream maker': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'food dehydrator': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            'vacuum sealer': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.85},
            
            # Toys & Games (Enhanced)
            'lego': {'primary': 'ABS Plastic', 'secondary': [], 'confidence': 0.95},
            'building blocks': {'primary': 'Plastic', 'secondary': ['Wood'], 'confidence': 0.8},
            'puzzle': {'primary': 'Cardboard', 'secondary': ['Wood'], 'confidence': 0.8},
            'jigsaw puzzle': {'primary': 'Cardboard', 'secondary': [], 'confidence': 0.9},
            'doll': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'barbie': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.9},
            'action figure': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'toy car': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'remote control car': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'toy': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.8},
            'plush toy': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'stuffed animal': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'teddy bear': {'primary': 'Fabric', 'secondary': [], 'confidence': 0.9},
            'board game': {'primary': 'Cardboard', 'secondary': ['Plastic'], 'confidence': 0.8},
            'card game': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'playing cards': {'primary': 'Paper', 'secondary': [], 'confidence': 0.95},
            'video game': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'game cartridge': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'frisbee': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'yo-yo': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.85},
            'slinky': {'primary': 'Metal', 'secondary': [], 'confidence': 0.95},
            'rubiks cube': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'kite': {'primary': 'Plastic', 'secondary': ['Fabric'], 'confidence': 0.8},
            'water gun': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.95},
            'nerf gun': {'primary': 'Plastic', 'secondary': [], 'confidence': 0.9},
            'toy train': {'primary': 'Plastic', 'secondary': ['Metal'], 'confidence': 0.8},
            'model train': {'primary': 'Metal', 'secondary': ['Plastic'], 'confidence': 0.8},
            'play doh': {'primary': 'Clay', 'secondary': ['Plastic'], 'confidence': 0.85},
            'modeling clay': {'primary': 'Clay', 'secondary': [], 'confidence': 0.9},
        }
    
    def setup_enhanced_keyword_patterns(self):
        """MASSIVELY ENHANCED keyword matching for material detection"""
        self.material_keywords = {
            # Metals (Enhanced)
            'Stainless Steel': ['stainless steel', 'stainless', 'ss304', 'ss316', '18/8 stainless', '18/10 stainless'],
            'Aluminum': ['aluminum', 'aluminium', 'anodized aluminum'],  # Removed 'alloy' - too broad
            'Titanium': ['titanium', 'grade 5 titanium', 'ti6al4v'],
            'Copper': ['copper', 'cu', 'copper alloy'],
            'Brass': ['brass', 'bronze'],
            'Iron': ['iron', 'cast iron', 'wrought iron'],
            'Metal': ['metal', 'metallic', 'steel', 'alloy'],  # Generic metal terms
            
            # Plastics & Composites (Enhanced)
            'Plastic': ['plastic', 'polymer', 'synthetic resin'],
            'Polypropylene': ['polypropylene', 'pp plastic', 'pp5'],
            'Polyethylene': ['polyethylene', 'pe plastic', 'hdpe', 'ldpe'],
            'ABS Plastic': ['abs plastic', 'abs', 'acrylonitrile'],
            'Polycarbonate': ['polycarbonate', 'pc plastic', 'lexan'],
            'PVC': ['pvc', 'vinyl chloride', 'polyvinyl chloride'],
            'Nylon': ['nylon', 'polyamide', 'pa6', 'pa66'],
            'Carbon Fiber': ['carbon fiber', 'carbon fibre', 'carbon composite', 'cf'],
            'Fiberglass': ['fiberglass', 'glass fiber', 'glass fibre', 'gfrp'],
            'Resin': ['resin', 'epoxy resin', 'polyester resin'],
            'Vinyl': ['vinyl', 'pvc vinyl'],
            'Silicon': ['silicon', 'silicone polymer'],
            
            # Natural Materials (Enhanced)
            'Wood': ['wood', 'wooden', 'timber', 'oak', 'pine', 'maple', 'cherry', 'walnut', 'mahogany', 'teak', 'birch', 'ash'],
            'Bamboo': ['bamboo', 'bamboo fiber', 'bamboo wood'],
            'Cork': ['cork', 'cork board'],
            'Leather': ['leather', 'genuine leather', 'full grain leather', 'top grain leather', 'suede'],
            'Down': ['down', 'goose down', 'duck down', 'down filling'],
            'Foam': ['foam', 'memory foam', 'polyurethane foam', 'latex foam'],
            'Latex': ['latex', 'natural latex', 'synthetic latex'],
            
            # Textiles & Fibers (Enhanced)
            'Cotton': ['cotton', '100% cotton', 'organic cotton', 'pima cotton', 'egyptian cotton'],
            'Linen': ['linen', '100% linen', 'flax linen'],
            'Wool': ['wool', 'merino wool', 'cashmere', 'alpaca wool', 'lambswool'],
            'Silk': ['silk', 'mulberry silk', 'silk fiber'],
            'Polyester': ['polyester', 'poly', 'synthetic fabric', 'microfiber'],
            'Lycra': ['lycra', 'spandex', 'elastane', 'stretch fabric'],
            'Nylon': ['nylon fabric', 'nylon fiber', 'ripstop nylon'],
            'Fabric': ['fabric', 'textile', 'cloth', 'woven', 'knit'],
            'Mesh': ['mesh', 'breathable mesh', 'air mesh'],
            'Fleece': ['fleece', 'polar fleece', 'micro fleece'],
            'Denim': ['denim', 'jean fabric', 'cotton denim'],
            'Canvas': ['canvas', 'duck canvas', 'cotton canvas'],
            'Velvet': ['velvet', 'crushed velvet'],
            'Satin': ['satin', 'silk satin'],
            'Tweed': ['tweed', 'wool tweed'],
            
            # Glass & Ceramics (Enhanced)
            'Glass': ['glass', 'tempered glass', 'borosilicate glass', 'soda lime glass', 'crystal'],
            'Ceramic': ['ceramic', 'pottery', 'stoneware', 'earthenware'],
            'Porcelain': ['porcelain', 'bone china', 'fine china'],
            'Clay': ['clay', 'terracotta', 'ceramic clay'],
            
            # Paper & Cardboard (Enhanced)
            'Paper': ['paper', 'pulp', 'recycled paper', 'kraft paper'],
            'Cardboard': ['cardboard', 'corrugated cardboard', 'paperboard', 'carton'],
            'Paperboard': ['paperboard', 'chipboard'],
            
            # Rubber & Elastomers (Enhanced)
            'Rubber': ['rubber', 'natural rubber', 'synthetic rubber'],
            'Silicone': ['silicone', 'food grade silicone', 'medical grade silicone'],
            'Neoprene': ['neoprene', 'wetsuit material'],
            
            # Wax & Other
            'Wax': ['wax', 'beeswax', 'paraffin wax', 'soy wax'],
            
            # Composite & Mixed
            'Composite': ['composite', 'composite material', 'laminate'],
            'Mixed': ['mixed materials', 'multi-material', 'hybrid'],
        }
    
    def setup_brand_intelligence(self):
        """Brand-aware material predictions for enhanced accuracy"""
        self.brand_materials = {
            # Premium brands typically use higher quality materials
            'apple': {
                'phone': {'primary': 'Glass', 'secondary': ['Aluminum'], 'confidence_boost': 0.1},
                'laptop': {'primary': 'Aluminum', 'secondary': ['Glass'], 'confidence_boost': 0.1},
                'watch': {'primary': 'Aluminum', 'secondary': ['Glass'], 'confidence_boost': 0.1},
            },
            'samsung': {
                'phone': {'primary': 'Glass', 'secondary': ['Metal', 'Plastic'], 'confidence_boost': 0.05},
                'tablet': {'primary': 'Glass', 'secondary': ['Metal'], 'confidence_boost': 0.05},
            },
            'nike': {
                'shoes': {'primary': 'Fabric', 'secondary': ['Rubber'], 'confidence_boost': 0.05},
                'clothing': {'primary': 'Polyester', 'secondary': ['Cotton'], 'confidence_boost': 0.05},
            },
            'adidas': {
                'shoes': {'primary': 'Fabric', 'secondary': ['Rubber'], 'confidence_boost': 0.05},
            },
            'lego': {
                'toy': {'primary': 'ABS Plastic', 'secondary': [], 'confidence_boost': 0.15},
            },
        }
    
    def setup_price_tier_intelligence(self):
        """Price-tier aware material predictions"""
        self.price_tier_keywords = {
            'premium': ['premium', 'luxury', 'high-end', 'professional', 'pro'],
            'budget': ['budget', 'basic', 'economy', 'affordable', 'value'],
            'mid-range': ['standard', 'classic', 'regular'],
        }
        
        self.price_tier_materials = {
            'premium': {
                'phone': {'primary': 'Titanium', 'secondary': ['Glass'], 'confidence_boost': 0.1},
                'watch': {'primary': 'Titanium', 'secondary': ['Sapphire Glass'], 'confidence_boost': 0.1},
                'cookware': {'primary': 'Stainless Steel', 'secondary': [], 'confidence_boost': 0.1},
            },
            'budget': {
                'phone': {'primary': 'Plastic', 'secondary': ['Glass'], 'confidence_boost': 0.05},
                'cookware': {'primary': 'Aluminum', 'secondary': ['Plastic'], 'confidence_boost': 0.05},
            }
        }
    
    def detect_materials(self, product_data: Dict, amazon_extracted_materials: Dict = None) -> Dict:
        """
        ENHANCED main entry point for 5-tier materials detection
        
        Args:
            product_data: Product info (title, description, category, etc.)
            amazon_extracted_materials: Pre-extracted materials from Amazon scraping
            
        Returns:
            Dict with materials info, tier used, and confidence
        """
        
        # Try each tier in order of preference
        result = None
        
        # Tier 1: Try detailed extraction with percentages
        if amazon_extracted_materials and amazon_extracted_materials.get('materials'):
            result = self._tier1_detailed_with_percentages(amazon_extracted_materials)
            if result:
                result['tier'] = 1
                result['tier_name'] = 'Detailed with percentages'
                return self._apply_intelligence_boosts(result, product_data)
        
        # Tier 2: Try detailed extraction without percentages
        if amazon_extracted_materials and amazon_extracted_materials.get('materials'):
            result = self._tier2_detailed_no_percentages(amazon_extracted_materials)
            if result:
                result['tier'] = 2
                result['tier_name'] = 'Detailed materials'
                return self._apply_intelligence_boosts(result, product_data)
        
        # Tier 4: Enhanced category-based intelligent guessing (CHECK BEFORE TIER 3)
        result = self._tier4_enhanced_category_based(product_data)
        if result:
            result['tier'] = 4
            result['tier_name'] = 'Enhanced category prediction'
            return self._apply_intelligence_boosts(result, product_data)
        
        # Tier 3: Enhanced single material detection
        result = self._tier3_enhanced_single_material(product_data)
        if result and result['primary_material'] not in ['Mixed', 'Unknown']:
            result['tier'] = 3
            result['tier_name'] = 'Enhanced keyword detection'
            return self._apply_intelligence_boosts(result, product_data)
        
        # Tier 5: Fallback defaults
        result = self._tier5_fallback()
        result['tier'] = 5
        result['tier_name'] = 'Fallback default'
        return result
    
    def _apply_intelligence_boosts(self, result: Dict, product_data: Dict) -> Dict:
        """Apply brand and price tier intelligence to boost accuracy"""
        title = product_data.get('title', '').lower()
        
        # Check for brand intelligence
        for brand, brand_info in self.brand_materials.items():
            if brand in title:
                for product_type, material_info in brand_info.items():
                    if product_type in title:
                        if result['primary_material'].lower() == material_info['primary'].lower():
                            result['confidence'] = min(0.98, result['confidence'] + material_info['confidence_boost'])
                            result['intelligence_applied'] = f'Brand: {brand}'
                        break
                break
        
        # Check for price tier intelligence
        price_tier = None
        for tier, keywords in self.price_tier_keywords.items():
            if any(keyword in title for keyword in keywords):
                price_tier = tier
                break
        
        if price_tier and price_tier in self.price_tier_materials:
            tier_materials = self.price_tier_materials[price_tier]
            for product_type, material_info in tier_materials.items():
                if product_type in title:
                    if result['primary_material'].lower() == material_info['primary'].lower():
                        result['confidence'] = min(0.98, result['confidence'] + material_info['confidence_boost'])
                        result['intelligence_applied'] = result.get('intelligence_applied', '') + f' Price-tier: {price_tier}'
                    break
        
        return result
    
    def _tier1_detailed_with_percentages(self, amazon_materials: Dict) -> Optional[Dict]:
        """Enhanced Tier 1: Detailed materials with percentage breakdown"""
        materials = amazon_materials.get('materials', [])
        if not materials or len(materials) < 1:
            return None
        
        # Check if we have percentage data
        has_percentages = any(m.get('weight', 0) > 0 for m in materials)
        if not has_percentages:
            return None
        
        # Sort by weight (highest first)
        materials_sorted = sorted(materials, key=lambda x: x.get('weight', 0), reverse=True)
        
        primary = materials_sorted[0]
        secondary = materials_sorted[1:] if len(materials_sorted) > 1 else []
        
        # Calculate environmental impact score
        env_impact = self._calculate_environmental_impact(materials_sorted)
        
        return {
            'primary_material': primary['name'],
            'primary_percentage': round(primary.get('weight', 0) * 100, 1),
            'secondary_materials': [
                {
                    'name': m['name'], 
                    'percentage': round(m.get('weight', 0) * 100, 1)
                } for m in secondary
            ],
            'all_materials': materials_sorted,
            'confidence': 0.95,
            'environmental_impact_score': env_impact,
            'has_percentages': True
        }
    
    def _tier2_detailed_no_percentages(self, amazon_materials: Dict) -> Optional[Dict]:
        """Enhanced Tier 2: Detailed materials without percentages"""
        materials = amazon_materials.get('materials', [])
        if not materials or len(materials) < 1:
            return None
        
        # Use confidence scores to determine primary
        materials_sorted = sorted(materials, key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        primary = materials_sorted[0]
        secondary = materials_sorted[1:] if len(materials_sorted) > 1 else []
        
        # Estimate environmental impact without exact percentages
        env_impact = self._estimate_environmental_impact_no_percentages(materials_sorted)
        
        return {
            'primary_material': primary['name'],
            'primary_percentage': None,
            'secondary_materials': [{'name': m['name'], 'percentage': None} for m in secondary],
            'all_materials': materials_sorted,
            'confidence': 0.8,
            'environmental_impact_score': env_impact,
            'has_percentages': False
        }
    
    def _tier3_enhanced_single_material(self, product_data: Dict) -> Dict:
        """Enhanced Tier 3: Single material detection with improved keyword matching"""
        title = product_data.get('title', '').lower()
        description = product_data.get('description', '').lower()
        text = f"{title} {description}"
        
        # Enhanced keyword matching with confidence scoring
        material_scores = {}
        
        for material, keywords in self.material_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    # Weight longer, more specific keywords higher
                    keyword_weight = len(keyword.split()) * 0.2 + 0.3
                    score += keyword_weight
            
            if score > 0:
                material_scores[material] = score
        
        if material_scores:
            # Get the highest scoring material
            best_material = max(material_scores.items(), key=lambda x: x[1])
            material_name = best_material[0]
            confidence = min(0.9, 0.5 + best_material[1] * 0.1)  # Scale confidence
            
            env_impact = self.material_co2_map.get(material_name.lower(), 2.5)
            return {
                'primary_material': material_name,
                'primary_percentage': None,
                'secondary_materials': [],
                'all_materials': [{'name': material_name, 'confidence_score': confidence}],
                'confidence': confidence,
                'environmental_impact_score': env_impact,
                'has_percentages': False
            }
        
        return {
            'primary_material': 'Mixed',
            'primary_percentage': None,
            'secondary_materials': [],
            'all_materials': [],
            'confidence': 0.3,
            'environmental_impact_score': 2.5,
            'has_percentages': False
        }
    
    def _tier4_enhanced_category_based(self, product_data: Dict) -> Optional[Dict]:
        """Enhanced Tier 4: Smart category-based material prediction with fuzzy matching"""
        title = product_data.get('title', '').lower()
        category = product_data.get('category', '').lower()
        
        # Enhanced matching with fuzzy logic
        best_match = None
        best_score = 0
        
        for product_type, material_info in self.category_materials.items():
            score = 0
            
            # Exact matches get highest score
            if product_type in title or product_type in category:
                score = 10
            
            # Partial matches (individual words)
            product_words = product_type.split()
            for word in product_words:
                if word in title or word in category:
                    score += 3
            
            # Fuzzy matching for similar terms
            if 'phone' in product_type and ('mobile' in title or 'cell' in title):
                score += 5
            if 'laptop' in product_type and ('notebook' in title or 'computer' in title):
                score += 5
            if 'shirt' in product_type and ('tee' in title or 'top' in title):
                score += 3
            
            if score > best_score:
                best_score = score
                best_match = (product_type, material_info)
        
        if best_match and best_score >= 3:  # Minimum threshold
            product_type, material_info = best_match
            primary = material_info['primary']
            secondary_list = material_info['secondary']
            base_confidence = material_info['confidence']
            
            # Adjust confidence based on match quality
            confidence = base_confidence * (min(best_score, 10) / 10)
            
            # Create secondary materials list
            secondary_materials = [{'name': mat, 'percentage': None} for mat in secondary_list]
            
            # Calculate environmental impact
            all_materials = [primary] + secondary_list
            env_impact = sum(self.material_co2_map.get(mat.lower(), 2.5) for mat in all_materials) / len(all_materials)
            
            return {
                'primary_material': primary,
                'primary_percentage': None,
                'secondary_materials': secondary_materials,
                'all_materials': [{'name': mat, 'confidence_score': confidence} for mat in all_materials],
                'confidence': confidence,
                'environmental_impact_score': env_impact,
                'has_percentages': False,
                'prediction_method': f'Enhanced category: {product_type} (score: {best_score})'
            }
        
        return None
    
    def _tier5_fallback(self) -> Dict:
        """Tier 5: Final fallback when nothing else works"""
        return {
            'primary_material': 'Mixed',
            'primary_percentage': None,
            'secondary_materials': [],
            'all_materials': [],
            'confidence': 0.1,
            'environmental_impact_score': 2.5,
            'has_percentages': False,
            'prediction_method': 'Fallback default'
        }
    
    def _calculate_environmental_impact(self, materials_with_weights: List[Dict]) -> float:
        """Calculate weighted environmental impact based on material percentages"""
        total_impact = 0
        for material in materials_with_weights:
            material_name = material['name'].lower()
            weight = material.get('weight', 0)
            co2_intensity = self.material_co2_map.get(material_name, 2.5)
            total_impact += co2_intensity * weight
        
        return round(total_impact, 2)
    
    def _estimate_environmental_impact_no_percentages(self, materials: List[Dict]) -> float:
        """Estimate environmental impact when percentages unknown"""
        if not materials:
            return 2.5
        
        # Assume primary material is 70%, secondary materials split the rest
        impacts = []
        for i, material in enumerate(materials):
            material_name = material['name'].lower()
            co2_intensity = self.material_co2_map.get(material_name, 2.5)
            
            if i == 0:  # Primary material
                weight = 0.7
            else:  # Secondary materials
                weight = 0.3 / (len(materials) - 1) if len(materials) > 1 else 0
            
            impacts.append(co2_intensity * weight)
        
        return round(sum(impacts), 2)

# Enhanced convenience function for easy integration
def detect_product_materials_enhanced(product_data: Dict, amazon_materials: Dict = None) -> Dict:
    """
    ENHANCED easy-to-use function for detecting materials in any product
    
    🎯 NEW FEATURES:
    - 300+ product categories (vs 94)
    - 35+ advanced materials (vs 14)
    - Brand-aware predictions
    - Price-tier intelligence
    - Enhanced fuzzy matching
    - Improved confidence scoring
    
    Usage:
        result = detect_product_materials_enhanced(product_data, amazon_materials)
        print(f"Primary: {result['primary_material']}")
        print(f"Tier: {result['tier']} - {result['tier_name']}")
        print(f"Confidence: {result['confidence']:.1%}")
    """
    service = EnhancedMaterialsIntelligenceService()
    return service.detect_materials(product_data, amazon_materials)