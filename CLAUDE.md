# Design Pattern Cookbook

This is an educational design pattern cookbook that show various design pattern strategy with example code in Python, C#, TypeScript, Dart. 

- **Book format:** Quarto Book (HTML-only)

- **Content style:** The content of this cookbook provide a UML-diagram of design pattern and easy-to-understand implementation for each language in the style of Quarto's `.panel-tabset` (arrange: "Python", "C#", "TypeScript", "Dart") that the reader can click to see or compare the implementation for each language. 

- **Target Audience:** The reader already knows the basic programming for each language. So, focus on the design pattern and its application. 

- **Code example theme:** 
  - Use a simple general "classic" real-world or fictional example for code example (e.g., class name, methods, etc.). Emphasis on the design architecture over specific implementation (you can simply print stuff out for that matter).
  - Please brainstorm the example theme and ask me to choose. You can suggest.

## Table of Contents

Here are the topics/chapers of this book. Each sub-bullet corresponding to one `.qmd` file:

- **OOP:** (This serve as quick revison or OOP concept or syntax for each languages)
  - OOP Cheatsheet: Quick revision of the OOP concept and syntax for each languages

- **Overview:**
  - Overview of Design Pattern

- **Creational Design Patterns:** ✅ DONE
  - Factory Method Pattern → Logistics/Transport theme
  - Abstract Factory → Game Theme/Units (Medieval vs SciFi)
  - Builder → House Builder
  - Prototype → Shape Cloning
  - Singleton → Logger (+ DI alternative)

- **Structural Design Patterns:** ✅ DONE
  - Adapter → Media Player (MP3/WAV/OGG adapters)
  - Bridge → Remote Control + Device
  - Composite → File System (Files & Folders)
  - Decorator → Coffee Shop (Beverages + Condiments)
  - Facade → Computer Startup (CPU/Memory/HardDrive)
  - Flyweight → Text Editor (Character Styles)
  - Proxy → Document Access (Protection Proxy)

- **Behavioral Design Patterns:** ✅ DONE
  - Chain of Responsibility → HTTP Middleware Pipeline
  - Command → Text Editor (Undo/Redo)
  - Iterator → Playlist (Sequential/Reverse)
  - Mediator → Smart Home Hub
  - Memento → Game Save System
  - Observer → Weather Station
  - State → Document Workflow
  - Strategy → Payment Processing
  - Template Method → Beverage Preparation
  - Visitor → Shape Operations

## Template

- For chapter that related to design pattern, use this template: @_template/design-pattern-chapter.qmd

## After Writting Content

- After you writting a `.qmd` file in `contents/`, please update `_quarto.yml`