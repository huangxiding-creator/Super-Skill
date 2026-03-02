---
name: code-transformation
description: AST-based code transformation, analysis, and generation. Covers TypeScript Compiler API, Babel plugins, codemods, and automated refactoring patterns.
tags: [ast, babel, typescript, codemod, transformation, refactoring]
version: 1.0.0
source: Based on TypeScript Compiler API, Babel, jscodeshift best practices
integrated-with: super-skill v3.7+
---

# Code Transformation Skill

This skill provides AST-based code transformation, analysis, and generation capabilities using TypeScript Compiler API, Babel, and codemod patterns.

## Transformation Tools

```
┌─────────────────────────────────────────────────────────────────┐
│                  CODE TRANSFORMATION STACK                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TYPESCRIPT COMPILER API                                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Type checking    • AST traversal   • Code generation  │    │
│  │ • Source maps      • Diagnostics     • Program API      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  BABEL                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Plugins          • Presets          • Transformations │    │
│  │ • JSX transform    • TypeScript       • Code mods       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  JSCODESHIFT                                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Codemods          • Bulk refactoring • Recipe runner  │    │
│  │ • React transforms  • JSX patterns      • File handling │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  REFACTORING TOOLS                                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Rename symbol    • Extract function   • Move file     │    │
│  │ • Inline variable  • Change signature   • Fix imports   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## TypeScript Compiler API

### AST Analysis

```typescript
import * as ts from 'typescript';

// Parse source file
function parseFile(sourceCode: string, fileName: string = 'temp.ts'): ts.SourceFile {
  return ts.createSourceFile(
    fileName,
    sourceCode,
    ts.ScriptTarget.Latest,
    true
  );
}

// Traverse AST
function traverseAST(node: ts.Node, callback: (node: ts.Node) => void) {
  callback(node);
  node.forEachChild((child) => traverseAST(child, callback));
}

// Find all function declarations
function findFunctions(sourceFile: ts.SourceFile): ts.FunctionDeclaration[] {
  const functions: ts.FunctionDeclaration[] = [];

  traverseAST(sourceFile, (node) => {
    if (ts.isFunctionDeclaration(node)) {
      functions.push(node);
    }
  });

  return functions;
}

// Get function signature
function getFunctionSignature(func: ts.FunctionDeclaration): string {
  const name = func.name?.getText() || 'anonymous';
  const params = func.parameters.map((p) => p.getText()).join(', ');
  const returnType = func.type ? `: ${func.type.getText()}` : '';
  return `${name}(${params})${returnType}`;
}
```

### Code Transformation

```typescript
import * as ts from 'typescript';

// Create transformer factory
function createRenameTransformer(
  oldName: string,
  newName: string
): ts.TransformerFactory<ts.SourceFile> {
  return (context) => (sourceFile) => {
    const visit = (node: ts.Node): ts.Node => {
      // Rename identifiers
      if (ts.isIdentifier(node) && node.getText() === oldName) {
        return ts.factory.createIdentifier(newName);
      }

      // Rename function declarations
      if (ts.isFunctionDeclaration(node) && node.name?.getText() === oldName) {
        return ts.factory.updateFunctionDeclaration(
          node,
          node.modifiers,
          node.asteriskToken,
          ts.factory.createIdentifier(newName),
          node.typeParameters,
          node.parameters,
          node.type,
          node.body
        );
      }

      return ts.visitEachChild(node, visit, context);
    };

    return ts.visitNode(sourceFile, visit) as ts.SourceFile;
  };
}

// Apply transformation
function transformCode(
  sourceCode: string,
  transformers: ts.TransformerFactory<ts.SourceFile>[]
): string {
  const sourceFile = parseFile(sourceCode);
  const printer = ts.createPrinter();
  const result = ts.transform(sourceFile, transformers);

  const transformedSource = result.transformed[0];
  return printer.printFile(transformedSource);
}

// Example: Rename variable
const code = `
function oldName(x: number): number {
  return x * 2;
}
console.log(oldName(5));
`;

const transformed = transformCode(code, [createRenameTransformer('oldName', 'newName')]);
console.log(transformed);
// function newName(x: number): number {
//   return x * 2;
// }
// console.log(newName(5));
```

### Type Analysis

```typescript
// Analyze types in a program
function analyzeTypes(fileNames: string[]): void {
  const program = ts.createProgram(fileNames, {
    strict: true,
    target: ts.ScriptTarget.Latest
  });

  const checker = program.getTypeChecker();

  for (const sourceFile of program.getSourceFiles()) {
    if (sourceFile.isDeclarationFile) continue;

    traverseAST(sourceFile, (node) => {
      if (ts.isVariableDeclaration(node) && node.name) {
        const symbol = checker.getSymbolAtLocation(node.name);
        if (symbol) {
          const type = checker.getTypeOfSymbolAtLocation(symbol, node);
          const typeString = checker.typeToString(type);
          console.log(`${node.name.getText()}: ${typeString}`);
        }
      }
    });
  }
}

// Find all exports
function findExports(sourceFile: ts.SourceFile): string[] {
  const exports: string[] = [];

  traverseAST(sourceFile, (node) => {
    if (ts.isExportAssignment(node)) {
      exports.push(node.expression.getText());
    }
    if (ts.isExportDeclaration(node)) {
      node.exportClause?.forEachChild((child) => {
        if (ts.isExportSpecifier(child)) {
          exports.push(child.name.getText());
        }
      });
    }
    if (ts.isFunctionDeclaration(node) && node.modifiers?.some(m => m.kind === ts.SyntaxKind.ExportKeyword)) {
      exports.push(node.name?.getText() || 'anonymous');
    }
  });

  return exports;
}
```

## Babel Plugins

### Custom Plugin

```javascript
// babel-plugin-transform-console-log.js
module.exports = function ({ types: t }) {
  return {
    name: 'transform-console-log',
    visitor: {
      CallExpression(path) {
        const { callee } = path.node;

        // Check if it's console.log
        if (
          t.isMemberExpression(callee) &&
          t.isIdentifier(callee.object, { name: 'console' }) &&
          t.isIdentifier(callee.property, { name: 'log' })
        ) {
          // Add prefix to log
          const prefix = t.stringLiteral('[LOG] ');
          path.node.arguments.unshift(prefix);
        }
      }
    }
  };
};

// babel-plugin-remove-debugger.js
module.exports = function ({ types: t }) {
  return {
    name: 'remove-debugger',
    visitor: {
      DebuggerStatement(path) {
        path.remove();
      }
    }
  };
};

// babel-plugin-transform-deprecated-api.js
module.exports = function ({ types: t }) {
  return {
    name: 'transform-deprecated-api',
    visitor: {
      CallExpression(path) {
        const { callee } = path.node;

        // Transform oldAPI.call() to newAPI()
        if (
          t.isMemberExpression(callee) &&
          t.isIdentifier(callee.object, { name: 'oldAPI' }) &&
          t.isIdentifier(callee.property, { name: 'call' })
        ) {
          path.replaceWith(
            t.callExpression(
              t.identifier('newAPI'),
              path.node.arguments
            )
          );
        }
      }
    }
  };
};
```

### Babel Configuration

```javascript
// babel.config.js
module.exports = {
  presets: [
    ['@babel/preset-env', { targets: { node: '18' } }],
    '@babel/preset-typescript',
    ['@babel/preset-react', { runtime: 'automatic' }]
  ],
  plugins: [
    './plugins/babel-plugin-transform-console-log.js',
    '@babel/plugin-proposal-decorators',
    '@babel/plugin-transform-runtime'
  ],
  env: {
    production: {
      plugins: [
        './plugins/babel-plugin-remove-debugger.js',
        'transform-remove-console'
      ]
    }
  }
};
```

## jscodeshift Codemods

### Basic Codemod

```javascript
// transform.js - jscodeshift codemod
module.exports = function (fileInfo, api, options) {
  const j = api.jscodeshift;
  const source = j(fileInfo.source);

  // Example 1: Rename variable
  source
    .find(j.Identifier, { name: 'oldVar' })
    .replaceWith(j.identifier('newVar'));

  // Example 2: Update import statements
  source
    .find(j.ImportDeclaration)
    .filter((path) => path.node.source.value === 'old-package')
    .forEach((path) => {
      path.node.source.value = 'new-package';
    });

  // Example 3: Transform function to arrow function
  source
    .find(j.FunctionDeclaration)
    .replaceWith((path) => {
      const { id, params, body } = path.node;
      return j.variableDeclaration('const', [
        j.variableDeclarator(
          id,
          j.arrowFunctionExpression(params, body)
        )
      ]);
    });

  return source.toSource();
};
```

### React Codemod

```javascript
// react-class-to-hooks.js - Transform class components to hooks
module.exports = function (fileInfo, api) {
  const j = api.jscodeshift;
  const source = j(fileInfo.source);

  // Find React class components
  source
    .find(j.ClassDeclaration, {
      superClass: {
        object: { name: 'React' },
        property: { name: 'Component' }
      }
    })
    .forEach((path) => {
      const className = path.node.id.name;

      // Extract methods
      const methods = {};
      j(path)
        .find(j.ClassMethod)
        .forEach((methodPath) => {
          const methodName = methodPath.node.key.name;
          methods[methodName] = methodPath.node;
        });

      // Create functional component with hooks
      const useStateHooks = [];
      const useEffectBlocks = [];

      // Convert state to useState
      if (methods.state) {
        // Parse state and create useState hooks
      }

      // Convert componentDidMount to useEffect
      if (methods.componentDidMount) {
        useEffectBlocks.push(
          j.useEffect(
            j.arrowFunctionExpression([], methods.componentDidMount.body),
            j.arrayExpression([])
          )
        );
      }

      // Create the new component
      const functionalComponent = j.functionDeclaration(
        j.identifier(className),
        [j.identifier('props')],
        j.blockStatement([
          ...useStateHooks,
          ...useEffectBlocks,
          methods.render?.body?.body || []
        ])
      );

      j(path).replaceWith(functionalComponent);
    });

  return source.toSource();
};
```

### Migration Codemod

```javascript
// migrate-imports.js - Migrate barrel imports to direct imports
module.exports = function (fileInfo, api) {
  const j = api.jscodeshift;
  const source = j(fileInfo.source);

  // Find imports from barrel file
  source
    .find(j.ImportDeclaration, {
      source: { value: '@/components' }
    })
    .forEach((path) => {
      const specifiers = path.node.specifiers;

      // Create individual imports
      const newImports = specifiers.map((spec) => {
        const componentName = spec.local.name;
        return j.importDeclaration(
          [j.importDefaultSpecifier(j.identifier(componentName))],
          j.literal(`@/components/${componentName}`)
        );
      });

      j(path).replaceWith(newImports);
    });

  return source.toSource();
};
```

## Automated Refactoring

### Refactoring Pipeline

```typescript
interface RefactoringRule {
  name: string;
  description: string;
  transform: (ast: ts.Node) => ts.Node;
  validate: (ast: ts.Node) => boolean;
}

class RefactoringPipeline {
  private rules: RefactoringRule[] = [];

  addRule(rule: RefactoringRule): this {
    this.rules.push(rule);
    return this;
  }

  apply(sourceCode: string): string {
    let ast = parseFile(sourceCode);

    for (const rule of this.rules) {
      if (rule.validate(ast)) {
        const result = ts.transform(ast, [
          (context) => (node) => rule.transform(node)
        ]);
        ast = result.transformed[0];
      }
    }

    return ts.createPrinter().printFile(ast);
  }
}

// Common refactoring rules
const extractConstantRule: RefactoringRule = {
  name: 'extract-constant',
  description: 'Extract magic numbers to constants',
  transform: (node) => node,
  validate: (node) => true
};

const removeUnusedImportsRule: RefactoringRule = {
  name: 'remove-unused-imports',
  description: 'Remove imports that are not used',
  transform: (node) => node,
  validate: (node) => true
};
```

## Integration with Super-Skill

### Phase Integration

```yaml
transformation_phase_mapping:
  phase_8_development:
    actions:
      - run_codemods
      - apply_refactoring_rules
      - transform_legacy_code

  phase_10_optimization:
    actions:
      - optimize_imports
      - remove_dead_code
      - transform_patterns
```

## Best Practices

### Codemod Development
- [ ] Always generate source maps
- [ ] Test on sample files first
- [ ] Create backup before running
- [ ] Use dry-run mode

### AST Operations
- [ ] Handle all edge cases
- [ ] Preserve comments
- [ ] Maintain formatting
- [ ] Generate valid code

### Refactoring
- [ ] Run tests after changes
- [ ] Review generated code
- [ ] Update documentation
- [ ] Version control friendly

## Deliverables

- Custom Babel plugins
- Codemod scripts
- Refactoring pipeline
- Transformation tests

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [TypeScript Compiler API](https://github.com/microsoft/TypeScript/wiki/Using-the-Compiler-API)
- [Babel Plugin Handbook](https://github.com/jamiebuilds/babel-handbook)
- [jscodeshift](https://github.com/facebook/jscodeshift)
- [ts-morph](https://ts-morph.com/)
