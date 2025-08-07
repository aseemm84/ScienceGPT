"""
Curriculum Data for ScienceGPT
Manages NCERT curriculum data and structure
"""

class CurriculumData:
    """Manages curriculum data for different grades and subjects"""

    def __init__(self):
        """Initialize curriculum data"""
        self.languages = [
            "English", "Hindi", "Marathi", "Gujarati", "Tamil", 
            "Kannada", "Telugu", "Malayalam", "Bengali", "Punjabi"
        ]

        self.grade_subjects = {
            1: ["General Science", "Environmental Studies"],
            2: ["General Science", "Environmental Studies"], 
            3: ["General Science", "Environmental Studies"],
            4: ["General Science", "Environmental Studies"],
            5: ["General Science", "Environmental Studies"],
            6: ["Science", "Physics", "Chemistry", "Biology"],
            7: ["Science", "Physics", "Chemistry", "Biology"],
            8: ["Science", "Physics", "Chemistry", "Biology"]
        }

        self.topics = {
            "General Science": [
                "Living and Non-living Things", "Plants", "Animals", "Human Body",
                "Food and Nutrition", "Water", "Air", "Weather", "Light and Shadow",
                "Sound", "Motion", "Simple Machines", "Materials", "Safety"
            ],
            "Environmental Studies": [
                "Family and Community", "Plants Around Us", "Animal Habitats", 
                "Water Sources", "Travel and Transport", "Our Environment",
                "Pollution", "Natural Resources", "Weather and Climate"
            ],
            "Science": [
                "Matter", "Living World", "Natural Phenomena", "Natural Resources",
                "Energy", "Motion", "Forces", "Light", "Sound", "Heat"
            ],
            "Physics": [
                "Motion and Forces", "Light", "Sound", "Heat", "Electricity",
                "Magnetism", "Energy", "Waves", "Matter and its Properties"
            ],
            "Chemistry": [
                "Matter and its States", "Elements and Compounds", "Acids and Bases",
                "Metals and Non-metals", "Chemical Reactions", "Air and Water",
                "Carbon Compounds", "Periodic Table"
            ],
            "Biology": [
                "Living Organisms", "Plant Life", "Animal Life", "Human Body Systems",
                "Nutrition", "Respiration", "Life Processes", "Heredity",
                "Evolution", "Ecosystem", "Biodiversity"
            ]
        }

    def get_languages(self):
        """Get list of supported languages"""
        return self.languages

    def get_subjects_for_grade(self, grade: int):
        """Get subjects available for a specific grade"""
        return self.grade_subjects.get(grade, ["General Science"])

    def get_topics_for_grade_subject(self, grade: int, subject: str):
        """Get topics for a specific grade and subject"""
        if subject in self.topics:
            return self.topics[subject]
        return ["Basic Concepts", "Advanced Topics", "Applications"]

    def get_all_grades(self):
        """Get list of all available grades"""
        return list(range(1, 9))

    def is_valid_combination(self, grade: int, subject: str):
        """Check if grade-subject combination is valid"""
        valid_subjects = self.get_subjects_for_grade(grade)
        return subject in valid_subjects
