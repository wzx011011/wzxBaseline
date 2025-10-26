# Coding Standards for Vibe Coding

## Overview

This document outlines the coding standards for this project following Vibe Coding principles. These standards are designed to make code easily understandable by both humans and AI assistants.

## General Principles

### Intent-Driven Development
- Code should clearly express its intent
- Comments should explain "why" rather than "what"
- Functions should have clear, single responsibilities
- Variable names should be descriptive and meaningful

### AI-Friendly Code Structure
- Use consistent naming conventions
- Break complex logic into smaller, well-named functions
- Include docstrings that describe the purpose and parameters
- Structure code in a modular way to facilitate AI understanding

## Language-Specific Guidelines

### C++
- Use modern C++ features (C++17/20)
- Prefer `auto` for complex type declarations
- Use `const` correctness consistently
- Follow RAII principles
- Use smart pointers instead of raw pointers when possible

### Python
- Follow PEP 8 style guide
- Use type hints where possible
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

## Documentation Standards

### Inline Comments
- Explain the reasoning behind complex algorithms
- Highlight non-obvious implementation decisions
- Focus on "why" rather than "what"

### Function Documentation
- Describe what the function does in clear terms
- List all parameters with their purposes
- Specify return values and possible exceptions
- Include usage examples when helpful

## Code Review Guidelines

### For Human Reviewers
- Check that code expresses intent clearly
- Ensure naming is consistent and meaningful
- Verify that complexity is appropriately managed

### For AI Reviewers
- Focus on functional correctness
- Check adherence to established patterns
- Suggest improvements to code clarity
- Identify potential edge cases