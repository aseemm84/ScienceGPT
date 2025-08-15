"""
Curriculum Data for ScienceGPT
Manages NCERT curriculum data and structure for Grades 1-12 using a class-based approach.
"""

class CurriculumData:
    """Manages curriculum data for different grades and subjects."""

    def __init__(self):
        """
        Initialize curriculum data.
        The main curriculum is stored in a nested dictionary for easy access and management.
        Structure: {grade: {subject: [topics]}}
        """
        self.languages = [
            "English", "Hindi", "Marathi", "Gujarati", "Tamil",
            "Kannada", "Telugu", "Malayalam", "Bengali", "Punjabi"
        ]

        # The single, comprehensive curriculum dictionary for all grades.
        self.curriculum = {
            1: {
                "General Science": ["Living and Non-living Things", "Plants", "Animals", "Human Body", "Water", "Air"],
                "Environmental Studies": ["Family and Community", "Plants Around Us", "Animal Habitats", "Water Sources"]
            },
            2: {
                "General Science": ["Food and Nutrition", "Weather", "Light and Shadow", "Sound", "Materials"],
                "Environmental Studies": ["Travel and Transport", "Our Environment", "Pollution", "Natural Resources"]
            },
            3: {
                "General Science": ["Motion", "Simple Machines", "Safety", "Human Body Systems"],
                "Environmental Studies": ["Weather and Climate", "Rocks and Minerals", "Soil"]
            },
            4: {
                "General Science": ["Force, Work, and Energy", "States of Matter", "Adaptations in Animals"],
                "Environmental Studies": ["Our Environment and Pollution", "Conservation"]
            },
            5: {
                "General Science": ["The Circulatory System", "The Nervous System", "Simple Machines", "Light and Shadows"],
                "Environmental Studies": ["Natural Disasters", "Agriculture"]
            },
            6: {
                "Physics": ["Motion and Measurement of Distances", "Light, Shadows and Reflections", "Electricity and Circuits"],
                "Chemistry": ["Sorting Materials into Groups", "Separation of Substances", "Changes Around Us"],
                "Biology": ["Components of Food", "Getting to Know Plants", "Body Movements", "The Living Organisms and Their Surroundings"]
            },
            7: {
                "Physics": ["Heat", "Motion and Time", "Electric Current and its Effects"],
                "Chemistry": ["Acids, Bases, and Salts", "Physical and Chemical Changes"],
                "Biology": ["Nutrition in Plants and Animals", "Fibre to Fabric", "Weather, Climate and Adaptations", "Respiration in Organisms", "Transportation in Animals and Plants"]
            },
            8: {
                "Physics": ["Force and Pressure", "Friction", "Sound", "Chemical Effects of Electric Current", "Some Natural Phenomena", "Light"],
                "Chemistry": ["Synthetic Fibres and Plastics", "Materials: Metals and Non-Metals", "Coal and Petroleum", "Combustion and Flame"],
                "Biology": ["Crop Production and Management", "Microorganisms: Friend and Foe", "Conservation of Plants and Animals", "Cell - Structure and Functions", "Reproduction in Animals"]
            },
            9: {
                "Physics": ["Motion", "Force and Laws of Motion", "Gravitation", "Work and Energy", "Sound"],
                "Chemistry": ["Matter in Our Surroundings", "Is Matter Around Us Pure?", "Atoms and Molecules", "Structure of the Atom"],
                "Biology": ["The Fundamental Unit of Life", "Tissues", "Diversity in Living Organisms", "Why Do We Fall Ill?", "Natural Resources"]
            },
            10: {
                "Physics": ["Light – Reflection and Refraction", "The Human Eye and the Colourful World", "Electricity", "Magnetic Effects of Electric Current", "Sources of Energy"],
                "Chemistry": ["Chemical Reactions and Equations", "Acids, Bases and Salts", "Metals and Non-Metals", "Carbon and its Compounds", "Periodic Classification of Elements"],
                "Biology": ["Life Processes", "Control and Coordination", "How do Organisms Reproduce?", "Heredity and Evolution", "Our Environment"]
            },
            11: {
                "Physics": ["Units and Measurement", "Motion in a Straight Line", "Motion in a Plane", "Laws of Motion", "Work, Energy and Power", "System of Particles and Rotational Motion", "Gravitation", "Mechanical Properties of Solids", "Mechanical Properties of Fluids", "Thermal Properties of Matter", "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves"],
                "Chemistry": ["Some Basic Concepts of Chemistry", "Structure of Atom", "Classification of Elements and Periodicity in Properties", "Chemical Bonding and Molecular Structure", "States of Matter", "Thermodynamics", "Equilibrium", "Redox Reactions", "Hydrogen", "The s-Block Elements", "The p-Block Elements", "Organic Chemistry – Some Basic Principles and Techniques", "Hydrocarbons", "Environmental Chemistry"],
                "Biology": ["The Living World", "Biological Classification", "Plant Kingdom", "Animal Kingdom", "Morphology of Flowering Plants", "Anatomy of Flowering Plants", "Structural Organisation in Animals", "Cell: The Unit of Life", "Biomolecules", "Cell Cycle and Cell Division", "Transport in Plants", "Mineral Nutrition", "Photosynthesis in Higher Plants", "Respiration in Plants", "Plant Growth and Development", "Digestion and Absorption", "Breathing and Exchange of Gases", "Body Fluids and Circulation", "Excretory Products and their Elimination", "Locomotion and Movement", "Neural Control and Coordination", "Chemical Coordination and Integration"]
            },
            12: {
                "Physics": ["Electric Charges and Fields", "Electrostatic Potential and Capacitance", "Current Electricity", "Moving Charges and Magnetism", "Magnetism and Matter", "Electromagnetic Induction", "Alternating Current", "Electromagnetic Waves", "Ray Optics and Optical Instruments", "Wave Optics", "Dual Nature of Radiation and Matter", "Atoms", "Nuclei", "Semiconductor Electronics: Materials, Devices and Simple Circuits", "Particle Physics", "Quantum Field Theory"],
                "Chemistry": ["The Solid State", "Solutions", "Electrochemistry", "Chemical Kinetics", "Surface Chemistry", "General Principles and Processes of Isolation of Elements", "The p-Block Elements", "The d-and f-Block Elements", "Coordination Compounds", "Haloalkanes and Haloarenes", "Alcohols, Phenols and Ethers", "Aldehydes, Ketones and Carboxylic Acids", "Amines", "Biomolecules", "Polymers", "Chemistry in Everyday Life"],
                "Biology": ["Reproduction in Organisms", "Sexual Reproduction in Flowering Plants", "Human Reproduction", "Reproductive Health", "Principles of Inheritance and Variation", "Molecular Basis of Inheritance", "Evolution", "Human Health and Disease", "Strategies for Enhancement in Food Production", "Microbes in Human Welfare", "Biotechnology: Principles and Processes", "Biotechnology and its Applications", "Organisms and Populations", "Ecosystem", "Biodiversity and Conservation", "Environmental Issues"]
            }
        }

    def get_languages(self):
        """Get list of supported languages."""
        return self.languages

    def get_all_grades(self):
        """Get a list of all available grades from the curriculum."""
        return list(self.curriculum.keys())

    def get_subjects_for_grade(self, grade: int):
        """Get subjects available for a specific grade."""
        return list(self.curriculum.get(grade, {}).keys())

    def get_topics_for_grade_subject(self, grade: int, subject: str):
        """Get topics for a specific grade and subject."""
        return self.curriculum.get(grade, {}).get(subject, [])

    def is_valid_combination(self, grade: int, subject: str):
        """Check if the grade-subject combination is valid."""
        return subject in self.get_subjects_for_grade(grade)
