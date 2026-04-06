---
type: platform
status: active
category: frontend-framework
created: 2026-04-06
updated: 2026-04-06
sources:
  - "Lightning-web-runtime-docs/01-LWR-Architecture-Foundations.md"
  - "Lightning-web-runtime-docs/02-Building-Components-Pages-Layouts.md"
  - "Lightning-web-runtime-docs/03-Branding-Styling-DXP-Hooks.md"
  - "Lightning-web-runtime-docs/04-Modules-APIs-Advanced-Customizations.md"
  - "Lightning-web-runtime-docs/09-B2B-Commerce-Custom-Components-Development.md"
tags:
  - lwc
  - experience-cloud
  - frontend
  - web-components
---

# Salesforce Lightning Web Components (LWC) & Experience Cloud

## Overview

**Lightning Web Components (LWC)** is Salesforce's modern web component framework built on standard web technologies (ES6+, Shadow DOM, Web Standards). **Lightning Web Runtime (LWR)** is Salesforce's serverless runtime environment that hosts LWC-based applications in Experience Cloud storefronts, portals, and custom web experiences.

Together, LWC + LWR + Experience Cloud provide a modern, fast alternative to Aura components and legacy Visualforce, enabling developers to build responsive, accessible, and performant customer experiences.

### Key Characteristics

**Technology Stack:**
- **Language:** ES6+ JavaScript with standard APIs (no proprietary Aura framework)
- **Templates:** HTML5 with custom Salesforce directives (`if:true`, `for:each`, `key`, etc.)
- **Styling:** CSS (optional Shadow DOM encapsulation; `--dxp` custom properties for theming)
- **Component Model:** Native Web Components (encapsulation via Shadow DOM)
- **Dependencies:** Lightning Service Cloud (LWS) for secure cross-domain calls

**Core Architecture:**
- **Components** — Reusable UI units with HTML, JavaScript, and CSS
- **Properties & Attributes** — Communication via `@api` public properties and private properties
- **Events** — Custom events for parent-child communication
- **Slots** — Template composition and content projection
- **Shadow DOM** — Style and DOM encapsulation (default; can be disabled)
- **Metadata (js-meta.xml)** — Component registration, Experience Builder configuration, target assignments

**Runtime Environment:**
- Runs in modern browsers (Chrome, Safari, Firefox, Edge) with full ES6+ support
- No build step required; source code deployed directly to Salesforce
- Automatic code minification and optimization on deploy
- Lazy-loaded components for performance
- Caching and service workers handled by Salesforce infrastructure

## Component Architecture & Development

### Component Structure

```
my-component/
├── myComponent.html          # Template
├── myComponent.js            # Logic
├── myComponent.css           # Styles
└── myComponent.js-meta.xml   # Metadata/configuration
```

**HTML Template (myComponent.html):**
- Standard HTML5 with Salesforce LWC directives
- Two-way binding not supported (by design)
- Declarative event binding: `onclick="{handleClick}"`
- Conditional rendering: `if:true={isVisible}`
- Iteration: `for:each={items} key="id"`
- Template refs: `template if:true={condition}` for DOM control

**JavaScript Logic (myComponent.js):**
```javascript
import { LightningElement, api, track } from 'lwc';

export default class MyComponent extends LightningElement {
    // Public properties (from parent)
    @api productId;
    @api onAdd;

    // Private reactive properties (triggers re-render on change)
    @track cartItems = [];

    // Lifecycle hooks
    connectedCallback() { /* After component inserted */ }
    renderedCallback() { /* After render */ }
    disconnectedCallback() { /* Before removal */ }

    // Methods
    handleClick(event) {
        this.cartItems = [...this.cartItems, event.detail];
    }
}
```

**Styling (myComponent.css):**
- Scoped to component via Shadow DOM (by default)
- Can use CSS custom properties for theming: `color: var(--lwc-primary-color)`
- Host selector for component-level styling: `:host { display: block; }`
- No global styles bleed into component (and vice versa)

**Metadata (myComponent.js-meta.xml):**
```xml
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightningCommunity__Page</target>
        <target>lightningCommunity__Default</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightningCommunity__Default">
            <property name="productId" type="String" label="Product ID" />
            <property name="showPrice" type="Boolean" default="true" label="Show Price" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

### Lifecycle & Rendering

**Component Lifecycle:**
1. **connectedCallback()** — Fires after component inserted into DOM; use for initialization
2. **renderedCallback()** — Fires after render cycle completes; use for DOM manipulation
3. **disconnectedCallback()** — Fires before component removed; cleanup opportunity

**Reactivity Model:**
- Property changes trigger automatic re-render (immutable pattern recommended)
- `@track` private properties trigger re-render when modified
- Framework uses Object.observe-like mechanism (under the hood)
- No two-way binding by design (encourages unidirectional data flow)

**Performance Optimization:**
- Components lazy-load on visibility (Intersection Observer)
- Rendered templates only re-render when data changes
- Conditional rendering with `if:true` prevents DOM creation (not just CSS hiding)
- Slot-based composition avoids deep component hierarchies

## Experience Cloud Integration

### Experience Builder

**Drag-and-Drop Authoring:**
- Visual page builder (no code required for configuration)
- Components exposed in right-sidebar palette via `isExposed: true` in metadata
- Properties configured via property panel (text fields, dropdowns, toggles, etc.)
- Pages auto-published to storefronts (or require approval workflow)

**Page Structure:**
- Pages composed of regions/zones
- Regions contain components (drag-and-drop)
- Standard components provided (Text, Image, Button, Product Listing, etc.)
- Custom LWC components added to palette automatically when deployed

**Publishing & Versioning:**
- Draft mode for editing
- Publish creates live version
- Rollback to previous versions available
- A/B testing framework available (Spring '24+)

### Experience Cloud Sites

**Types:**
- **Customer Portal** — Self-service portal for registered users
- **Partner Portal** — B2B partner and reseller portal
- **Employee Portal** — Internal intranet
- **Commerce Storefront** — B2B e-commerce (using Commerce Experience Builder template)

**Authentication & Identity:**
- SAML 2.0 SSO integration (federated identity providers like Azure AD, Okta, etc.)
- OAuth 2.0 support
- Self-registration with email verification
- Passwordless authentication (biometric, magic link)
- Multi-factor authentication (MFA) optional

**Content Management:**
- Built-in Content Manager for CMS-style pages
- Reusable content snippets
- Scheduling for content publication
- Draft/publish workflow

**SEO & Performance:**
- Meta tag configuration per page
- URL slug customization (human-readable paths)
- Canonical tag support for duplicate content prevention
- Lighthouse performance metrics tracked in Experience Cloud dashboard
- Static asset caching and CDN delivery

## Theming & Styling with --dxp Hooks

### Design Tokens & Custom Properties

Experience Cloud provides **--dxp-*** custom property tokens for consistent theming across all components. These are Salesforce-managed variables that define:

**Color Tokens:**
- `--dxp-primary-color` — Primary brand color
- `--dxp-secondary-color` — Secondary brand color
- `--dxp-surface-color` — Background surfaces
- `--dxp-error-color`, `--dxp-success-color`, `--dxp-warning-color` — Status colors

**Typography Tokens:**
- `--dxp-font-family` — Primary font stack
- `--dxp-heading-font-size`, `--dxp-body-font-size` — Font sizing
- `--dxp-font-weight-bold`, `--dxp-font-weight-normal` — Font weights

**Spacing & Layout:**
- `--dxp-spacing-unit` — Base unit for spacing (e.g., 8px, then `var(--dxp-spacing-unit)` = 8px, `calc(2 * var(--dxp-spacing-unit))` = 16px)
- `--dxp-border-radius` — Corner rounding
- `--dxp-box-shadow` — Shadow effects

**Usage in Components:**
```css
/* myComponent.css */
:host {
    background-color: var(--dxp-surface-color);
    color: var(--dxp-text-color);
}

.card {
    border-radius: var(--dxp-border-radius);
    box-shadow: var(--dxp-box-shadow);
}

.button-primary {
    background-color: var(--dxp-primary-color);
    padding: calc(2 * var(--dxp-spacing-unit));
}
```

**Theming Workflow:**
1. Define color and typography scheme in Experience Cloud > Theme Settings
2. Custom properties automatically generated from design system config
3. Deploy components using `--dxp-*` tokens instead of hardcoded colors
4. Change theme centrally; all components update automatically

## Advanced Topics

### Lightning Service Cloud (LWS)

**Cross-Domain Communication:**
- LWC runs in isolated rendering context (Shadow DOM) with CSP (Content Security Policy)
- Cannot make direct HTTP requests to non-Salesforce domains (CSP blocks it)
- LWS enables secure server-side calls via `lightning/messageService` or Apex remoting

**Server-Side Calls (Apex):**
```javascript
import { LightningElement } from 'lwc';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import getProducts from '@salesforce/apex/ProductController.getProducts';

export default class ProductSearch extends LightningElement {
    handleSearch(event) {
        getProducts({ keyword: event.detail.value })
            .then(result => {
                this.products = result;
            })
            .catch(error => {
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Error', message: error.body.message, variant: 'error'
                    })
                );
            });
    }
}
```

### x-oasis-script Tag (LWR Security)

**Sandboxed Script Execution:**
- LWR scripts run in a sandboxed iframe (OASIS — Open Autonomous Security Interchange Service)
- Allows third-party scripts (analytics, payment forms, chatbots) to run without CSP violations
- Custom `<x-oasis-script>` tag wraps external scripts

**Usage:**
```html
<template>
    <x-oasis-script
        src="https://js.stripe.com/v3/"
        onload="handleStripeLoaded">
    </x-oasis-script>
</template>
```

### API & Data Access

**Salesforce APIs Available in LWC:**
- **UI API** — Query record data, field metadata, layouts
- **Connect Commerce API** — Product, cart, checkout, order queries
- **Graph API** — Custom relationships and data queries
- **Apex Remote Actions** — Server-side Apex method calls
- **Platform Events** — Real-time pub/sub messaging
- **Change Data Capture** — Change notification subscriptions

**External API Calls:**
- Cannot call external APIs directly (CSP blocks HTTP)
- Must route through Apex callouts (Apex @AuraEnabled methods)
- Apex can call HTTP endpoints, databases, webhooks, etc.

## Commerce-Specific Patterns

### Custom Commerce Components

**Standard Commerce Components Available:**
- Product Listing, Product Detail, Search, Search Facets
- Cart, Cart Items, Checkout (4-step flow), Order History
- Price Display, Inventory Availability, Shipping Methods, Tax Summary

**Customization Patterns:**
1. **Pricing Component** — Display list price, negotiated price, discount percentage
2. **Inventory Component** — Show stock levels per location, backorder messaging
3. **Search Facets** — Custom filter UI, collapsible facets, range sliders
4. **Checkout Extensions** — Custom payment forms, address validation, custom fields

**Example: Custom Pricing Display**
```javascript
import { LightningElement, api } from 'lwc';

export default class PricingDisplay extends LightningElement {
    @api listPrice;
    @api negotiatedPrice;

    get hasDiscount() {
        return this.negotiatedPrice < this.listPrice;
    }

    get discountPercentage() {
        if (!this.hasDiscount) return 0;
        return Math.round((1 - this.negotiatedPrice / this.listPrice) * 100);
    }
}
```

### Einstein Recommendations

**Personalized Product Recommendations:**
- Display "Frequently Bought Together", "Customers Also Viewed", "Personalized for You"
- Driven by Einstein AI trained on order history and behavior
- Components can be configured with recommendation type and item count

## Gotchas & Common Pitfalls

**Shadow DOM Encapsulation:**
- Styles defined in component don't apply to child components (intentional)
- Parent styles don't leak into component (intentional)
- Use CSS custom properties (`--dxp-*`) for theming if component must be themable
- To disable Shadow DOM (not recommended): `shadow: false` in js-meta.xml

**Event Binding:**
- Parent-child communication is event-driven; no two-way binding
- Custom events must be explicitly fired: `this.dispatchEvent(new CustomEvent('myevent'))`
- Avoid `@wire` for real-time queries (use `connectedCallback` with lifecycle awareness)

**Performance:**
- Avoid large loops in templates (1000+ items slow down rendering)
- Use key attribute in `for:each` to optimize list re-renders
- Lazy-load images and heavy components
- Pagination or virtual scrolling recommended for large datasets

**Browser Compatibility:**
- LWC requires modern browsers with Web Components support
- IE11 not supported (intentional design decision for modern standards)
- Evergreen browser requirement (Chrome, Safari, Firefox, Edge latest versions)

**CSP & External Scripts:**
- Direct HTTP calls from LWC fail (Content Security Policy)
- Payment forms, analytics, tracking pixels must use `<x-oasis-script>` tag
- Some third-party libraries may require wrapping in iframe

## Relationships & Cross-References

**Related Platforms:**
- [[salesforce-b2b-commerce|Salesforce B2B Commerce]] — Built entirely on LWC + LWR
- [[merchtank|MerchTank]] — Legacy system (context for migration to LWC-based Salesforce)

**Development Tools:**
- **SFDX CLI** — Source code synchronization and deployment
- **VS Code Salesforce Extension Pack** — Development environment and debugging
- **Scratch Orgs** — Temporary development instances for safe testing

## Notes

- LWC is **the future of Salesforce UI development**; Aura is in maintenance mode
- LWR provides **10x-100x performance improvement** over Aura/Visualforce for customer-facing experiences
- The `--dxp-*` theming approach is Salesforce-specific and not portable to other platforms
- Shadow DOM by default is a **feature, not a limitation** — enforces component isolation and prevents style conflicts
- Experience Builder is **not code-first** — business users can publish pages without developer involvement (though developers can build components and set up governance)
