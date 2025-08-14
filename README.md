# ScienceGPT - AI-Powered Science Learning Tool

ScienceGPT is an interactive science education platform designed specifically for Indian students in grades 1-8. It follows the NCERT curriculum and uses AI to provide personalized learning experiences with gamification elements.

## 🌟 Features

### 🎓 Educational Features
* **Grade-Specific Curriculum (1-12)**: Covers a wide range of topics in Physics, Chemistry, and Biology tailored for each grade.
* **Multi-language Support**: Learn in English, Hindi, and several other regional Indian languages.
* **Interactive Explanations**: Get clear, age-appropriate answers to your science questions.
* **AI-Powered Video Recommendations**: Finds and summarizes relevant YouTube videos for visual learning.
* **Gamification**: Earn points, unlock badges, and maintain a learning streak to make learning fun.
* **Daily Challenges**: Tackle new facts and questions every day to build a habit.
* **Progress Tracking**: Monitor your learning journey across different subjects and topics.

### 🎮 Gamification Elements
- **Points System**: Earn points for asking questions, completing challenges, and daily engagement
- **Achievement Badges**: Unlock badges for various learning milestones
- **Learning Streaks**: Track consecutive days of learning
- **Daily Challenges**: Fun science facts and quiz questions every day
- **Progress Tracking**: Monitor learning progress across subjects and topics

### 🔧 Technical Features
- **Clean Architecture**: Modular code structure with separated frontend and backend
- **Secure API Integration**: Uses Streamlit secrets for secure API key management
- **Responsive Design**: Works well on different screen sizes
- **Session Management**: Tracks user progress and preferences

## 📁 Project Structure

```
ScienceGPT/
├── frontend.py                 # Main Streamlit application
├── backend_code/              # Backend logic and data processing
│   ├── __init__.py
│   ├── llm_handler.py         # Groq API integration and LLM management
│   ├── curriculum_data.py     # NCERT curriculum data and management
│   ├── gamification.py        # Points, badges, and achievement system
│   └── student_progress.py    # Progress tracking and analytics
├── frontend_components/       # UI components and interface logic
│   ├── __init__.py
│   ├── sidebar.py            # Grade, language, subject selection sidebar
│   ├── main_interface.py     # Main chat interface and question handling
│   ├── gamification_ui.py    # Gamification display components
│   └── daily_challenge.py    # Daily challenge and fun facts
├── .streamlit/
│   └── secrets.toml          # Configuration secrets (not included in repo)
├── requirements.txt          # Python dependencies
└── README.md                # This file
```


## 🛠️ Technical Details

### Backend Components

#### LLM Handler (`llm_handler.py`)
- Manages Groq API integration
- Generates contextual responses based on grade, subject, and language
- Creates dynamic question suggestions
- Handles daily challenge generation

#### Curriculum Data (`curriculum_data.py`)
- Complete NCERT science curriculum for grades 1-12
- Subject and topic organization by grade level
- Multi-language support framework
- Structured data access methods

#### Gamification System (`gamification.py`)
- Points and rewards system
- Badge definitions and criteria
- Streak tracking and maintenance
- Achievement progress calculation

#### Student Progress (`student_progress.py`)
- Learning session tracking
- Question and topic analytics
- Performance metrics calculation
- Progress data export capabilities

### Frontend Components

#### Main Interface (`main_interface.py`)
- Chat-based question answering interface
- Dynamic suggestion generation and display
- Chat history management
- Progress update handling

#### Sidebar (`sidebar.py`)
- Grade, language, and subject selection
- Settings application and validation
- Progress summary display
- User preference management

#### Gamification UI (`gamification_ui.py`)
- Points, badges, and achievement display
- Progress bars and level indicators
- Badge notification system
- Leaderboard placeholder

#### Daily Challenge (`daily_challenge.py`)
- Daily science fact and quiz generation
- Interactive challenge completion
- Bonus points and engagement rewards
- Related content suggestions


## 🔐 Security Considerations

- API keys are stored securely using Streamlit secrets
- No sensitive data is logged or stored permanently
- User sessions are managed locally without external storage
- Input validation prevents malicious prompts

## 📊 Performance Optimization

- Caching for suggestion generation
- Session state management for user data
- Modular loading of components
- Efficient API call management


## 🐛 Known Issues & Limitations

- Requires active internet connection for AI responses
- LLM response quality depends on Groq API availability
- Limited to text-based interactions (no image processing)
- Progress data is session-based (resets on browser refresh)
- Free Groq API is used, so API calls are constrained to token per minute and per day limits

## 🙏 Acknowledgments

- **NCERT**: For the comprehensive curriculum guidelines
- **Groq**: For the powerful free AI API
- **Streamlit**: For the excellent web app framework
- **Indian Education System**: For inspiring this educational tool
- **Open Source Community**: For the various libraries and tools used

---

**Built with ❤️ by Aseem Mehrotra for Indian students and educators**

*Empowering the next generation of scientists and innovators through AI-powered education*


<https://www.linkedin.com/in/aseem-mehrotra/>
