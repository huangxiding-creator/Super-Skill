# code-transformation — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

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
