# 📘 Smart PDF Word Analyzer

**Smart PDF Word Analyzer** is a user-friendly app designed to help readers expand their vocabulary and improve reading comprehension by identifying and defining difficult words in any PDF book or document. Built with accessibility and offline usability in mind, the app offers a clean reading experience tailored to your English proficiency.

---

## 🚀 Key Features

### 📄 PDF Upload & Text Extraction  
Upload any text-based PDF book or document. The app automatically extracts the content and scans it for complex or uncommon words using advanced frequency data.

### 🎯 Proficiency-Based Filtering  
Choose your proficiency level to control word filtering:
- **Low**: Highlights most uncommon words.  
- **Medium**: Balanced detection.  
- **High**: Only very rare words are shown.

### 🔍 Word Lookup & Smart Learning  
Use the search bar to find word meanings. The app learns from your activity to improve future suggestions.

### 🌙 Theme Support & Minimal Distractions  
Switch between light and dark themes. Once the PDF is processed, the app works fully offline for focused reading.

### 📚 Single Active Book System  
Each upload replaces the previous one, keeping things tidy.

### 📥 Android Support with Searchable PDFs  
Download word definitions as searchable PDFs (better than .txt) for smooth use on Android devices.

### 🗑️ Data Reset & Management  
Use the trash icon to clear existing data and start fresh.

---

## ✅ Best Practices

- Use clean, text-based PDFs (no scanned images).  
- Update the app to enjoy better accuracy and UI improvements.

---

## 💡 Why Use This App?

Perfect for language learners and avid readers, Smart PDF Word Analyzer boosts vocabulary through interactive, offline reading. It's simple, smart, and distraction-free.


---

## 👨‍💻 From the Developer

The original goal was to build this as an Android app, but I ran into persistent issues with Buildozer that I couldn’t resolve. I’m sharing this project publicly in the hope that someone else might pick it up and succeed where I couldn’t.  
**Trust me — this cost me a lot of precious time and sanity, feel free to contribute or fork!**

---

## 🤝 Contributions

Contributions, bug reports, and feature requests are welcome! Please open issues or submit pull requests.

---


## 🚀 Installation

1. Clone the Repository

      ```bash
      git clone https://github.com/i0Ta07/word_search
      cd word_search

2. **Create a virtual environment** (optional but recommended):

   ```bash
   python -m venv venv
   
3. **Activate virtual environment**:
   
   ```bash
   .\venv\Scripts\Activate.ps1
   
4. **Install dependencies**

   Before running the application, install all required Python packages:

   ```bash
   pip install -r requirements.txt

5. **Run main.py**

   ```bash
    python main.py

---

## Building the Executable (Windows)

To create a standalone `.exe` file, follow the steps below. This will ensure all required assets including the `wordfreq` data and `.kv` file are bundled into the executable.

1. Install PyInstaller

   If it's not already installed, run:
 
   ```bash
   pip install pyinstaller

2. Build the Executable

   Run the following command in PowerShell from the root of your project directory:
   
      ```bash
      pyinstaller --onefile --windowed `
        --name WordSearchApp `
        --icon "assets/app_icon.ico" `
        --add-data "assets;assets" `
        --add-data "assets/wordfreq/data/large_en.msgpack.gz;wordfreq/data" `
        --add-data "wordsearchapp.kv;." `
        --hidden-import=win32timezone `
        --hidden-import=pywintypes `
        main.py


3. After the build completes, your .exe file will be located in the dist/ directory:

---

## Download

To use the application without setting up the development environment, you can download the pre-built executable:

🔗 [Download Word Search App (Windows .exe)](https://drive.google.com/drive/folders/1JwQyfh3aH2QDaz5jHnjBCVg5MwlTaRov?usp=sharing)

> After downloading, extract the `.zip` file (if zipped) and double-click the `.exe` file to launch the app.

