# JARVIS Mobile Conversion Plan

## Overview
Convert the desktop JARVIS assistant (Windows/PyQt6) to a cross-platform mobile app for Android/iOS.

## Key Challenges
1. UI Framework: PyQt6 → Kivy/BeeWare
2. Windows-specific dependencies: Remove/replace 12+ packages
3. Desktop features: Adapt to mobile capabilities (intents, sensors, etc.)
4. Permissions: Implement mobile permission model

## Proposed Solution: Kivy-based Architecture

### Phase 1: Core AI Preservation
- Keep: main.py AI logic (Gemini connection, tool execution framework, memory)
- Replace: ui.py with Kivy interface
- Adapt: tools for mobile functionality

### Phase 2: Mobile Tool Implementation
Replace desktop tools with mobile equivalents:
- `open_app` → Mobile intents/URL schemes
- `browser_control` → WebView or browser intents
- `file_controller` → Scoped storage access (Android) / File access (iOS)
- `screen_process` → Camera/image processing (with permissions)
- `computer_settings` → Mobile settings via intents
- `send_message` → SMS/messaging apps via intents
- `reminder` → Mobile alarm/calendar APIs
- `youtube_video` → YouTube app intents or embedded player
- `weather_report` → Keep (API-based)
- `web_search` → Keep (API-based)
- `code_helper` → Limited mobile coding capabilities
- `dev_agent` → Remove or simplify (not mobile-appropriate)
- `agent_task` → Keep for multi-step tasks
- `file_processor` → Adapt for mobile file types
- `computer_control` → Limited mobile device control
- `game_updater` → Remove (desktop-specific)
- `flight_finder` → Keep (API-based)

### Phase 3: UI/UX Adaptation
- Replace desktop HUD with mobile-appropriate interface
- Implement voice wave visualization suitable for mobile
- Adapt metric display for mobile screen sizes
- Implement proper mobile navigation patterns

### Phase 4: Platform-Specific Considerations
Android:
- Use Android intents for app launching
- Request runtime permissions (CAMERA, RECORD_AUDIO, etc.)
- Use Android storage access framework

iOS:
- Use URL schemes for app communication
- Request permissions via iOS privacy controls
- Handle background execution limits

## Implementation Steps

### Step 1: Create Mobile Project Structure
```
mobile/
├── main_mobile.py          # Entry point
├── jarvis_mobile.py        # Adapted core logic
├── ui_mobile.kv            # Kivy UI definition
├── tools_mobile/           # Mobile-specific tool implementations
│   ├── __init__.py
│   ├── mobile_intents.py
│   ├── file_access.py
│   ├── camera_tools.py
│   └── messaging.py
├── requirements_mobile.txt
└── buildozer.spec          # For Android packaging
```

### Step 2: Core Logic Adaptation
Modify main.py to:
- Remove Windows-specific imports
- Abstract platform-dependent functionality
- Keep the tool execution framework intact
- Maintain Gemini API connection

### Step 3: Mobile UI Implementation
Create Kivy interface with:
- Voice input/output visualization
- Simple chat-like interface for text commands
- File upload/camera access buttons
- Settings panel for API keys and preferences
- Minimal system status display (battery, network)

### Step 4: Tool Migration
For each desktop tool, create mobile equivalent:
- Start with essential tools: web_search, weather_report, send_message
- Implement mobile-specific tools: location, sensors, notifications
- Gracefully handle unavailable features

### Step 5: Testing & Packaging
- Test on Android emulator/device
- Test on iOS simulator/device (if available)
- Package with Buildozer (Android) and Xcode (iOS)
- Handle platform-specific quirks

## Dependencies Analysis

### To Keep (Cross-platform):
- sounddevice (may need alternatives for mobile)
- google-genai
- google-generativeai
- pillow
- requests
- beautifulsoup4
- duckduckgo-search
- numpy
- psutil (limited mobile support)

### To Remove/Replace:
- pyqt6 → kivy
- pygetwindow, pyautogui, pywinauto, win10toast, comtypes → mobile intents
- opencv-python, mss → camera/image APIs
- pyperclip → clipboard APIs
- youtube-transcript-api → YouTube API or intents
- python-pptx → limited mobile document handling

### Mobile-Specific Additions:
- plyer (for platform-independent API access)
- kivy-garden.graph or similar for visualization
- android/iOS specific packages as needed

## Estimated Effort
- Core adaptation: 2-3 days
- UI implementation: 3-4 days
- Tool migration: 5-7 days (depending on features needed)
- Testing/packaging: 2-3 days
Total: ~2 weeks for MVP

## Next Steps
1. Create mobile directory structure
2. Implement basic Kivy UI
3. Port core audio/Gemini logic
4. Implement essential mobile tools
5. Iterate based on user feedback