# automated-documentation — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## API Documentation

### OpenAPI/Swagger Generation

```python
from dataclasses import dataclass
from typing import Any

@dataclass
class APIEndpoint:
    """Represents an API endpoint for documentation."""
    path: str
    method: str
    summary: str
    description: str
    request_body: dict | None
    responses: dict[int, dict]
    parameters: list[dict]
    security: list[str] | None


def generate_openapi_spec(
    endpoints: list[APIEndpoint],
    info: dict
) -> dict:
    """
    Generate OpenAPI specification from endpoints.

    Args:
        endpoints: List of API endpoints.
        info: API metadata (title, version, etc.).

    Returns:
        OpenAPI specification dictionary.
    """
    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": info.get("title", "API"),
            "version": info.get("version", "1.0.0"),
            "description": info.get("description", "")
        },
        "paths": {}
    }

    for endpoint in endpoints:
        path_item = spec["paths"].setdefault(endpoint.path, {})

        path_item[endpoint.method.lower()] = {
            "summary": endpoint.summary,
            "description": endpoint.description,
            "operationId": f"{endpoint.method}_{endpoint.path}".replace("/", "_"),
            "responses": {
                str(code): {
                    "description": resp.get("description", ""),
                    "content": resp.get("content", {})
                }
                for code, resp in endpoint.responses.items()
            }
        }

        if endpoint.parameters:
            path_item[endpoint.method.lower()]["parameters"] = endpoint.parameters

        if endpoint.request_body:
            path_item[endpoint.method.lower()]["requestBody"] = endpoint.request_body

    return spec
```

### GraphQL Schema Documentation

```graphql
"""
Represents a user in the system.
"""
type User {
  """Unique identifier for the user."""
  id: ID!

  """User's email address."""
  email: String!

  """User's display name."""
  name: String!

  """User's created posts."""
  posts: [Post!]!

  """Account creation timestamp."""
  createdAt: DateTime!
}

"""
Input type for creating a new user.
"""
input CreateUserInput {
  """User's email address."""
  email: String!

  """User's display name."""
  name: String!

  """Initial password."""
  password: String!
}

extend type Query {
  """
  Fetch a user by their unique identifier.

  Returns null if user is not found.
  """
  user(id: ID!): User

  """
  Fetch all users with pagination.

  Requires admin role.
  """
  users(
    """Number of items per page."""
    limit: Int = 20

    """Offset for pagination."""
    offset: Int = 0
  ): UserConnection!
}

extend type Mutation {
  """
  Create a new user account.

  Throws error if email already exists.
  """
  createUser(
    """User creation input."""
    input: CreateUserInput!
  ): User!
}
```

## Project Documentation Templates

### README Template

```markdown
# {project_name}

[![CI]({badge_url})]({workflow_url})
[![Coverage]({coverage_url})]({coverage_link})
[![License]({license_url})]({license_link})

{description}

## Features

- {feature_1}
- {feature_2}
- {feature_3}

## Installation

```bash
# Using npm
npm install {package_name}

# Using yarn
yarn add {package_name}
```

## Quick Start

```{language}
import { main_export } from '{package_name}'

// Basic usage
const result = {main_export}({example_params})
console.log(result)
```

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| {option1} | {type1} | {default1} | {description1} |
| {option2} | {type2} | {default2} | {description2} |

## API Reference

See [API.md](./docs/API.md) for detailed API documentation.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

{license} - See [LICENSE](./LICENSE) for details.
```

### CHANGELOG Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- New features to be released

### Changed
- Changes to existing features

### Fixed
- Bug fixes

## [1.0.0] - 2026-03-02

### Added
- Initial release
- Core functionality

### Security
- Security improvements
```

## Documentation Quality Checks

```python
class DocumentationQualityChecker:
    """
    Validates documentation quality.
    """

    QUALITY_CRITERIA = {
        "has_description": {
            "weight": 0.2,
            "check": lambda d: len(d.get("description", "")) > 20
        },
        "has_parameters": {
            "weight": 0.2,
            "check": lambda d: len(d.get("parameters", [])) > 0
        },
        "has_return": {
            "weight": 0.15,
            "check": lambda d: d.get("returns") is not None
        },
        "has_examples": {
            "weight": 0.2,
            "check": lambda d: len(d.get("examples", [])) > 0
        },
        "has_raises": {
            "weight": 0.1,
            "check": lambda d: len(d.get("raises", [])) > 0
        },
        "type_annotations": {
            "weight": 0.15,
            "check": lambda d: all(
                p.get("type") for p in d.get("parameters", [])
            )
        }
    }

    def calculate_quality_score(self, doc: dict) -> float:
        """
        Calculate documentation quality score (0-100).
        """
        total_score = 0

        for criterion, config in self.QUALITY_CRITERIA.items():
            if config["check"](doc):
                total_score += config["weight"] * 100

        return total_score

    def get_improvement_suggestions(self, doc: dict) -> list[str]:
        """
        Generate suggestions for improving documentation.
        """
        suggestions = []

        for criterion, config in self.QUALITY_CRITERIA.items():
            if not config["check"](doc):
                suggestions.append(
                    f"Add {criterion.replace('_', ' ')} to documentation"
                )

        return suggestions
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [JSDoc Documentation](https://jsdoc.app/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [Keep a Changelog](https://keepachangelog.com/)
