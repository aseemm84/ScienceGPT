"""
Curriculum Data Management for ScienceGPT
Contains NCERT science curriculum data for grades 1-8
"""

from typing import Dict, List
import json

class CurriculumData:
    """Manages curriculum data and subject/topic mappings"""

    def __init__(self):
        self.curriculum_data = self._load_curriculum_data()
        self.languages = [
            "English", "Hindi", "Marathi", "Gujarati", "Tamil", 
            "Kannada", "Telugu", "Malayalam", "Bengali", "Punjabi"
        ]

    def _load_curriculum_data(self) -> Dict:
        """Load comprehensive NCERT curriculum data"""
        return {
            # Grades 1-2: Basic observation and awareness
            1: {
                "subjects": ["General Science"],
                "topics": {
                    "General Science": [
                        "Living and Non-living Things",
                        "Our Body Parts",
                        "Animals Around Us",
                        "Plants Around Us",
                        "Food We Eat",
                        "Water and Its Uses",
                        "Air Around Us",
                        "Day and Night",
                        "Weather and Seasons"
                    ]
                }
            },

            2: {
                "subjects": ["General Science"],
                "topics": {
                    "General Science": [
                        "Living and Non-living Things",
                        "Human Body and Health",
                        "Animals and Their Homes",
                        "Plants and Trees",
                        "Food and Nutrition",
                        "Water in Daily Life",
                        "Air and Wind",
                        "Sun, Moon and Stars",
                        "Seasons and Weather",
                        "Safety and First Aid"
                    ]
                }
            },

            # Grade 3: Introduction to basic concepts
            3: {
                "subjects": ["General Science"],
                "topics": {
                    "General Science": [
                        "Components of Food",
                        "Sorting Materials into Groups",
                        "Getting to Know Plants",
                        "Animals and Their Characteristics",
                        "Our Environment",
                        "Simple Machines in Daily Life",
                        "Light and Shadow",
                        "Sound Around Us",
                        "Force and Motion"
                    ]
                }
            },

            # Grade 4: Deeper exploration
            4: {
                "subjects": ["General Science"],
                "topics": {
                    "General Science": [
                        "Separation of Substances",
                        "Body Movements",
                        "Living Organisms and Their Surroundings",
                        "Motion and Types of Motion",
                        "Water Cycle",
                        "Air and Its Properties",
                        "Rocks and Minerals",
                        "Weather and Climate",
                        "Natural Resources"
                    ]
                }
            },

            # Grade 5: Foundation concepts
            5: {
                "subjects": ["General Science"],
                "topics": {
                    "General Science": [
                        "Light, Shadows and Reflections",
                        "Electricity and Circuits",
                        "Fun with Magnets",
                        "Air Around Us",
                        "Natural Phenomena",
                        "Natural Resources",
                        "Waste Management",
                        "Health and Hygiene",
                        "Measurement and Motion"
                    ]
                }
            },

            # Grade 6: Subject separation begins
            6: {
                "subjects": ["Biology", "Physics", "Chemistry"],
                "topics": {
                    "Biology": [
                        "Food: Where Does It Come From?",
                        "Components of Food",
                        "Getting to Know Plants",
                        "Body Movements",
                        "The Living Organisms - Characteristics and Habitats",
                        "Garbage In, Garbage Out"
                    ],
                    "Physics": [
                        "Motion and Measurement of Distances",
                        "Light, Shadows and Reflections",
                        "Electricity and Circuits",
                        "Fun with Magnets"
                    ],
                    "Chemistry": [
                        "Sorting Materials into Groups",
                        "Separation of Substances",
                        "Air Around Us"
                    ]
                }
            },

            # Grade 7: Expanded concepts
            7: {
                "subjects": ["Biology", "Physics", "Chemistry"],
                "topics": {
                    "Biology": [
                        "Nutrition in Plants and Animals",
                        "Respiration in Organisms",
                        "Transportation in Animals and Plants",
                        "Reproduction in Plants",
                        "Weather, Climate and Adaptations"
                    ],
                    "Physics": [
                        "Heat and Temperature",
                        "Motion and Time",
                        "Electric Current and Its Effects",
                        "Light"
                    ],
                    "Chemistry": [
                        "Acids, Bases and Salts",
                        "Physical and Chemical Changes",
                        "Fibres and Plastics",
                        "Water: A Precious Resource"
                    ]
                }
            },

            # Grade 8: Advanced concepts
            8: {
                "subjects": ["Biology", "Physics", "Chemistry"],
                "topics": {
                    "Biology": [
                        "Crop Production and Management",
                        "Microorganisms: Friend and Foe",
                        "Cell Structure and Functions",
                        "Reproduction in Animals",
                        "Reaching the Age of Adolescence"
                    ],
                    "Physics": [
                        "Force and Pressure",
                        "Friction",
                        "Sound",
                        "Chemical Effects of Electric Current",
                        "Some Natural Phenomena"
                    ],
                    "Chemistry": [
                        "Synthetic Fibres and Plastics",
                        "Materials: Metals and Non-metals",
                        "Coal and Petroleum",
                        "Combustion and Flame",
                        "Pollution of Air and Water"
                    ]
                }
            }
        }

    def get_grades(self) -> List[int]:
        """Get list of available grades"""
        return list(self.curriculum_data.keys())

    def get_subjects(self, grade: int) -> List[str]:
        """Get subjects for a specific grade"""
        return self.curriculum_data.get(grade, {}).get("subjects", ["General Science"])

    def get_topics(self, grade: int, subject: str) -> List[str]:
        """Get topics for a specific grade and subject"""
        grade_data = self.curriculum_data.get(grade, {})
        topics_data = grade_data.get("topics", {})
        return topics_data.get(subject, [])

    def get_languages(self) -> List[str]:
        """Get available languages"""
        return self.languages

    def get_curriculum_info(self, grade: int, subject: str = None) -> Dict:
        """Get comprehensive curriculum information"""
        info = {
            "grade": grade,
            "subjects": self.get_subjects(grade),
            "all_topics": {}
        }

        if subject:
            info["selected_subject"] = subject
            info["topics"] = self.get_topics(grade, subject)
        else:
            # Get all topics for all subjects
            for subj in info["subjects"]:
                info["all_topics"][subj] = self.get_topics(grade, subj)

        return info
