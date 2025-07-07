# Contributing to csDNA

Thank you for your interest in contributing to the csDNA project! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment following the README instructions
4. Create a new branch for your feature or bug fix

## Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/CSDNA.git
cd CSDNA

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up Django
python manage.py migrate
python manage.py runserver
```

## Code Style

- Follow PEP 8 Python style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Write comments for complex logic

## Testing

- Write tests for new functionality
- Ensure all existing tests pass
- Test your changes manually through the web interface

## Submitting Changes

1. Create a descriptive pull request title
2. Include details about what your changes do
3. Reference any related issues
4. Ensure your code follows the project's style guidelines

## Types of Contributions

- Bug fixes
- New features for image processing
- Documentation improvements
- Performance optimizations
- UI/UX enhancements

## Questions?

Feel free to open an issue for questions or discussion about potential contributions.