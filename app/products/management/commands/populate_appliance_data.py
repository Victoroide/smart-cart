from django.core.management.base import BaseCommand
from app.products.models import Brand, ProductCategory, Warranty
from django.db import transaction

class Command(BaseCommand):
    help = 'Populates the database with realistic appliance brands, categories, and warranties'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to populate appliance data...')
        
        # Clear existing data if needed
        self.stdout.write('Clearing existing data...')
        Brand.objects.all().delete()
        ProductCategory.objects.all().delete()
        Warranty.objects.all().delete()
        
        # Create categories
        self.stdout.write('Creating product categories...')
        categories = [
            # Major appliances
            {"name": "Refrigeradores y Congeladores", "active": True},
            {"name": "Lavadoras y Secadoras", "active": True},
            {"name": "Cocinas y Hornos", "active": True},
            {"name": "Lavavajillas", "active": True},
            {"name": "Campanas y Extractores", "active": True},
            
            # Small appliances
            {"name": "Microondas", "active": True},
            {"name": "Cafeteras", "active": True},
            {"name": "Licuadoras y Batidoras", "active": True},
            {"name": "Tostadoras", "active": True},
            {"name": "Freidoras", "active": True},
            
            # Climate control
            {"name": "Aires Acondicionados", "active": True},
            {"name": "Ventiladores", "active": True},
            {"name": "Calefactores", "active": True},
            {"name": "Purificadores de Aire", "active": True},
            
            # Home entertainment/electronics
            {"name": "Televisores", "active": True},
            {"name": "Equipos de Sonido", "active": True},
            {"name": "Aspiradoras y Limpieza", "active": True},
            {"name": "Planchas", "active": True},
        ]
        
        category_objects = []
        for category_data in categories:
            category = ProductCategory.objects.create(**category_data)
            category_objects.append(category)
            self.stdout.write(f'Created category: {category.name}')
        
        # Create brands
        self.stdout.write('Creating brands...')
        brands = [
            {"name": "Samsung", "active": True},
            {"name": "LG", "active": True},
            {"name": "Whirlpool", "active": True},
            {"name": "Mabe", "active": True},
            {"name": "Electrolux", "active": True},
            {"name": "Bosch", "active": True},
            {"name": "General Electric", "active": True},
            {"name": "Frigidaire", "active": True},
            {"name": "Haier", "active": True},
            {"name": "Sony", "active": True},
            {"name": "Panasonic", "active": True},
            {"name": "Philips", "active": True},
            {"name": "Oster", "active": True},
            {"name": "Black & Decker", "active": True},
            {"name": "Hamilton Beach", "active": True},
            {"name": "Midea", "active": True},
            {"name": "Teka", "active": True},
            {"name": "Siemens", "active": True},
        ]
        
        brand_objects = {}
        for brand_data in brands:
            brand = Brand.objects.create(**brand_data)
            brand_objects[brand.name] = brand
            self.stdout.write(f'Created brand: {brand.name}')
        
        # Create warranties
        self.stdout.write('Creating warranties...')
        
        warranties = [
            # Samsung warranties
            {
                "name": "Garantía Estándar Samsung",
                "description": "Garantía limitada que cubre defectos de fabricación y materiales",
                "duration_months": 12,
                "brand": brand_objects["Samsung"],
                "active": True
            },
            {
                "name": "Garantía Extendida Samsung Premium",
                "description": "Cobertura ampliada para electrodomésticos de gama alta",
                "duration_months": 36,
                "brand": brand_objects["Samsung"],
                "active": True
            },
            
            # LG warranties
            {
                "name": "Garantía Básica LG",
                "description": "Garantía oficial para todos los productos LG",
                "duration_months": 12,
                "brand": brand_objects["LG"],
                "active": True
            },
            {
                "name": "LG ProCare",
                "description": "Garantía extendida con soporte prioritario y cobertura ampliada",
                "duration_months": 24,
                "brand": brand_objects["LG"],
                "active": True
            },
            
            # Whirlpool warranties
            {
                "name": "Garantía Total Whirlpool",
                "description": "Cobertura completa para todos los electrodomésticos Whirlpool",
                "duration_months": 12,
                "brand": brand_objects["Whirlpool"],
                "active": True
            },
            {
                "name": "Whirlpool Protection Plus",
                "description": "Garantía ampliada con servicio a domicilio incluido",
                "duration_months": 36,
                "brand": brand_objects["Whirlpool"],
                "active": True
            },
            
            # Mabe warranties
            {
                "name": "Garantía Básica Mabe",
                "description": "Garantía estándar para productos Mabe",
                "duration_months": 12,
                "brand": brand_objects["Mabe"],
                "active": True
            },
            
            # Electrolux warranties
            {
                "name": "Garantía Electrolux Standard",
                "description": "Cobertura básica para productos Electrolux",
                "duration_months": 12,
                "brand": brand_objects["Electrolux"],
                "active": True
            },
            {
                "name": "Electrolux Comfort Guard",
                "description": "Garantía premium con cobertura extendida",
                "duration_months": 36,
                "brand": brand_objects["Electrolux"],
                "active": True
            },
            
            # Bosch warranties
            {
                "name": "Garantía Bosch",
                "description": "Garantía europea con estándares de alta calidad",
                "duration_months": 24,
                "brand": brand_objects["Bosch"],
                "active": True
            },
            
            # GE warranties
            {
                "name": "GE Appliance Guarantee",
                "description": "Garantía americana para todos los productos GE",
                "duration_months": 12,
                "brand": brand_objects["General Electric"],
                "active": True
            },
            
            # Other brands with standard warranties
            {
                "name": "Garantía Frigidaire",
                "description": "Cobertura estándar para productos Frigidaire",
                "duration_months": 12,
                "brand": brand_objects["Frigidaire"],
                "active": True
            },
            {
                "name": "Garantía Haier",
                "description": "Cobertura básica para electrodomésticos Haier",
                "duration_months": 12,
                "brand": brand_objects["Haier"],
                "active": True
            },
            {
                "name": "Garantía Sony",
                "description": "Garantía oficial Sony para productos electrónicos",
                "duration_months": 12,
                "brand": brand_objects["Sony"],
                "active": True
            },
            {
                "name": "Garantía Panasonic",
                "description": "Cobertura estándar para electrodomésticos Panasonic",
                "duration_months": 12,
                "brand": brand_objects["Panasonic"],
                "active": True
            },
            {
                "name": "Garantía Philips",
                "description": "Garantía oficial para productos Philips",
                "duration_months": 24,
                "brand": brand_objects["Philips"],
                "active": True
            },
            {
                "name": "Garantía Oster",
                "description": "Garantía para electrodomésticos pequeños Oster",
                "duration_months": 12,
                "brand": brand_objects["Oster"],
                "active": True
            },
            {
                "name": "Garantía Black & Decker",
                "description": "Garantía estándar para productos Black & Decker",
                "duration_months": 24,
                "brand": brand_objects["Black & Decker"],
                "active": True
            },
            {
                "name": "Garantía Hamilton Beach",
                "description": "Cobertura para electrodomésticos de cocina Hamilton Beach",
                "duration_months": 12,
                "brand": brand_objects["Hamilton Beach"],
                "active": True
            },
        ]
        
        for warranty_data in warranties:
            warranty = Warranty.objects.create(**warranty_data)
            self.stdout.write(f'Created warranty: {warranty.name} for {warranty.brand.name}')
        
        self.stdout.write(self.style.SUCCESS('Successfully populated the database with appliance data!'))
        self.stdout.write(f'Created {len(categories)} categories')
        self.stdout.write(f'Created {len(brands)} brands')
        self.stdout.write(f'Created {len(warranties)} warranties')