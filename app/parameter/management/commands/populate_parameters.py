from django.core.management.base import BaseCommand
from app.parameter.models import Country, State, City

class Command(BaseCommand):
    help = 'Populate database with countries, states and cities of South America'

    def handle(self, *args, **options):
        self.stdout.write("Starting to populate location parameters...")
        self.populate_countries()
        self.stdout.write(self.style.SUCCESS('Successfully populated all countries, states and cities'))

    def populate_countries(self):
        # BOLIVIA
        bolivia = self._create_country("Bolivia", "BO")
        self.stdout.write("Populating Bolivia...")
        self._create_bolivia_data(bolivia)
        
        # ARGENTINA
        argentina = self._create_country("Argentina", "AR")
        self.stdout.write("Populating Argentina...")
        self._create_argentina_data(argentina)
        
        # BRASIL
        brasil = self._create_country("Brasil", "BR")
        self.stdout.write("Populating Brasil...")
        self._create_brasil_data(brasil)
        
        # CHILE
        chile = self._create_country("Chile", "CL")
        self.stdout.write("Populating Chile...")
        self._create_chile_data(chile)
        
        # COLOMBIA
        colombia = self._create_country("Colombia", "CO")
        self.stdout.write("Populating Colombia...")
        self._create_colombia_data(colombia)
        
        # PERÚ
        peru = self._create_country("Perú", "PE")
        self.stdout.write("Populating Perú...")
        self._create_peru_data(peru)
        
        # ECUADOR
        ecuador = self._create_country("Ecuador", "EC")
        self.stdout.write("Populating Ecuador...")
        self._create_ecuador_data(ecuador)
        
        # PARAGUAY
        paraguay = self._create_country("Paraguay", "PY")
        self.stdout.write("Populating Paraguay...")
        self._create_paraguay_data(paraguay)
        
        # URUGUAY
        uruguay = self._create_country("Uruguay", "UY")
        self.stdout.write("Populating Uruguay...")
        self._create_uruguay_data(uruguay)
        
        # VENEZUELA
        venezuela = self._create_country("Venezuela", "VE")
        self.stdout.write("Populating Venezuela...")
        self._create_venezuela_data(venezuela)

    def _create_country(self, name, code):
        country, _ = Country.objects.get_or_create(name=name, code=code)
        return country
        
    def _create_state(self, name, code, country):
        state, _ = State.objects.get_or_create(name=name, code=code, country=country)
        return state
        
    def _create_cities(self, state, city_names):
        for city_name in city_names:
            City.objects.get_or_create(name=city_name, state=state)

    def _create_bolivia_data(self, bolivia):
        # La Paz
        la_paz = self._create_state("La Paz", "LP", bolivia)
        self._create_cities(la_paz, [
            "La Paz", "El Alto", "Viacha", "Achacachi", "Copacabana", 
            "Coroico", "Desaguadero", "Caranavi", "Patacamaya", "Sorata"
        ])
        
        # Cochabamba
        cochabamba = self._create_state("Cochabamba", "CB", bolivia)
        self._create_cities(cochabamba, [
            "Cochabamba", "Quillacollo", "Sacaba", "Punata", "Cliza", 
            "Tiquipaya", "Vinto", "Colcapirhua", "Sipe Sipe", "Tarata"
        ])
        
        # Santa Cruz
        santa_cruz = self._create_state("Santa Cruz", "SC", bolivia)
        self._create_cities(santa_cruz, [
            "Santa Cruz de la Sierra", "Montero", "Warnes", "La Guardia", "Cotoca", 
            "Mineros", "Portachuelo", "Camiri", "Puerto Suárez", "San Ignacio de Velasco"
        ])
        
        # Chuquisaca
        chuquisaca = self._create_state("Chuquisaca", "CH", bolivia)
        self._create_cities(chuquisaca, [
            "Sucre", "Camargo", "Monteagudo", "Villa Serrano", "Padilla", 
            "Tarabuco", "Zudáñez", "Villa Abecia", "Incahuasi", "Culpina"
        ])
        
        # Oruro
        oruro = self._create_state("Oruro", "OR", bolivia)
        self._create_cities(oruro, [
            "Oruro", "Challapata", "Huanuni", "Caracollo", "Machacamarca", 
            "Poopó", "Eucaliptus", "Sabaya", "Toledo", "Huachacalla"
        ])
        
        # Potosí
        potosi = self._create_state("Potosí", "PT", bolivia)
        self._create_cities(potosi, [
            "Potosí", "Villazón", "Tupiza", "Uyuni", "Llallagua", 
            "Uncía", "Colquechaca", "Betanzos", "Cotagaita", "Villazon"
        ])
        
        # Tarija
        tarija = self._create_state("Tarija", "TJ", bolivia)
        self._create_cities(tarija, [
            "Tarija", "Yacuiba", "Villamontes", "Bermejo", "Entre Ríos", 
            "Caraparí", "San Lorenzo", "Padcaya", "El Puente", "Concepción"
        ])
        
        # Beni
        beni = self._create_state("Beni", "BN", bolivia)
        self._create_cities(beni, [
            "Trinidad", "Riberalta", "Guayaramerín", "San Borja", "Santa Ana del Yacuma", 
            "San Ignacio de Moxos", "Rurrenabaque", "San Joaquín", "Magdalena", "San Ramón"
        ])
        
        # Pando
        pando = self._create_state("Pando", "PD", bolivia)
        self._create_cities(pando, [
            "Cobija", "Porvenir", "Puerto Rico", "Filadelfia", "Bella Flor", 
            "Santa Rosa del Abuná", "Ingavi", "Nueva Esperanza", "Villa Nueva", "Bolpebra"
        ])

    def _create_argentina_data(self, argentina):
        # Buenos Aires
        buenos_aires = self._create_state("Buenos Aires", "BA", argentina)
        self._create_cities(buenos_aires, [
            "Buenos Aires", "La Plata", "Mar del Plata", "Quilmes", "Lanús", 
            "Bahía Blanca", "Pilar", "San Isidro", "Tigre", "Tandil"
        ])
        
        # Córdoba
        cordoba = self._create_state("Córdoba", "CBA", argentina)
        self._create_cities(cordoba, [
            "Córdoba", "Villa María", "Río Cuarto", "San Francisco", "Alta Gracia",
            "Villa Carlos Paz", "Bell Ville", "Río Tercero", "Jesús María", "Cosquín"
        ])
        
        # Santa Fe
        santa_fe = self._create_state("Santa Fe", "SF", argentina)
        self._create_cities(santa_fe, [
            "Santa Fe", "Rosario", "Venado Tuerto", "Rafaela", "Reconquista",
            "Santo Tomé", "Villa Gobernador Gálvez", "San Lorenzo", "Esperanza", "Casilda"
        ])
        
        # Mendoza
        mendoza = self._create_state("Mendoza", "MZA", argentina)
        self._create_cities(mendoza, [
            "Mendoza", "San Rafael", "Godoy Cruz", "Guaymallén", "Las Heras",
            "Luján de Cuyo", "Maipú", "Rivadavia", "Junín", "Tunuyán"
        ])
        
        # Tucumán
        tucuman = self._create_state("Tucumán", "TUC", argentina)
        self._create_cities(tucuman, [
            "San Miguel de Tucumán", "Yerba Buena", "Tafí Viejo", "Banda del Río Salí", "Alderetes",
            "Concepción", "Famaillá", "Aguilares", "Monteros", "Simoca"
        ])
        
        # Salta
        salta = self._create_state("Salta", "SAL", argentina)
        self._create_cities(salta, [
            "Salta", "San Ramón de la Nueva Orán", "Tartagal", "General Güemes", "Rosario de la Frontera",
            "Cafayate", "Embarcación", "Metán", "Salvador Mazza", "Joaquín V. González"
        ])
        
        # Entre Ríos
        entre_rios = self._create_state("Entre Ríos", "ER", argentina)
        self._create_cities(entre_rios, [
            "Paraná", "Concordia", "Gualeguaychú", "Concepción del Uruguay", "Gualeguay",
            "Villaguay", "Victoria", "La Paz", "Colón", "Crespo"
        ])

    def _create_brasil_data(self, brasil):
        # São Paulo
        sao_paulo = self._create_state("São Paulo", "SP", brasil)
        self._create_cities(sao_paulo, [
            "São Paulo", "Campinas", "Guarulhos", "São Bernardo do Campo", "Santo André",
            "Santos", "Ribeirão Preto", "Sorocaba", "São José dos Campos", "Osasco"
        ])
        
        # Rio de Janeiro
        rio = self._create_state("Rio de Janeiro", "RJ", brasil)
        self._create_cities(rio, [
            "Rio de Janeiro", "Niterói", "São Gonçalo", "Duque de Caxias", "Nova Iguaçu",
            "Petrópolis", "Volta Redonda", "Campos dos Goytacazes", "Macaé", "Angra dos Reis"
        ])
        
        # Minas Gerais
        minas = self._create_state("Minas Gerais", "MG", brasil)
        self._create_cities(minas, [
            "Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim",
            "Montes Claros", "Ribeirão das Neves", "Uberaba", "Governador Valadares", "Ipatinga"
        ])
        
        # Bahia
        bahia = self._create_state("Bahia", "BA", brasil)
        self._create_cities(bahia, [
            "Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Itabuna",
            "Juazeiro", "Ilhéus", "Lauro de Freitas", "Jequié", "Barreiras"
        ])
        
        # Rio Grande do Sul
        rio_grande = self._create_state("Rio Grande do Sul", "RS", brasil)
        self._create_cities(rio_grande, [
            "Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria",
            "Gravataí", "Viamão", "Novo Hamburgo", "São Leopoldo", "Rio Grande"
        ])

    def _create_chile_data(self, chile):
        # Región Metropolitana
        metropolitana = self._create_state("Región Metropolitana de Santiago", "RMS", chile)
        self._create_cities(metropolitana, [
            "Santiago", "Puente Alto", "Maipú", "La Florida", "Las Condes",
            "Peñalolén", "Pudahuel", "Ñuñoa", "Providencia", "Renca"
        ])
        
        # Valparaíso
        valparaiso = self._create_state("Valparaíso", "VAL", chile)
        self._create_cities(valparaiso, [
            "Valparaíso", "Viña del Mar", "Quilpué", "Villa Alemana", "San Antonio",
            "Quillota", "Concón", "Los Andes", "Limache", "San Felipe"
        ])
        
        # Biobío
        biobio = self._create_state("Biobío", "BIO", chile)
        self._create_cities(biobio, [
            "Concepción", "Talcahuano", "Chillán", "Los Ángeles", "Coronel",
            "San Pedro de la Paz", "Hualpén", "Chiguayante", "Lota", "Tomé"
        ])
        
        # Antofagasta
        antofagasta = self._create_state("Antofagasta", "ANT", chile)
        self._create_cities(antofagasta, [
            "Antofagasta", "Calama", "Tocopilla", "Mejillones", "Taltal",
            "San Pedro de Atacama", "Sierra Gorda", "María Elena", "Ollagüe"
        ])

    def _create_colombia_data(self, colombia):
        # Cundinamarca/Bogotá
        cundinamarca = self._create_state("Cundinamarca", "CUN", colombia)
        self._create_cities(cundinamarca, [
            "Bogotá", "Soacha", "Zipaquirá", "Facatativá", "Chía",
            "Mosquera", "Madrid", "Funza", "Cajicá", "Fusagasugá"
        ])
        
        # Antioquia
        antioquia = self._create_state("Antioquia", "ANT", colombia)
        self._create_cities(antioquia, [
            "Medellín", "Bello", "Itagüí", "Envigado", "Apartadó",
            "Rionegro", "Turbo", "Caucasia", "Copacabana", "Sabaneta"
        ])
        
        # Valle del Cauca
        valle = self._create_state("Valle del Cauca", "VAC", colombia)
        self._create_cities(valle, [
            "Cali", "Buenaventura", "Palmira", "Tuluá", "Buga",
            "Yumbo", "Jamundí", "Cartago", "Florida", "Zarzal"
        ])
        
        # Atlántico
        atlantico = self._create_state("Atlántico", "ATL", colombia)
        self._create_cities(atlantico, [
            "Barranquilla", "Soledad", "Malambo", "Sabanalarga", "Galapa",
            "Baranoa", "Puerto Colombia", "Santo Tomás", "Palmar de Varela", "Sabanagrande"
        ])

    def _create_peru_data(self, peru):
        # Lima
        lima = self._create_state("Lima", "LIM", peru)
        self._create_cities(lima, [
            "Lima", "Callao", "San Juan de Lurigancho", "San Martín de Porres", "Ate",
            "Comas", "Villa El Salvador", "Villa María del Triunfo", "San Juan de Miraflores", "Los Olivos"
        ])
        
        # Arequipa
        arequipa = self._create_state("Arequipa", "AQP", peru)
        self._create_cities(arequipa, [
            "Arequipa", "Camaná", "Mollendo", "Mejía", "Majes",
            "Pedregal", "Yura", "Chivay", "La Joya", "Cotahuasi"
        ])
        
        # La Libertad
        la_libertad = self._create_state("La Libertad", "LAL", peru)
        self._create_cities(la_libertad, [
            "Trujillo", "Chepén", "Pacasmayo", "Guadalupe", "Casa Grande",
            "Huamachuco", "Santiago de Chuco", "Otuzco", "Laredo", "Virú"
        ])
        
        # Cusco
        cusco = self._create_state("Cusco", "CUS", peru)
        self._create_cities(cusco, [
            "Cusco", "Sicuani", "Quillabamba", "Espinar", "Urubamba",
            "Calca", "Yanaoca", "Anta", "Ollantaytambo", "Pisac"
        ])

    def _create_ecuador_data(self, ecuador):
        # Pichincha
        pichincha = self._create_state("Pichincha", "P", ecuador)
        self._create_cities(pichincha, [
            "Quito", "Sangolquí", "Cayambe", "Machachi", "Pedro Vicente Maldonado",
            "San Miguel de los Bancos", "Tabacundo", "Puerto Quito", "Alangasí", "Guayllabamba"
        ])
        
        # Guayas
        guayas = self._create_state("Guayas", "G", ecuador)
        self._create_cities(guayas, [
            "Guayaquil", "Durán", "Samborondón", "Milagro", "Daule",
            "El Triunfo", "Playas", "Naranjal", "Naranjito", "Balzar"
        ])
        
        # Azuay
        azuay = self._create_state("Azuay", "A", ecuador)
        self._create_cities(azuay, [
            "Cuenca", "Gualaceo", "Santa Isabel", "Paute", "Camilo Ponce Enríquez",
            "Sigsig", "Chordeleg", "Girón", "Nabón", "Oña"
        ])
        
        # Manabí
        manabi = self._create_state("Manabí", "M", ecuador)
        self._create_cities(manabi, [
            "Portoviejo", "Manta", "Chone", "Jipijapa", "El Carmen",
            "Bahía de Caráquez", "Pedernales", "Montecristi", "Jaramijó", "Puerto López"
        ])

    def _create_paraguay_data(self, paraguay):
        # Central
        central = self._create_state("Central", "11", paraguay)
        self._create_cities(central, [
            "Asunción", "San Lorenzo", "Lambaré", "Fernando de la Mora", "Luque",
            "Capiatá", "Limpio", "Ñemby", "Villa Elisa", "Mariano Roque Alonso"
        ])
        
        # Alto Paraná
        alto_parana = self._create_state("Alto Paraná", "10", paraguay)
        self._create_cities(alto_parana, [
            "Ciudad del Este", "Presidente Franco", "Hernandarias", "Minga Guazú", "Santa Rita",
            "Juan León Mallorquín", "San Cristóbal", "Naranjal", "Santa Rosa del Monday", "Minga Porá"
        ])
        
        # Itapúa
        itapua = self._create_state("Itapúa", "7", paraguay)
        self._create_cities(itapua, [
            "Encarnación", "Hohenau", "Bella Vista", "Obligado", "Capitán Miranda",
            "Trinidad", "Nueva Alborada", "Jesús", "Coronel Bogado", "Carmen del Paraná"
        ])
        
        # Cordillera
        cordillera = self._create_state("Cordillera", "3", paraguay)
        self._create_cities(cordillera, [
            "Caacupé", "Tobatí", "Atyrá", "Altos", "Emboscada",
            "San Bernardino", "Eusebio Ayala", "Piribebuy", "Itacurubí de la Cordillera", "Valenzuela"
        ])

    def _create_uruguay_data(self, uruguay):
        # Montevideo
        montevideo = self._create_state("Montevideo", "MO", uruguay)
        self._create_cities(montevideo, [
            "Montevideo", "Ciudad de la Costa", "La Paz", "Las Piedras", "Colón",
            "Pando", "Toledo", "Santiago Vázquez", "Pajas Blancas", "Manga"
        ])
        
        # Canelones
        canelones = self._create_state("Canelones", "CA", uruguay)
        self._create_cities(canelones, [
            "Canelones", "Santa Lucía", "Progreso", "Salinas", "Atlántida",
            "La Floresta", "San Ramón", "Tala", "Sauce", "Pando"
        ])
        
        # Maldonado
        maldonado = self._create_state("Maldonado", "MA", uruguay)
        self._create_cities(maldonado, [
            "Maldonado", "Punta del Este", "San Carlos", "Piriápolis", "Pan de Azúcar",
            "Aiguá", "Garzón", "José Ignacio", "La Barra", "Manantiales"
        ])
        
        # Paysandú
        paysandu = self._create_state("Paysandú", "PA", uruguay)
        self._create_cities(paysandu, [
            "Paysandú", "Guichón", "Quebracho", "Tambores", "Lorenzo Geyres",
            "Porvenir", "Piedras Coloradas", "Constancia", "Chapicuy", "Algorta"
        ])

    def _create_venezuela_data(self, venezuela):
        # Distrito Capital
        distrito_capital = self._create_state("Distrito Capital", "A", venezuela)
        self._create_cities(distrito_capital, [
            "Caracas", "El Junquito", "Antimano", "La Vega", "Macarao",
            "Caricuao", "El Valle", "Coche", "El Paraíso", "Chacao"
        ])
        
        # Miranda
        miranda = self._create_state("Miranda", "M", venezuela)
        self._create_cities(miranda, [
            "Los Teques", "Guarenas", "Guatire", "Petare", "Santa Teresa del Tuy",
            "Charallave", "Ocumare del Tuy", "San Antonio de los Altos", "Carrizal", "Baruta"
        ])
        
        # Zulia
        zulia = self._create_state("Zulia", "V", venezuela)
        self._create_cities(zulia, [
            "Maracaibo", "Cabimas", "Ciudad Ojeda", "Machiques", "Santa Rita",
            "El Moján", "San Carlos del Zulia", "La Concepción", "La Cañada de Urdaneta", "Villa del Rosario"
        ])
        
        # Carabobo
        carabobo = self._create_state("Carabobo", "G", venezuela)
        self._create_cities(carabobo, [
            "Valencia", "Puerto Cabello", "Guacara", "Morón", "Los Guayos",
            "Tocuyito", "Mariara", "Güigüe", "San Diego", "Naguanagua"
        ])