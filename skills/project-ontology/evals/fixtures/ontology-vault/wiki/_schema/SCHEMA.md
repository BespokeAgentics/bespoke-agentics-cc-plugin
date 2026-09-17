# Wiki Schema

Pages carry YAML frontmatter with a `type`. Controlled values are listed in the page templates.

### Gap

**Definition**: A capability the target platform lacks compared with the current system.

```yaml
---
type: gap
client: northwind
severity: critical|high|medium|low
status: open|in-progress|resolved
---
```

### Feature

**Definition**: A business capability the client relies on.

```yaml
---
type: feature
client: northwind
status: proposed|active|retired
---
```

### Minimal frontmatter

```yaml
---
type: gap|feature|decision
client: {client-slug}|shared
---
```
