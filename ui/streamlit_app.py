# -*- coding: utf-8 -*-
"""
Streamlit UI for YouTube Data Analyzer

A comprehensive web interface for YouTube data analysis with AI-powered content generation.
"""

import streamlit as st
import pandas as pd
import json
import io
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import application modules
try:
    from core.youtube_api import YouTubeAPI
    from core.llm_integration import LLMIntegration
    from core.image_generation import ImageGeneration
    from core.preset_manager import PresetManager
    from core.data_filter import DataFilter
    from core.export_manager import ExportManager
    from core.voice_input import VoiceInput
    from database.db_manager import DatabaseManager
    from utils.config_manager import ConfigManager
    from utils.error_handler import get_error_handler, create_user_friendly_message
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="YouTube Data Analyzer",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #FF0000;
    text-align: center;
    margin-bottom: 2rem;
}
.section-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
    margin-top: 2rem;
    margin-bottom: 1rem;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.success-message {
    background-color: #d4edda;
    color: #155724;
    padding: 0.75rem;
    border-radius: 0.25rem;
    border: 1px solid #c3e6cb;
}
.error-message {
    background-color: #f8d7da;
    color: #721c24;
    padding: 0.75rem;
    border-radius: 0.25rem;
    border: 1px solid #f5c6cb;
}
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    """
    Main Streamlit application class.
    """
    
    def __init__(self):
        """
        Initialize the Streamlit application.
        """
        self.error_handler = get_error_handler()
        self.config_manager = None
        self.youtube_api = None
        self.llm_integration = None
        self.image_generation = None
        self.preset_manager = None
        self.data_filter = None
        self.export_manager = None
        self.voice_input = None
        self.db_manager = None
        
        self._initialize_session_state()
        self._load_configuration()
    
    def _initialize_session_state(self):
        """
        Initialize Streamlit session state variables.
        """
        if 'initialized' not in st.session_state:
            st.session_state.initialized = False
            st.session_state.videos_data = []
            st.session_state.current_video = None
            st.session_state.generated_content = {}
            st.session_state.export_history = []
            st.session_state.voice_enabled = False
    
    def _load_configuration(self):
        """
        Load application configuration.
        """
        try:
            self.config_manager = ConfigManager()
            config = self.config_manager.get_config()
            
            if config:
                self._initialize_components(config)
                st.session_state.initialized = True
            else:
                st.error("Failed to load configuration. Please check your .env file.")
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Configuration error: {error_msg}")
    
    def _initialize_components(self, config):
        """
        Initialize application components.
        
        Args:
            config: Application configuration
        """
        try:
            # Initialize database
            self.db_manager = DatabaseManager(config.database.path)
            
            # Initialize core components
            if config.youtube.api_key:
                self.youtube_api = YouTubeAPI(config.youtube.api_key)
            
            self.llm_integration = LLMIntegration(config)
            self.image_generation = ImageGeneration(config)
            self.preset_manager = PresetManager(self.db_manager)
            self.data_filter = DataFilter()
            self.export_manager = ExportManager()
            
            # Initialize voice input if available
            try:
                self.voice_input = VoiceInput()
                st.session_state.voice_enabled = True
            except Exception:
                st.session_state.voice_enabled = False
                
        except Exception as e:
            self.error_handler.handle_error(e, context={"component": "initialization"})
            st.error(f"Failed to initialize components: {create_user_friendly_message(e)}")
    
    def run(self):
        """
        Run the Streamlit application.
        """
        # Header
        st.markdown('<h1 class="main-header">🎥 YouTube Data Analyzer</h1>', unsafe_allow_html=True)
        
        if not st.session_state.initialized:
            self._show_configuration_page()
            return
        
        # Sidebar navigation
        page = self._render_sidebar()
        
        # Main content area
        if page == "Data Collection":
            self._render_data_collection_page()
        elif page == "Data Analysis":
            self._render_data_analysis_page()
        elif page == "AI Generation":
            self._render_ai_generation_page()
        elif page == "Export & Reports":
            self._render_export_page()
        elif page == "Settings":
            self._render_settings_page()
    
    def _show_configuration_page(self):
        """
        Show configuration setup page.
        """
        st.markdown('<h2 class="section-header">⚙️ Configuration Setup</h2>', unsafe_allow_html=True)
        
        st.warning("Please configure the application before proceeding.")
        
        with st.expander("Configuration Help", expanded=True):
            st.markdown("""
            **Required Configuration:**
            1. Create a `.env` file in the project root
            2. Add your YouTube API key: `YOUTUBE_API_KEY=your_key_here`
            3. Configure LLM providers (optional)
            4. Set up image generation models (optional)
            
            **Example .env file:**
            ```
            YOUTUBE_API_KEY=your_youtube_api_key
            OPENAI_API_KEY=your_openai_key
            ANTHROPIC_API_KEY=your_anthropic_key
            ```
            """)
        
        if st.button("Reload Configuration"):
            st.rerun()
    
    def _render_sidebar(self) -> str:
        """
        Render the sidebar navigation.
        
        Returns:
            str: Selected page
        """
        with st.sidebar:
            st.markdown('<h2 class="section-header">📋 Navigation</h2>', unsafe_allow_html=True)
            
            page = st.selectbox(
                "Select Page",
                ["Data Collection", "Data Analysis", "AI Generation", "Export & Reports", "Settings"]
            )
            
            st.markdown("---")
            
            # Quick stats
            if st.session_state.videos_data:
                st.markdown('<h3 class="section-header">📊 Quick Stats</h3>', unsafe_allow_html=True)
                st.metric("Total Videos", len(st.session_state.videos_data))
                
                if st.session_state.videos_data:
                    total_views = sum(video.get('view_count', 0) for video in st.session_state.videos_data)
                    st.metric("Total Views", f"{total_views:,}")
            
            st.markdown("---")
            
            # Voice input status
            if st.session_state.voice_enabled:
                st.success("🎤 Voice Input Available")
            else:
                st.info("🎤 Voice Input Unavailable")
        
        return page
    
    def _render_data_collection_page(self):
        """
        Render the data collection page.
        """
        st.markdown('<h2 class="section-header">📥 Data Collection</h2>', unsafe_allow_html=True)
        
        if not self.youtube_api:
            st.error("YouTube API not configured. Please add YOUTUBE_API_KEY to your .env file.")
            return
        
        # Input methods
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔗 URL Input")
            url_input = st.text_input("YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
            
            if st.button("Analyze Single Video", type="primary"):
                if url_input:
                    self._analyze_single_video(url_input)
        
        with col2:
            st.subheader("🔍 Search & Batch")
            search_query = st.text_input("Search Query", placeholder="Enter search terms...")
            max_results = st.slider("Max Results", 1, 50, 10)
            
            if st.button("Search Videos", type="primary"):
                if search_query:
                    self._search_videos(search_query, max_results)
        
        # Voice input section
        if st.session_state.voice_enabled:
            st.markdown("---")
            st.subheader("🎤 Voice Input")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎤 Record Search Query"):
                    self._record_voice_input("search")
            
            with col2:
                if st.button("🎤 Record Video URL"):
                    self._record_voice_input("url")
        
        # Display collected data
        if st.session_state.videos_data:
            st.markdown("---")
            st.subheader("📊 Collected Videos")
            self._display_videos_table()
    
    def _render_data_analysis_page(self):
        """
        Render the data analysis page.
        """
        st.markdown('<h2 class="section-header">📊 Data Analysis</h2>', unsafe_allow_html=True)
        
        if not st.session_state.videos_data:
            st.info("No video data available. Please collect some data first.")
            return
        
        # Filters
        st.subheader("🔍 Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_views = st.number_input("Minimum Views", min_value=0, value=0)
        
        with col2:
            min_duration = st.number_input("Minimum Duration (seconds)", min_value=0, value=0)
        
        with col3:
            date_range = st.date_input(
                "Date Range",
                value=(datetime.now() - timedelta(days=365), datetime.now()),
                max_value=datetime.now()
            )
        
        # Apply filters
        filtered_data = self._apply_filters(st.session_state.videos_data, min_views, min_duration, date_range)
        
        # Analytics
        st.markdown("---")
        st.subheader("📈 Analytics")
        
        if filtered_data:
            self._display_analytics(filtered_data)
        else:
            st.warning("No videos match the current filters.")
    
    def _render_ai_generation_page(self):
        """
        Render the AI generation page.
        """
        st.markdown('<h2 class="section-header">🤖 AI Content Generation</h2>', unsafe_allow_html=True)
        
        if not st.session_state.videos_data:
            st.info("No video data available. Please collect some data first.")
            return
        
        # Video selection
        st.subheader("🎯 Select Video")
        video_options = [f"{video['title'][:50]}..." if len(video['title']) > 50 else video['title'] 
                        for video in st.session_state.videos_data]
        
        selected_idx = st.selectbox("Choose a video", range(len(video_options)), format_func=lambda x: video_options[x])
        selected_video = st.session_state.videos_data[selected_idx]
        
        # Generation options
        st.markdown("---")
        st.subheader("⚙️ Generation Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Text Generation**")
            generate_title = st.checkbox("Generate Title", value=True)
            generate_description = st.checkbox("Generate Description", value=True)
            generate_tags = st.checkbox("Generate Tags", value=True)
        
        with col2:
            st.markdown("**Image Generation**")
            generate_thumbnail = st.checkbox("Generate Thumbnail", value=False)
            
            if generate_thumbnail:
                thumbnail_style = st.selectbox(
                    "Thumbnail Style",
                    ["Modern", "Vintage", "Minimalist", "Bold", "Professional"]
                )
        
        # Preset selection
        if self.preset_manager:
            presets = self.preset_manager.get_all_presets()
            if presets:
                st.markdown("---")
                st.subheader("📋 Use Preset")
                preset_names = [preset['name'] for preset in presets]
                selected_preset = st.selectbox("Select Preset", ["None"] + preset_names)
        
        # Voice input for custom prompts
        if st.session_state.voice_enabled:
            st.markdown("---")
            st.subheader("🎤 Voice Prompts")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎤 Record Title Prompt"):
                    self._record_voice_input("title_prompt")
            
            with col2:
                if st.button("🎤 Record Description Prompt"):
                    self._record_voice_input("description_prompt")
        
        # Generate button
        st.markdown("---")
        if st.button("🚀 Generate Content", type="primary"):
            self._generate_ai_content(
                selected_video,
                generate_title,
                generate_description,
                generate_tags,
                generate_thumbnail,
                thumbnail_style if generate_thumbnail else None
            )
        
        # Display generated content
        if st.session_state.generated_content:
            st.markdown("---")
            st.subheader("✨ Generated Content")
            self._display_generated_content()
    
    def _render_export_page(self):
        """
        Render the export and reports page.
        """
        st.markdown('<h2 class="section-header">📤 Export & Reports</h2>', unsafe_allow_html=True)
        
        if not st.session_state.videos_data:
            st.info("No video data available. Please collect some data first.")
            return
        
        # Export options
        st.subheader("📋 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                ["CSV", "JSON", "Excel", "PDF Report"]
            )
        
        with col2:
            include_generated = st.checkbox("Include Generated Content", value=True)
        
        # Data selection
        st.subheader("🎯 Data Selection")
        
        export_all = st.checkbox("Export All Videos", value=True)
        
        if not export_all:
            selected_videos = st.multiselect(
                "Select Videos",
                range(len(st.session_state.videos_data)),
                format_func=lambda x: st.session_state.videos_data[x]['title'][:50]
            )
        else:
            selected_videos = list(range(len(st.session_state.videos_data)))
        
        # Export button
        if st.button("📤 Export Data", type="primary"):
            if selected_videos:
                self._export_data(export_format, selected_videos, include_generated)
            else:
                st.warning("Please select at least one video to export.")
        
        # Export history
        if st.session_state.export_history:
            st.markdown("---")
            st.subheader("📜 Export History")
            
            for export_record in st.session_state.export_history[-5:]:  # Show last 5
                with st.expander(f"{export_record['timestamp']} - {export_record['format']}"):
                    st.json(export_record)
    
    def _render_settings_page(self):
        """
        Render the settings page.
        """
        st.markdown('<h2 class="section-header">⚙️ Settings</h2>', unsafe_allow_html=True)
        
        # Configuration status
        st.subheader("📊 Configuration Status")
        
        if self.config_manager:
            config_summary = self.config_manager.get_config_summary()
            
            for category, status in config_summary.items():
                if status:
                    st.success(f"✅ {category.replace('_', ' ').title()}: Configured")
                else:
                    st.error(f"❌ {category.replace('_', ' ').title()}: Not Configured")
        
        # Preset management
        st.markdown("---")
        st.subheader("📋 Preset Management")
        
        if self.preset_manager:
            # Create new preset
            with st.expander("Create New Preset"):
                preset_name = st.text_input("Preset Name")
                preset_description = st.text_area("Description")
                
                # Preset configuration
                col1, col2 = st.columns(2)
                
                with col1:
                    title_template = st.text_area("Title Template", height=100)
                    description_template = st.text_area("Description Template", height=150)
                
                with col2:
                    tags_template = st.text_area("Tags Template", height=100)
                    thumbnail_style = st.selectbox("Thumbnail Style", ["Modern", "Vintage", "Minimalist", "Bold", "Professional"])
                
                if st.button("Create Preset"):
                    if preset_name and title_template:
                        self._create_preset(
                            preset_name,
                            preset_description,
                            title_template,
                            description_template,
                            tags_template,
                            thumbnail_style
                        )
            
            # Existing presets
            presets = self.preset_manager.get_all_presets()
            if presets:
                st.subheader("📋 Existing Presets")
                
                for preset in presets:
                    with st.expander(f"{preset['name']}"):
                        st.write(f"**Description:** {preset.get('description', 'No description')}")
                        st.write(f"**Created:** {preset.get('created_at', 'Unknown')}")
                        
                        if st.button(f"Delete {preset['name']}", key=f"delete_{preset['id']}"):
                            self.preset_manager.delete_preset(preset['id'])
                            st.rerun()
        
        # Database management
        st.markdown("---")
        st.subheader("🗄️ Database Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear All Data"):
                if st.session_state.get('confirm_clear', False):
                    self._clear_all_data()
                    st.session_state.confirm_clear = False
                    st.rerun()
                else:
                    st.session_state.confirm_clear = True
                    st.warning("Click again to confirm data clearing.")
        
        with col2:
            if st.button("Export Database"):
                self._export_database()
    
    def _analyze_single_video(self, url: str):
        """
        Analyze a single video from URL.
        
        Args:
            url (str): YouTube video URL
        """
        try:
            with st.spinner("Analyzing video..."):
                video_data = self.youtube_api.get_video_details(url)
                
                if video_data:
                    # Store in database
                    if self.db_manager:
                        self.db_manager.store_video_data(video_data)
                    
                    # Add to session state
                    st.session_state.videos_data.append(video_data)
                    
                    st.success(f"✅ Successfully analyzed: {video_data['title']}")
                else:
                    st.error("Failed to analyze video. Please check the URL.")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Error analyzing video: {error_msg}")
    
    def _search_videos(self, query: str, max_results: int):
        """
        Search for videos using YouTube API.
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results
        """
        try:
            with st.spinner(f"Searching for '{query}'..."):
                videos = self.youtube_api.search_videos(query, max_results)
                
                if videos:
                    # Store in database
                    if self.db_manager:
                        for video in videos:
                            self.db_manager.store_video_data(video)
                    
                    # Add to session state
                    st.session_state.videos_data.extend(videos)
                    
                    st.success(f"✅ Found {len(videos)} videos for '{query}'")
                else:
                    st.warning(f"No videos found for '{query}'")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Error searching videos: {error_msg}")
    
    def _record_voice_input(self, input_type: str):
        """
        Record voice input for various purposes.
        
        Args:
            input_type (str): Type of input (search, url, title_prompt, etc.)
        """
        try:
            with st.spinner("🎤 Recording... Speak now!"):
                text = self.voice_input.record_and_transcribe()
                
                if text:
                    st.success(f"✅ Recorded: {text}")
                    
                    # Handle different input types
                    if input_type == "search":
                        st.session_state.voice_search = text
                    elif input_type == "url":
                        st.session_state.voice_url = text
                    elif input_type == "title_prompt":
                        st.session_state.voice_title_prompt = text
                    elif input_type == "description_prompt":
                        st.session_state.voice_description_prompt = text
                else:
                    st.error("Failed to record voice input.")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Voice recording error: {error_msg}")
    
    def _display_videos_table(self):
        """
        Display videos in a table format.
        """
        df = pd.DataFrame(st.session_state.videos_data)
        
        # Select relevant columns
        display_columns = ['title', 'channel_title', 'view_count', 'like_count', 'duration', 'published_at']
        available_columns = [col for col in display_columns if col in df.columns]
        
        if available_columns:
            st.dataframe(
                df[available_columns],
                use_container_width=True,
                hide_index=True
            )
    
    def _apply_filters(self, data: List[Dict], min_views: int, min_duration: int, date_range) -> List[Dict]:
        """
        Apply filters to video data.
        
        Args:
            data (List[Dict]): Video data
            min_views (int): Minimum view count
            min_duration (int): Minimum duration
            date_range: Date range tuple
            
        Returns:
            List[Dict]: Filtered data
        """
        if not self.data_filter:
            return data
        
        filters = {
            'min_views': min_views,
            'min_duration': min_duration,
            'date_range': date_range
        }
        
        return self.data_filter.apply_filters(data, filters)
    
    def _display_analytics(self, data: List[Dict]):
        """
        Display analytics for video data.
        
        Args:
            data (List[Dict]): Video data
        """
        if not data:
            return
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_videos = len(data)
            st.metric("Total Videos", total_videos)
        
        with col2:
            total_views = sum(video.get('view_count', 0) for video in data)
            st.metric("Total Views", f"{total_views:,}")
        
        with col3:
            avg_views = total_views / total_videos if total_videos > 0 else 0
            st.metric("Avg Views", f"{avg_views:,.0f}")
        
        with col4:
            total_likes = sum(video.get('like_count', 0) for video in data)
            st.metric("Total Likes", f"{total_likes:,}")
        
        # Charts
        df = pd.DataFrame(data)
        
        if 'view_count' in df.columns:
            st.subheader("📊 View Count Distribution")
            st.bar_chart(df['view_count'])
        
        if 'published_at' in df.columns:
            st.subheader("📅 Publishing Timeline")
            # Convert to datetime and create timeline chart
            df['published_date'] = pd.to_datetime(df['published_at'])
            timeline_data = df.groupby(df['published_date'].dt.date).size()
            st.line_chart(timeline_data)
    
    def _generate_ai_content(
        self,
        video: Dict,
        generate_title: bool,
        generate_description: bool,
        generate_tags: bool,
        generate_thumbnail: bool,
        thumbnail_style: Optional[str] = None
    ):
        """
        Generate AI content for a video.
        
        Args:
            video (Dict): Video data
            generate_title (bool): Whether to generate title
            generate_description (bool): Whether to generate description
            generate_tags (bool): Whether to generate tags
            generate_thumbnail (bool): Whether to generate thumbnail
            thumbnail_style (Optional[str]): Thumbnail style
        """
        try:
            generated = {}
            
            with st.spinner("🤖 Generating AI content..."):
                # Generate text content
                if generate_title and self.llm_integration:
                    generated['title'] = self.llm_integration.generate_title(video)
                
                if generate_description and self.llm_integration:
                    generated['description'] = self.llm_integration.generate_description(video)
                
                if generate_tags and self.llm_integration:
                    generated['tags'] = self.llm_integration.generate_tags(video)
                
                # Generate thumbnail
                if generate_thumbnail and self.image_generation:
                    prompt = f"YouTube thumbnail for '{video['title']}' in {thumbnail_style} style"
                    generated['thumbnail'] = self.image_generation.generate_image(prompt)
            
            st.session_state.generated_content = generated
            st.success("✅ AI content generated successfully!")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Error generating AI content: {error_msg}")
    
    def _display_generated_content(self):
        """
        Display generated AI content.
        """
        content = st.session_state.generated_content
        
        if 'title' in content:
            st.subheader("📝 Generated Title")
            st.write(content['title'])
        
        if 'description' in content:
            st.subheader("📄 Generated Description")
            st.write(content['description'])
        
        if 'tags' in content:
            st.subheader("🏷️ Generated Tags")
            if isinstance(content['tags'], list):
                st.write(", ".join(content['tags']))
            else:
                st.write(content['tags'])
        
        if 'thumbnail' in content:
            st.subheader("🖼️ Generated Thumbnail")
            if content['thumbnail']:
                st.image(content['thumbnail'], caption="Generated Thumbnail")
    
    def _export_data(self, format_type: str, selected_videos: List[int], include_generated: bool):
        """
        Export video data in specified format.
        
        Args:
            format_type (str): Export format
            selected_videos (List[int]): Selected video indices
            include_generated (bool): Whether to include generated content
        """
        try:
            # Prepare data
            export_data = [st.session_state.videos_data[i] for i in selected_videos]
            
            if include_generated and st.session_state.generated_content:
                # Add generated content to the last video (or all if applicable)
                if export_data:
                    export_data[-1]['generated_content'] = st.session_state.generated_content
            
            # Export using export manager
            if self.export_manager:
                output = self.export_manager.export_data(export_data, format_type)
                
                if output:
                    # Create download
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"youtube_data_{timestamp}.{format_type.lower()}"
                    
                    if format_type.lower() in ['csv', 'json']:
                        st.download_button(
                            label=f"📥 Download {format_type}",
                            data=output,
                            file_name=filename,
                            mime=f"text/{format_type.lower()}"
                        )
                    
                    # Record export
                    export_record = {
                        "timestamp": datetime.now().isoformat(),
                        "format": format_type,
                        "video_count": len(selected_videos),
                        "include_generated": include_generated
                    }
                    st.session_state.export_history.append(export_record)
                    
                    st.success(f"✅ {format_type} export ready for download!")
                else:
                    st.error("Failed to generate export.")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Export error: {error_msg}")
    
    def _create_preset(
        self,
        name: str,
        description: str,
        title_template: str,
        description_template: str,
        tags_template: str,
        thumbnail_style: str
    ):
        """
        Create a new preset.
        
        Args:
            name (str): Preset name
            description (str): Preset description
            title_template (str): Title template
            description_template (str): Description template
            tags_template (str): Tags template
            thumbnail_style (str): Thumbnail style
        """
        try:
            preset_data = {
                "name": name,
                "description": description,
                "title_template": title_template,
                "description_template": description_template,
                "tags_template": tags_template,
                "thumbnail_style": thumbnail_style
            }
            
            preset_id = self.preset_manager.create_preset(preset_data)
            
            if preset_id:
                st.success(f"✅ Preset '{name}' created successfully!")
                st.rerun()
            else:
                st.error("Failed to create preset.")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Error creating preset: {error_msg}")
    
    def _clear_all_data(self):
        """
        Clear all application data.
        """
        try:
            # Clear session state
            st.session_state.videos_data = []
            st.session_state.generated_content = {}
            st.session_state.export_history = []
            
            # Clear database
            if self.db_manager:
                self.db_manager.clear_all_data()
            
            st.success("✅ All data cleared successfully!")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Error clearing data: {error_msg}")
    
    def _export_database(self):
        """
        Export the entire database.
        """
        try:
            if self.db_manager:
                backup_data = self.db_manager.export_all_data()
                
                if backup_data:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"database_backup_{timestamp}.json"
                    
                    st.download_button(
                        label="📥 Download Database Backup",
                        data=json.dumps(backup_data, indent=2),
                        file_name=filename,
                        mime="application/json"
                    )
                    
                    st.success("✅ Database backup ready for download!")
                else:
                    st.error("Failed to create database backup.")
        
        except Exception as e:
            error_msg = create_user_friendly_message(e)
            st.error(f"Database export error: {error_msg}")

def main():
    """
    Main function to run the Streamlit app.
    """
    app = StreamlitApp()
    app.run()

if __name__ == "__main__":
    main()