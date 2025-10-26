# Style Guide

## Overview

This document defines the style guidelines for code and documentation in this project. Following these guidelines helps ensure consistency and readability, making it easier for both humans and AI assistants to understand and contribute to the codebase.

## Code Style

### Naming Conventions

#### Variables and Functions
- Use descriptive names that clearly indicate purpose
- Use `snake_case` for variables and functions in Python
- Use `camelCase` for variables and functions in JavaScript
- Use `CamelCase` for class names in all languages
- Avoid abbreviations unless they are widely recognized

#### Files and Directories
- Use lowercase with hyphens for separation (e.g., `test-runner.cpp`)
- Use descriptive names that reflect content or purpose
- Group related files in appropriately named directories

### Formatting

#### Indentation
- Use 4 spaces for indentation (not tabs)
- Be consistent with indentation levels
- Align continuation lines appropriately

#### Line Length
- Maximum line length is 100 characters
- Break long lines at logical points
- Use parentheses or line continuation characters when necessary

#### Spacing
- Use spaces around operators (`a = b + c`, not `a=b+c`)
- Use spaces after commas in function parameters
- No trailing whitespace at the end of lines
- Use blank lines to separate logical sections of code

### Comments

#### General Principles
- Comments should explain "why" not "what"
- Keep comments up to date with code changes
- Remove outdated or misleading comments
- Write comments in clear, concise English

#### Comment Types
- Use inline comments sparingly and only for non-obvious code
- Use block comments for longer explanations
- Use docstrings for function and class documentation
- Mark TODOs with clear descriptions and context

### Language-Specific Guidelines

#### C++
- Follow the Google C++ Style Guide with project-specific modifications
- Use `#pragma once` for header guards
- Initialize variables at declaration when possible
- Use const-correctness consistently

#### Python
- Follow PEP 8 with project-specific modifications
- Use type hints for function parameters and return values
- Place imports at the top of the file
- Use docstrings for all public functions and classes

#### JSON
- Use 2-space indentation
- Always use double quotes for strings
- Include trailing commas for easier diffs
- Format files consistently with the project standard

## Documentation Style

### Markdown
- Use ATX-style headers (`# Header` not `Header\n=======`)
- Use descriptive link text (not "click here")
- Use code blocks with language identifiers
- Keep lines under 80 characters when possible

### Technical Writing
- Use active voice
- Address the reader directly ("you" rather than "the user")
- Define technical terms on first use
- Provide examples for complex concepts

### Diagrams
- Use ASCII art for simple diagrams
- Use Mermaid.js for more complex diagrams
- Label all diagram elements clearly
- Include alt text for accessibility

## Git Practices

### Commit Messages
- Use present tense ("Add feature" not "Added feature")
- Start with a capital letter
- Keep the first line under 50 characters
- Use the body for detailed explanations when necessary
- Reference issue numbers when applicable

### Branch Names
- Use descriptive names (`feature/user-authentication`)
- Use hyphens to separate words
- Include issue numbers when applicable (`bugfix/issue-123-login-error`)

## AI Interaction Tags

### Commit Tags
- `[AI]` - Significant AI assistance (>50% generated)
- `[AI-minor]` - Minor AI assistance (<50% generated)
- `[AI-review]` - AI used for code review only

### Code Comments
- Use `// AI-CODE:` prefix for AI-generated code sections
- Use `// AI-REVIEW:` for AI-suggested improvements
- Add context notes for AI-generated code explaining intent

## Review Guidelines

### Self-Review
- Check adherence to style guidelines
- Verify that code is readable and well-documented
- Confirm that tests are adequate
- Ensure that error handling is appropriate

### Peer Review
- Focus on correctness and maintainability
- Check for consistency with existing code
- Verify that documentation is clear
- Look for potential performance issues

### AI Review
- Focus on functional correctness
- Check adherence to style guidelines
- Suggest improvements to clarity
- Identify potential edge cases