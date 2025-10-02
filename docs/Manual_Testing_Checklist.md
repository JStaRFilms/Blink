# Manual Testing Checklist for Blink

This document contains the manual testing checklist that should be performed before releasing the application. These tests cover edge cases and integration issues that automated tests cannot catch.

## Hotkey & Triggering Edge Cases

- [ ] **Fullscreen Game Compatibility**: Does the hotkey work while a fullscreen game is running? (Some games capture all input)
- [ ] **Virtual Machine**: Does the hotkey work inside a Virtual Machine?
- [-] **Rapid Pressing**: What happens if you press the hotkey *really fast* twice in a row? Does it launch two instances? Does it crash? (It should ideally ignore the second press)
- [x] **Clipboard Context Hotkey**: Does the "Clipboard Context" hotkey work correctly?

## Input/Output Edge Cases

- [x] **Large Text Blocks**: Select and process a **HUGE** block of text (like the entire text of a Wikipedia article)
- [x] **Unicode Characters**: Select text containing weird Unicode characters (e.g., `你好`, `🚀`, `¯\_(ツ)_/¯`)
- [x] **Long Responses**: Ask the LLM a question that generates a very long, multi-paragraph response. Does the pop-up scroll correctly? Does the direct stream complete?
- [x] **Special Characters**: Ask the LLM to generate code with lots of special characters (`<`, `>`, `&`, `{`, `}`)
- [x] **No Text Selected**: Try to trigger it with **no text selected**. Does it fail gracefully?
- [x] **Window Switching**: Trigger it, and then immediately click into another window while it's streaming. What happens to the Direct Stream? (It should start typing in the new window, which is expected but good to confirm)

## State & Configuration Edge Cases

- [x] **Setting Changes**: Change a setting (like the output mode) and immediately try the hotkey. Does it use the new setting without a restart?
- [x] **Missing Config File**: Delete your `config.json` file completely and run the app. Does it successfully create a new, default config file?
- [x] **Invalid API Key**: Put an invalid API key in the settings. Does the error notification work as expected?
- [x] **Network Issues**: Turn off your Wi-Fi or unplug your network cable. Does the connection error notification work?
- [ ] **Startup Setting**: Check "Launch on Startup," then restart your computer. Does it launch? Then uncheck it and restart again. Does it *not* launch?

## GUI & User Experience

- [x] **Window Positioning**: Does the overlay window appear in the correct position relative to the selected text?
- [x] **Window Sizing**: Does the overlay window resize appropriately for different amounts of content?
- [x] **Text Selection**: Does the app correctly capture text from various applications (browsers, text editors, PDFs, etc.)?
- [x] **Keyboard Navigation**: Can you navigate the settings dialog using only the keyboard?
- [x] **High DPI Displays**: Does the UI look correct on high-DPI displays?

## Performance & Stability

- [ ] **Memory Usage**: Monitor memory usage during extended use. Does it grow unbounded?
- [ ] **CPU Usage**: Check CPU usage during streaming responses.
- [ ] **Long-Running Sessions**: Use the app continuously for several hours. Does it remain stable?
- [ ] **Error Recovery**: Force various error conditions and verify the app recovers gracefully.

## Cross-Platform Compatibility (if applicable)

- [ ] **Different Windows Versions**: Test on Windows 10, 11, and any other supported versions.
- [ ] **Different Screen Resolutions**: Test on various screen resolutions and aspect ratios.
- [ ] **Multiple Monitors**: Test behavior when the app spans multiple monitors.

## Integration Testing

- [x] **Ollama Integration**: Test with different Ollama models and configurations.
- [ ] **OpenAI Integration**: Test with different OpenAI models and API keys.
- [x] **Gemini Integration**: Test with Google Gemini models.
- [x] **LM Studio Integration**: Test with LM Studio local models.

## Dogfooding

- [ ] **Daily Usage**: Use the application as your primary AI assistant for a full day. Note any annoyances, unexpected behaviors, or missing features.
- [ ] **Real-World Scenarios**: Test with real tasks you actually need to accomplish, not just contrived test cases.

## Pre-Release Checklist

- [ ] All automated tests pass
- [ ] All manual test items checked
- [ ] No critical bugs remaining
- [x] Documentation updated
- [ ] Version number updated
- [ ] Release notes prepared
- [x] Backup of working code created

## How to Run Manual Tests

1. Build the application executable
2. Install it on a clean test machine if possible
3. Go through each checklist item systematically
4. Document any failures or unexpected behaviors
5. Fix issues and re-test
6. Only proceed to release when all critical items pass

## Notes

- Some tests may be environment-specific and may not apply to all setups
- Document any test failures with screenshots, error messages, and steps to reproduce
- Consider creating automated tests for issues discovered during manual testing when possible
