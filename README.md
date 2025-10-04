
<div align="center">
<img src="https://github.com/JStaRFilms/Blink/blob/main/assets/icon.png?raw=true" alt="Blink Logo" width="150"/>
  <h1>Blink: Your Instant AI Sidekick</h1>
  <p><strong>Select text. Hit a hotkey. Get AI magic. Instantly. Anywhere.</strong></p>
  
  <p>
    <img src="https://img.shields.io/badge/status-active-brightgreen" alt="Status">
    <img src="https://img.shields.io/badge/platform-Windows-blue" alt="Platform">
    <img src="https://img.shields.io/github/license/JStaRFilms/Blink" alt="License">
    <img src="https://img.shields.io/github/stars/JStaRFilms/Blink?style=social" alt="GitHub Stars">
  </p>
</div>

<br>

---

<div align="center">
  <p><strong>✨ Pop-up Mode: Clean, controlled, and perfect for complex tasks.</strong></p>
  <img src="https://github.com/JStaRFilms/Blink/blob/main/assets/demo%201.gif?raw=true" alt="Blink Pop-up Mode Demo">

  <br>

  <p><strong>🚀 Direct Stream Mode: Seamlessly injects AI responses right where you're working.</strong></p>
  <img src="https://github.com/JStaRFilms/Blink/blob/main/assets/demo%202.gif?raw=true" alt="Blink Direct Stream Mode Demo">
</div>

---

## ⚡ What's the Vibe?

Ever been deep in your workflow and thought, "Man, I wish I could just ask an AI to fix this, translate that, or summarize this wall of text without breaking my flow?"

**Blink is the answer.**

It's a slick, lightweight Windows utility that lives in your system tray and puts your favorite LLM just a hotkey away. No more copy-pasting into a browser tab. Just select, press, and get your response streamed right back to you.

This whole project is pure **#VibeCode**. It was built from scratch in **under 24 hours** with the help of AI, inspired by the cool concept of [jasonjmcghee/plock](https://github.com/jasonjmcghee/plock). The mission? Create a Windows-native, feature-packed AI assistant that just *works*.

## ✨ Feature Drop

Blink isn't just a simple text-passer. It's stacked with features to actually make you faster.

-   **🤖 Truly System-Wide:** Works in VS Code, Chrome, Notion, Notepad... if you can select text, Blink is there.
-   **🔥 Dual Output Modes:** Get responses in a clean **Pop-up Overlay** or let Blink **Direct Stream** the answer by typing it out for you.
-   **🧠 Conversational Memory:** Ask follow-up questions. Blink remembers the last 50 messages so you don't have to repeat yourself.
-   **📋 Clipboard Context:** The ultimate power move. Copy a file, an image, or a block of text, then select an instruction and hit `Ctrl+Alt+/`. Instant two-part commands.
-   **👁️ Adaptive Multimodal:** Smart enough to know if your model can see. It sends images directly to vision models (like GPT-4o or Llava) or automatically performs OCR for text-only models.
-   **⚙️ Total Control:** A full settings UI in the system tray lets you switch models, manage API keys, toggle memory, and craft the perfect custom system prompt.
-   **🚀 Launch & Forget:** Set it to launch on startup, and it'll always be ready when you need it.

## 🚀 Get Started (The Easy Way)

No need to be a dev. Just grab the installer and you're good to go.

1.  Head over to the **[Releases Section](https://github.com/JStaRFilms/Blink/releases)**.
2.  Download the latest `Blink-Setup.exe`.
3.  Run the installer. Blink will live in your system tray.

Done. Seriously, that's it.

## 💻 How to Use

#### The Main Move: `Ctrl + Alt + .`
1.  Select any text on your screen.
2.  Press `Ctrl + Alt + .`.
3.  Watch the magic happen in your chosen output mode.

#### The Pro Move: Clipboard Context `Ctrl + Alt + /`
1.  Copy your **content** (`Ctrl+C` on text, an image, or even multiple files in Explorer).
2.  Highlight your **instruction** (e.g., `"summarize this"`, `"what's in this image?"`).
3.  Press `Ctrl + Alt + /`.

Blink combines them and sends the request. This is your go-to for translation, summarization, and analysis.

## 🛠️ For the Devs (The VibeCode Way)

Wanna get your hands dirty or see how the AI did it?

1.  Clone the repo:
    ```bash
    git clone https://github.com/JStaRFilms/Blink.git
    cd Blink
    ```
2.  Setup your venv:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```
3.  Install the goods:
    ```bash
    pip install -r requirements.txt
    ```
4.  Make sure your local LLM (like Ollama) is running.
5.  Run it:
    ```bash
    python main.py
    ```

#### Building the `.exe` Yourself
If you want to build the single-file executable, use the `.spec` file which handles all the complex pywin32 bundling and includes the icon/assets automatically.

```bash
# ⚠️ ALWAYS build with: pyinstaller Blink.spec
# Do NOT use: pyinstaller main.py — it ignores all pywin32 bundling logic!
pyinstaller Blink.spec
```

**Why `.spec` file?** The old CLI approach (`pyinstaller --name Blink --onefile --windowed --icon="assets/icon.ico" --add-data="assets;assets" main.py`) doesn't handle the complex pywin32 dependencies properly. The `.spec` file includes automatic collection of all required DLLs and data files.

The final `Blink.exe` will be in the `dist` folder with the icon and all assets bundled correctly.

## 🤝 Let's Build Together! (Contribute)

This project was born from inspiration and built with AI, but its future is community-driven. Got a dope feature idea? Found a bug? Want to refactor something?

**All contributions are welcome!**

1.  **Fork** the repository.
2.  Create your feature branch (`git checkout -b feature/AmazingNewFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingNewFeature'`).
4.  Push to the branch (`git push origin feature/AmazingNewFeature`).
5.  Open a **Pull Request**.

Check out the [open issues](https://github.com/JStaRFilms/Blink/issues) for ideas, or just drop a suggestion. Let's make Blink the ultimate AI sidekick for Windows.

## 🙏 Credits & Inspiration

Huge shoutout to **Jason McGhee** for his project **[plock](https://github.com/jasonjmcghee/plock)**. The original Rust-based concept was the spark that ignited this entire project. While Blink is a full rewrite in Python with a different feature set, it stands on the shoulders of that initial great idea.
