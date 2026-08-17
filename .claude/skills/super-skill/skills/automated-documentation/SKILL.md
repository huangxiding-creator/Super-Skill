---
name: automated-documentation
description: AI-powered automated documentation generation for code, APIs, and projects. Supports multiple formats (JSDoc, Python docstrings, Markdown) with intelligent analysis and example generation.
tags: [documentation, docstrings, jsdoc, markdown, api-docs]
version: 1.0.0
source: Based on GitHub Copilot, Tabnine, Documatic patterns
integrated-with: super-skill v3.7+
---
# Automated Documentation Skill

This skill provides AI-powered automated documentation generation capabilities for code, APIs, and project documentation, supporting multiple formats and intelligent analysis.

## Documentation Types

```
┌─────────────────────────────────────────────────────────────────┐
│                  DOCUMENTATION GENERATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CODE DOCUMENTATION                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Inline comments    • Docstrings    • Type annotations │    │
│  │ • JSDoc/TSDoc       • Javadoc       • Python docstrings │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  API DOCUMENTATION                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • OpenAPI/Swagger   • GraphQL Schema  • REST endpoints  │    │
│  │ • Request/Response  • Authentication   • Error codes    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  PROJECT DOCUMENTATION                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • README.md        • CHANGELOG.md     • CONTRIBUTING.md │    │
│  │ • Architecture     • Setup guides     • API references  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Docstring Formats

### Python Docstrings

```python
# Google Style
def calculate_total(
    items: list[dict],
    tax_rate: float = 0.1
) -> float:
    """
    Calculate total price including tax.

    Args:
        items: List of item dictionaries with 'price' key.
        tax_rate: Tax rate as decimal (default 0.1 for 10%).

    Returns:
        Total price including tax.

    Raises:
        ValueError: If items list is empty or contains invalid data.

    Example:
        >>> items = [{"price": 100}, {"price": 50}]
        >>> calculate_total(items, 0.1)
        165.0
    """
    if not items:
        raise ValueError("Items list cannot be empty")

    subtotal = sum(item.get("price", 0) for item in items)
    return subtotal * (1 + tax_rate)


# NumPy Style
def process_data(
    data: np.ndarray,
    normalize: bool = True
) -> tuple[np.ndarray, dict]:
    """
    Process and optionally normalize input data.

    Parameters
    ----------
    data : np.ndarray
        Input data array of shape (n_samples, n_features).
    normalize : bool, optional
        Whether to normalize data (default is True).

    Returns
    -------
    processed : np.ndarray
        Processed data array.
    stats : dict
        Statistics used for processing.

    Examples
    --------
    >>> data = np.array([[1, 2], [3, 4]])
    >>> processed, stats = process_data(data)
    """
    pass


# Sphinx Style
def connect_database(
    host: str,
    port: int = 5432,
    database: str = "default"
) -> Connection:
    """
    Establish connection to PostgreSQL database.

    :param host: Database server hostname.
    :type host: str
    :param port: Database server port.
    :type port: int
    :param database: Database name.
    :type database: str
    :return: Database connection object.
    :rtype: Connection
    :raises ConnectionError: If connection fails.
    """
    pass
```

### JavaScript/TypeScript Documentation

```typescript
/**
 * Represents a user in the system.
 * @interface User
 */
interface User {
  /** Unique identifier for the user. */
  id: string;

  /** User's email address. */
  email: string;

  /** User's display name. */
  name: string;

  /** Account creation timestamp. */
  createdAt: Date;
}

/**
 * Service for managing user operations.
 * @class UserService
 * @example
 * ```typescript
 * const userService = new UserService(repository);
 * const user = await userService.findById('user-123');
 * ```
 */
class UserService {
  /**
   * Creates an instance of UserService.
   * @param {UserRepository} repository - The user repository.
   */
  constructor(private repository: UserRepository) {}

  /**
   * Finds a user by their unique identifier.
   * @param {string} id - The user's unique identifier.
   * @returns {Promise<User | null>} The user if found, null otherwise.
   * @throws {DatabaseError} If database operation fails.
   * @example
   * ```typescript
   * const user = await service.findById('user-123');
   * if (user) {
   *   console.log(user.name);
   * }
   * ```
   */
  async findById(id: string): Promise<User | null> {
    return this.repository.find(id);
  }
}
```

## AI Documentation Generator

```python
class AIDocGenerator:
    """
    AI-powered documentation generator.
    """

    DOCSTRING_PROMPT = """
    Generate comprehensive documentation for the following code:

    Code:
    ```
    {code}
    ```

    Generate documentation that includes:
    1. Brief description (one line)
    2. Detailed description
    3. Parameters (name, type, description, default)
    4. Return value (type, description)
    5. Exceptions (type, condition)
    6. Example usage

    Format: {format} (Google/NumPy/Sphinx/JSDoc/TSDoc)
    Language: {language}
    """

    async def generate_docstring(
        self,
        code: str,
        language: str = "python",
        format: str = "google"
    ) -> str:
        """
        Generate docstring for code.
        """
        prompt = self.DOCSTRING_PROMPT.format(
            code=code,
            format=format,
            language=language
        )

        docstring = await self.llm.generate(prompt)

        # Validate generated docstring
        if self.validate_docstring(docstring, format):
            return docstring

        # Retry with corrections
        return await self.retry_with_corrections(code, format)

    async def generate_readme(
        self,
        project_info: dict,
        files: list[str]
    ) -> str:
        """
        Generate README.md for a project.
        """
        prompt = f"""
        Generate a comprehensive README.md for:

        Project: {project_info.get('name')}
        Description: {project_info.get('description')}

        Key files:
        {chr(10).join(files[:10])}

        Include:
        1. Project title and badges
        2. Description
        3. Features
        4. Installation
        5. Quick start / Usage
        6. Configuration
        7. API Reference (if applicable)
        8. Contributing
        9. License
        """

        return await self.llm.generate(prompt)
```

## Integration with Super-Skill

### Phase Integration

```yaml
documentation_phase_mapping:
  phase_4_requirements:
    outputs:
      - README.md (initial)
      - docs/REQUIREMENTS.md

  phase_5_design:
    outputs:
      - docs/ARCHITECTURE.md
      - docs/API.md (OpenAPI spec)

  phase_8_development:
    actions:
      - auto_docstring_generation
      - inline_comment_enhancement
      - type_annotation_validation

  phase_12_summary:
    outputs:
      - docs/CHANGELOG.md
      - docs/CONTRIBUTING.md
      - README.md (updated)
```

### Automated Documentation Generation

```python
async def generate_phase_documentation(phase: int, context: dict):
    """
    Generate documentation for a phase.
    """
    doc_generator = AIDocGenerator()

    if phase == 4:
        # Requirements phase
        await doc_generator.generate_requirements_doc(context)

    elif phase == 5:
        # Design phase
        await doc_generator.generate_architecture_doc(context)
        await doc_generator.generate_api_spec(context)

    elif phase == 8:
        # Development phase
        await doc_generator.generate_code_docs(context)

    elif phase == 12:
        # Summary phase
        await doc_generator.update_readme(context)
        await doc_generator.generate_changelog(context)
```

## Best Practices

### 1. Docstring Guidelines
- Start with brief summary (one line)
- Include detailed description for complex functions
- Document all parameters with types
- Provide example usage
- List possible exceptions

### 2. README Guidelines
- Clear project description
- Installation instructions
- Quick start example
- Configuration options
- Contributing guidelines

### 3. API Documentation
- Document all endpoints
- Include request/response examples
- Document error codes
- Authentication requirements
- Rate limiting information

## Checklist

### Code Documentation
- [ ] All public functions documented
- [ ] All classes documented
- [ ] Complex logic explained
- [ ] Examples provided
- [ ] Type annotations present

### API Documentation
- [ ] All endpoints documented
- [ ] Request/response schemas
- [ ] Error responses documented
- [ ] Authentication specified
- [ ] Version information

### Project Documentation
- [ ] README.md present
- [ ] CHANGELOG.md maintained
- [ ] CONTRIBUTING.md present
- [ ] LICENSE file exists
- [ ] Architecture documented

## Deliverables

- Generated docstrings
- OpenAPI specification
- README.md
- CHANGELOG.md
- API documentation

---

## Detail Reference

Loaded on demand from [references/details.md](references/details.md): `API Documentation`, `Project Documentation Templates`, `Documentation Quality Checks`, `Version History`, `References`.
